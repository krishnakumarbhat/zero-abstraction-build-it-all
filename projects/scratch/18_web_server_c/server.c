#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static void send_404(int cfd) {
    const char *msg = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nnot found\n";
    send(cfd, msg, strlen(msg), 0);
}

int main(int argc, char **argv) {
    int port = argc > 1 ? atoi(argv[1]) : 8080;
    int sfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sfd < 0) { perror("socket"); return 1; }

    int yes = 1;
    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((uint16_t)port);

    if (bind(sfd, (struct sockaddr *)&addr, sizeof(addr)) < 0) { perror("bind"); return 2; }
    if (listen(sfd, 16) < 0) { perror("listen"); return 3; }
    printf("listening on :%d\n", port);

    while (1) {
        int cfd = accept(sfd, NULL, NULL);
        if (cfd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            continue;
        }

        char req[4096] = {0};
        ssize_t n = recv(cfd, req, sizeof(req) - 1, 0);
        if (n <= 0) { close(cfd); continue; }

        char method[16], path[1024];
        if (sscanf(req, "%15s %1023s", method, path) != 2) {
            close(cfd);
            continue;
        }
        if (strcmp(method, "GET") != 0) {
            const char *msg = "HTTP/1.1 405 Method Not Allowed\r\n\r\n";
            send(cfd, msg, strlen(msg), 0);
            close(cfd);
            continue;
        }

        char fs_path[1200] = ".";
        strncat(fs_path, path, sizeof(fs_path) - strlen(fs_path) - 1);
        if (strcmp(path, "/") == 0) strcpy(fs_path, "./index.html");

        int fd = open(fs_path, O_RDONLY);
        if (fd < 0) {
            send_404(cfd);
            close(cfd);
            continue;
        }

        const char *head = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n";
        send(cfd, head, strlen(head), 0);
        char buf[4096];
        while ((n = read(fd, buf, sizeof(buf))) > 0) {
            send(cfd, buf, (size_t)n, 0);
        }
        close(fd);
        close(cfd);
    }
}
