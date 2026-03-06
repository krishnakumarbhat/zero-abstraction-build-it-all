#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

static struct termios orig;

typedef struct {
    char *buf;
    size_t gap_start, gap_end, cap;
} GapBuffer;

static void die(const char *m) {
    perror(m);
    exit(1);
}

static void raw_off(void) { tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig); }

static void raw_on(void) {
    if (tcgetattr(STDIN_FILENO, &orig) == -1) die("tcgetattr");
    atexit(raw_off);
    struct termios raw = orig;
    raw.c_iflag &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
    raw.c_oflag &= ~(OPOST);
    raw.c_cflag |= (CS8);
    raw.c_lflag &= ~(ECHO | ICANON | IEXTEN | ISIG);
    raw.c_cc[VMIN] = 0;
    raw.c_cc[VTIME] = 1;
    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) die("tcsetattr");
}

static void gb_init(GapBuffer *g, size_t cap) {
    g->buf = (char *)calloc(cap, 1);
    g->cap = cap;
    g->gap_start = 0;
    g->gap_end = cap;
}

static size_t gb_len(GapBuffer *g) { return g->cap - (g->gap_end - g->gap_start); }

static void gb_insert(GapBuffer *g, char c) {
    if (g->gap_start >= g->gap_end) return;
    g->buf[g->gap_start++] = c;
}

static void gb_backspace(GapBuffer *g) {
    if (g->gap_start > 0) g->gap_start--;
}

static void gb_render(GapBuffer *g, int fd) {
    write(fd, "\x1b[2J\x1b[H", 7);
    write(fd, g->buf, g->gap_start);
    write(fd, g->buf + g->gap_end, g->cap - g->gap_end);
    write(fd, "\r\n-- CTRL-S save | CTRL-Q quit --", 33);
}

static int gb_save(GapBuffer *g, const char *path) {
    int fd = open(path, O_CREAT | O_TRUNC | O_WRONLY, 0644);
    if (fd < 0) return -1;
    if (write(fd, g->buf, g->gap_start) < 0) { close(fd); return -1; }
    if (write(fd, g->buf + g->gap_end, g->cap - g->gap_end) < 0) { close(fd); return -1; }
    close(fd);
    return 0;
}

int main(int argc, char **argv) {
    const char *file = argc > 1 ? argv[1] : "editor.txt";
    GapBuffer g;
    gb_init(&g, 1 << 16);
    raw_on();

    while (1) {
        gb_render(&g, STDOUT_FILENO);
        char c;
        int n = read(STDIN_FILENO, &c, 1);
        if (n != 1) continue;
        if (c == 17) break;
        if (c == 19) {
            if (gb_save(&g, file) == -1) {
                const char *m = "\r\nsave failed\r\n";
                write(STDOUT_FILENO, m, strlen(m));
            }
            continue;
        }
        if (c == 127) gb_backspace(&g);
        else gb_insert(&g, c);
    }

    raw_off();
    free(g.buf);
    return 0;
}
