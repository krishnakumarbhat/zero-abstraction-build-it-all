#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_LINE 1024
#define MAX_ARGS 128

static void trim_newline(char *s) {
    size_t len = strlen(s);
    if (len > 0 && s[len - 1] == '\n') {
        s[len - 1] = '\0';
    }
}

static int parse_args(char *segment, char **args, char **infile, char **outfile) {
    int argc = 0;
    *infile = NULL;
    *outfile = NULL;

    char *token = strtok(segment, " \t");
    while (token != NULL && argc < MAX_ARGS - 1) {
        if (strcmp(token, "<") == 0) {
            token = strtok(NULL, " \t");
            if (token) *infile = token;
        } else if (strcmp(token, ">") == 0) {
            token = strtok(NULL, " \t");
            if (token) *outfile = token;
        } else {
            args[argc++] = token;
        }
        token = strtok(NULL, " \t");
    }
    args[argc] = NULL;
    return argc;
}

static int run_builtin(char **args) {
    if (args[0] == NULL) return 1;

    if (strcmp(args[0], "exit") == 0) {
        exit(0);
    }

    if (strcmp(args[0], "cd") == 0) {
        const char *target = args[1] ? args[1] : getenv("HOME");
        if (chdir(target) != 0) {
            perror("cd");
        }
        return 1;
    }

    if (strcmp(args[0], "echo") == 0) {
        for (int i = 1; args[i] != NULL; i++) {
            printf("%s", args[i]);
            if (args[i + 1] != NULL) printf(" ");
        }
        printf("\n");
        return 1;
    }

    return 0;
}

static void exec_single(char **args, char *infile, char *outfile) {
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return;
    }

    if (pid == 0) {
        if (infile) {
            int fd = open(infile, O_RDONLY);
            if (fd < 0) {
                perror("open input");
                _exit(1);
            }
            dup2(fd, STDIN_FILENO);
            close(fd);
        }
        if (outfile) {
            int fd = open(outfile, O_WRONLY | O_CREAT | O_TRUNC, 0644);
            if (fd < 0) {
                perror("open output");
                _exit(1);
            }
            dup2(fd, STDOUT_FILENO);
            close(fd);
        }
        execvp(args[0], args);
        perror("execvp");
        _exit(1);
    }

    waitpid(pid, NULL, 0);
}

static void exec_pipe(char **left_args, char **right_args) {
    int fd[2];
    if (pipe(fd) < 0) {
        perror("pipe");
        return;
    }

    pid_t p1 = fork();
    if (p1 < 0) {
        perror("fork");
        close(fd[0]);
        close(fd[1]);
        return;
    }

    if (p1 == 0) {
        dup2(fd[1], STDOUT_FILENO);
        close(fd[0]);
        close(fd[1]);
        execvp(left_args[0], left_args);
        perror("execvp left");
        _exit(1);
    }

    pid_t p2 = fork();
    if (p2 < 0) {
        perror("fork");
        close(fd[0]);
        close(fd[1]);
        return;
    }

    if (p2 == 0) {
        dup2(fd[0], STDIN_FILENO);
        close(fd[1]);
        close(fd[0]);
        execvp(right_args[0], right_args);
        perror("execvp right");
        _exit(1);
    }

    close(fd[0]);
    close(fd[1]);
    waitpid(p1, NULL, 0);
    waitpid(p2, NULL, 0);
}

int main(void) {
    char line[MAX_LINE];

    signal(SIGINT, SIG_IGN);

    while (1) {
        printf("$ ");
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) {
            printf("\n");
            break;
        }
        trim_newline(line);

        if (strlen(line) == 0) continue;

        char *pipe_pos = strchr(line, '|');
        if (pipe_pos) {
            *pipe_pos = '\0';
            char *left = line;
            char *right = pipe_pos + 1;

            char *left_args[MAX_ARGS];
            char *right_args[MAX_ARGS];
            char *left_in = NULL;
            char *left_out = NULL;
            char *right_in = NULL;
            char *right_out = NULL;

            int leftc = parse_args(left, left_args, &left_in, &left_out);
            int rightc = parse_args(right, right_args, &right_in, &right_out);
            if (leftc == 0 || rightc == 0) continue;

            exec_pipe(left_args, right_args);
            continue;
        }

        char *args[MAX_ARGS];
        char *infile = NULL;
        char *outfile = NULL;
        int argc = parse_args(line, args, &infile, &outfile);
        if (argc == 0) continue;

        if (run_builtin(args)) continue;
        exec_single(args, infile, outfile);
    }

    return 0;
}
