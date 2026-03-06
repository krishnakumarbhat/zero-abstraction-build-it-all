#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int ignore_case;
    int show_line_num;
    int show_version;
    const char *pattern;
    const char *file;
} Options;

static void usage(const char *prog) {
    fprintf(stdout, "Usage: %s [-i] [-n] <pattern> [file]\n", prog);
    fprintf(stdout, "Options:\n  -i ignore case\n  -n show line numbers\n  -v show version\n  --help show this\n");
}

static int lower(int c) { return (c >= 'A' && c <= 'Z') ? c + 32 : c; }

static int contains(const char *line, const char *pat, int ignore_case) {
    size_t n = strlen(line), m = strlen(pat);
    if (m == 0) return 1;
    for (size_t i = 0; i + m <= n; i++) {
        size_t j = 0;
        while (j < m) {
            char a = line[i + j], b = pat[j];
            if (ignore_case) {
                a = (char)lower(a);
                b = (char)lower(b);
            }
            if (a != b) break;
            j++;
        }
        if (j == m) return 1;
    }
    return 0;
}

static int parse_args(int argc, char **argv, Options *opt) {
    memset(opt, 0, sizeof(*opt));
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        if (a[0] == '-') {
            if (strcmp(a, "-i") == 0) opt->ignore_case = 1;
            else if (strcmp(a, "-n") == 0) opt->show_line_num = 1;
            else if (strcmp(a, "-v") == 0 || strcmp(a, "--version") == 0) opt->show_version = 1;
            else if (strcmp(a, "--help") == 0) return 2;
            else {
                fprintf(stderr, "Unknown flag: %s\n", a);
                return 0;
            }
        } else if (!opt->pattern) {
            opt->pattern = a;
        } else if (!opt->file) {
            opt->file = a;
        } else {
            fprintf(stderr, "Unexpected arg: %s\n", a);
            return 0;
        }
    }
    if (opt->show_version) return 3;
    if (!opt->pattern) return 0;
    return 1;
}

int main(int argc, char **argv) {
    Options opt;
    int p = parse_args(argc, argv, &opt);
    if (p == 2) {
        usage(argv[0]);
        return 0;
    }
    if (p == 3) {
        puts("cli_tool 0.1.0");
        return 0;
    }
    if (p == 0) {
        usage(argv[0]);
        return 1;
    }

    FILE *in = stdin;
    if (opt.file) {
        in = fopen(opt.file, "rb");
        if (!in) {
            fprintf(stderr, "open failed: %s (%s)\n", opt.file, strerror(errno));
            return 2;
        }
    }

    char buf[4096];
    size_t line_no = 0;
    while (fgets(buf, sizeof(buf), in)) {
        line_no++;
        if (contains(buf, opt.pattern, opt.ignore_case)) {
            if (opt.show_line_num) fprintf(stdout, "%zu:", line_no);
            fputs(buf, stdout);
        }
    }

    if (in != stdin) fclose(in);
    if (ferror(in)) {
        fprintf(stderr, "read error\n");
        return 3;
    }
    return 0;
}
