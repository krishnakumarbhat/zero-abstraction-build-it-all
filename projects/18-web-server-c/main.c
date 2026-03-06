#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <limits.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define BUF_SIZE 8192

static volatile sig_atomic_t keep_running = 1;
static char g_docroot[PATH_MAX] = {0};

static void on_sigint(int sig) {
  (void)sig;
  keep_running = 0;
}

static const char *content_type_for(const char *path) {
  const char *dot = strrchr(path, '.');
  if (!dot) return "text/plain; charset=utf-8";
  if (strcmp(dot, ".html") == 0 || strcmp(dot, ".htm") == 0) return "text/html; charset=utf-8";
  if (strcmp(dot, ".css") == 0) return "text/css; charset=utf-8";
  if (strcmp(dot, ".js") == 0) return "application/javascript; charset=utf-8";
  if (strcmp(dot, ".json") == 0) return "application/json; charset=utf-8";
  if (strcmp(dot, ".txt") == 0) return "text/plain; charset=utf-8";
  if (strcmp(dot, ".png") == 0) return "image/png";
  if (strcmp(dot, ".jpg") == 0 || strcmp(dot, ".jpeg") == 0) return "image/jpeg";
  return "application/octet-stream";
}

static void send_simple_response(int client_fd, int code, const char *reason, const char *body) {
  char hdr[512];
  int body_len = (int)strlen(body);
  int n = snprintf(hdr, sizeof(hdr),
                   "HTTP/1.1 %d %s\r\n"
                   "Content-Type: text/plain; charset=utf-8\r\n"
                   "Content-Length: %d\r\n"
                   "Connection: close\r\n\r\n",
                   code, reason, body_len);
  send(client_fd, hdr, (size_t)n, 0);
  send(client_fd, body, (size_t)body_len, 0);
}

static bool parse_request_line(const char *req, char *method, size_t method_sz, char *path, size_t path_sz) {
  const char *line_end = strstr(req, "\r\n");
  if (!line_end) return false;

  char line[1024];
  size_t len = (size_t)(line_end - req);
  if (len >= sizeof(line)) return false;
  memcpy(line, req, len);
  line[len] = '\0';

  char version[32];
  if (sscanf(line, "%15s %1023s %31s", method, path, version) != 3) return false;
  (void)method_sz;
  (void)path_sz;
  return true;
}

static void init_docroot(const char *argv0) {
  (void)argv0;
  char exe_path[PATH_MAX];
  ssize_t n = readlink("/proc/self/exe", exe_path, sizeof(exe_path) - 1);
  if (n > 0) {
    exe_path[n] = '\0';
    char *slash = strrchr(exe_path, '/');
    if (slash) {
      *slash = '\0';
      snprintf(g_docroot, sizeof(g_docroot), "%s", exe_path);
      return;
    }
  }

  if (!getcwd(g_docroot, sizeof(g_docroot))) {
    snprintf(g_docroot, sizeof(g_docroot), ".");
  }
}

static void build_fs_path(const char *url_path, char *out, size_t out_sz) {
  const char *p = url_path;
  if (*p == '\0' || strcmp(p, "/") == 0) {
    snprintf(out, out_sz, "%s/index.html", g_docroot);
    return;
  }

  while (*p == '/') p++;
  size_t root_len = strlen(g_docroot);
  if (root_len + 2 >= out_sz) {
    snprintf(out, out_sz, "%s", g_docroot);
    return;
  }

  memcpy(out, g_docroot, root_len);
  size_t i = root_len;
  out[i++] = '/';

  for (; *p && i + 1 < out_sz; p++) {
    if (*p == '?') break;
    out[i++] = *p;
  }
  out[i] = '\0';
}

static void handle_client(int client_fd) {
  char req[BUF_SIZE + 1];
  ssize_t n = recv(client_fd, req, BUF_SIZE, 0);
  if (n <= 0) return;
  req[n] = '\0';

  char method[16] = {0};
  char path[1024] = {0};
  if (!parse_request_line(req, method, sizeof(method), path, sizeof(path))) {
    send_simple_response(client_fd, 400, "Bad Request", "bad request\n");
    return;
  }

  if (strcmp(method, "GET") != 0) {
    send_simple_response(client_fd, 405, "Method Not Allowed", "only GET is supported\n");
    return;
  }

  if (strstr(path, "..") != NULL) {
    send_simple_response(client_fd, 403, "Forbidden", "forbidden path\n");
    return;
  }

  char fs_path[1200];
  build_fs_path(path, fs_path, sizeof(fs_path));

  int fd = open(fs_path, O_RDONLY);
  if (fd < 0) {
    send_simple_response(client_fd, 404, "Not Found", "not found\n");
    return;
  }

  struct stat st;
  if (fstat(fd, &st) < 0 || !S_ISREG(st.st_mode)) {
    close(fd);
    send_simple_response(client_fd, 404, "Not Found", "not found\n");
    return;
  }

  const char *ctype = content_type_for(fs_path);
  char hdr[512];
  int hlen = snprintf(hdr, sizeof(hdr),
                      "HTTP/1.1 200 OK\r\n"
                      "Content-Type: %s\r\n"
                      "Content-Length: %lld\r\n"
                      "Connection: close\r\n\r\n",
                      ctype, (long long)st.st_size);
  send(client_fd, hdr, (size_t)hlen, 0);

  char buf[BUF_SIZE];
  while (1) {
    ssize_t r = read(fd, buf, sizeof(buf));
    if (r == 0) break;
    if (r < 0) {
      if (errno == EINTR) continue;
      break;
    }

    ssize_t off = 0;
    while (off < r) {
      ssize_t w = send(client_fd, buf + off, (size_t)(r - off), 0);
      if (w < 0) {
        if (errno == EINTR) continue;
        close(fd);
        return;
      }
      off += w;
    }
  }

  close(fd);
}

int main(int argc, char **argv) {
  int port = 8080;
  if (argc >= 2) {
    port = atoi(argv[1]);
    if (port <= 0 || port > 65535) {
      fprintf(stderr, "invalid port: %s\n", argv[1]);
      return 1;
    }
  }

  signal(SIGINT, on_sigint);
  init_docroot(argv[0]);

  int server_fd = socket(AF_INET, SOCK_STREAM, 0);
  if (server_fd < 0) {
    perror("socket");
    return 1;
  }

  int opt = 1;
  setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

  struct sockaddr_in addr;
  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = htonl(INADDR_ANY);
  addr.sin_port = htons((uint16_t)port);

  if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
    perror("bind");
    close(server_fd);
    return 1;
  }

  if (listen(server_fd, 16) < 0) {
    perror("listen");
    close(server_fd);
    return 1;
  }

  printf("mini-web-server listening on 0.0.0.0:%d (docroot: %s)\n", port, g_docroot);

  while (keep_running) {
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
    if (client_fd < 0) {
      if (errno == EINTR) continue;
      perror("accept");
      break;
    }

    handle_client(client_fd);
    close(client_fd);
  }

  close(server_fd);
  return 0;
}
