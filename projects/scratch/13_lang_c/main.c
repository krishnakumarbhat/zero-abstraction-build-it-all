#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum { TOK_INT, TOK_ID, TOK_NUM, TOK_EQ, TOK_PLUS, TOK_SEMI, TOK_EOF } Tok;
typedef struct { Tok t; char lex[64]; } Token;

static const char *src;
static size_t pos;

static Token next_tok(void) {
    while (isspace((unsigned char)src[pos])) pos++;
    if (!src[pos]) return (Token){TOK_EOF, ""};
    if (isalpha((unsigned char)src[pos])) {
        size_t s = pos;
        while (isalnum((unsigned char)src[pos])) pos++;
        Token tk = {TOK_ID, ""};
        strncpy(tk.lex, src + s, pos - s);
        tk.lex[pos - s] = 0;
        if (strcmp(tk.lex, "int") == 0) tk.t = TOK_INT;
        return tk;
    }
    if (isdigit((unsigned char)src[pos])) {
        size_t s = pos;
        while (isdigit((unsigned char)src[pos])) pos++;
        Token tk = {TOK_NUM, ""};
        strncpy(tk.lex, src + s, pos - s);
        tk.lex[pos - s] = 0;
        return tk;
    }
    char c = src[pos++];
    if (c == '=') return (Token){TOK_EQ, "="};
    if (c == '+') return (Token){TOK_PLUS, "+"};
    if (c == ';') return (Token){TOK_SEMI, ";"};
    return (Token){TOK_EOF, ""};
}

typedef struct { char name[64]; int declared; } Sym;
static Sym syms[128];
static int symn = 0;

static int find_sym(const char *name) {
    for (int i = 0; i < symn; i++) if (strcmp(syms[i].name, name) == 0) return i;
    return -1;
}

static void declare(const char *name) {
    if (find_sym(name) >= 0) return;
    strcpy(syms[symn].name, name);
    syms[symn].declared = 1;
    symn++;
}

int main(void) {
    src = "int a; int b; a = 2 + 3; b = a + 4;";
    pos = 0;
    Token tk;
    FILE *out = fopen("out.s", "w");
    if (!out) return 1;

    fprintf(out, ".intel_syntax noprefix\n.global _start\n_start:\n");
    while ((tk = next_tok()).t != TOK_EOF) {
        if (tk.t == TOK_INT) {
            Token id = next_tok();
            Token semi = next_tok();
            if (id.t != TOK_ID || semi.t != TOK_SEMI) return 2;
            declare(id.lex);
        } else if (tk.t == TOK_ID) {
            if (find_sym(tk.lex) < 0) return 3;
            Token eq = next_tok();
            Token a = next_tok();
            Token plus = next_tok();
            Token b = next_tok();
            Token semi = next_tok();
            if (eq.t != TOK_EQ || plus.t != TOK_PLUS || semi.t != TOK_SEMI) return 4;
            fprintf(out, "  mov eax, %s\n", a.lex);
            fprintf(out, "  add eax, %s\n", b.lex);
            fprintf(out, "  ; %s = eax\n", tk.lex);
        } else {
            return 5;
        }
    }
    fprintf(out, "  mov eax, 60\n  xor edi, edi\n  syscall\n");
    fclose(out);
    puts("ok");
    return 0;
}
