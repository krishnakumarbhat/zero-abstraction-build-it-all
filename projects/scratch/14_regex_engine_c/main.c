#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct State State;
struct State {
    int c;
    State *out1;
    State *out2;
    int is_accept;
};

typedef struct PtrList PtrList;
struct PtrList {
    State **outp;
    PtrList *next;
};

typedef struct {
    State *start;
    PtrList *outs;
} Frag;

static State states[1024];
static int ns;

static State *new_state(int c, State *o1, State *o2) {
    State *s = &states[ns++];
    s->c = c; s->out1 = o1; s->out2 = o2; s->is_accept = 0;
    return s;
}

static PtrList *list1(State **outp) {
    PtrList *l = (PtrList *)malloc(sizeof(PtrList));
    l->outp = outp; l->next = NULL; return l;
}

static PtrList *append(PtrList *a, PtrList *b) {
    if (!a) return b;
    PtrList *t = a;
    while (t->next) t = t->next;
    t->next = b;
    return a;
}

static void patch(PtrList *l, State *s) {
    while (l) { *(l->outp) = s; l = l->next; }
}

static int is_meta(char c) { return c == '|' || c == '*' || c == '(' || c == ')'; }

static int re2post(const char *re, char *post) {
    char stack[128]; int sp = 0;
    int nalt = 0, natom = 0, p = 0;
    for (int i = 0; re[i]; i++) {
        char c = re[i];
        switch (c) {
            case '(':
                if (natom > 1) { --natom; post[p++] = '.'; }
                stack[sp++] = (char)nalt;
                stack[sp++] = (char)natom;
                nalt = 0; natom = 0;
                break;
            case '|':
                while (--natom > 0) post[p++] = '.';
                nalt++;
                break;
            case ')':
                while (--natom > 0) post[p++] = '.';
                while (nalt-- > 0) post[p++] = '|';
                natom = (unsigned char)stack[--sp];
                nalt = (unsigned char)stack[--sp];
                natom++;
                break;
            case '*':
                post[p++] = '*';
                break;
            default:
                if (natom > 1) { --natom; post[p++] = '.'; }
                post[p++] = c;
                natom++;
        }
    }
    while (--natom > 0) post[p++] = '.';
    while (nalt-- > 0) post[p++] = '|';
    post[p] = 0;
    return p;
}

static State *compile(const char *re) {
    char post[512];
    re2post(re, post);
    Frag st[512]; int sp = 0;
    ns = 0;
    for (int i = 0; post[i]; i++) {
        char c = post[i];
        if (!is_meta(c) && c != '.') {
            State *s = new_state((unsigned char)c, NULL, NULL);
            st[sp++] = (Frag){s, list1(&s->out1)};
        } else if (c == '.') {
            Frag e2 = st[--sp], e1 = st[--sp];
            patch(e1.outs, e2.start);
            st[sp++] = (Frag){e1.start, e2.outs};
        } else if (c == '|') {
            Frag e2 = st[--sp], e1 = st[--sp];
            State *s = new_state(-1, e1.start, e2.start);
            st[sp++] = (Frag){s, append(e1.outs, e2.outs)};
        } else if (c == '*') {
            Frag e = st[--sp];
            State *s = new_state(-1, e.start, NULL);
            patch(e.outs, s);
            st[sp++] = (Frag){s, list1(&s->out2)};
        }
    }
    Frag e = st[--sp];
    State *acc = new_state(-2, NULL, NULL);
    acc->is_accept = 1;
    patch(e.outs, acc);
    return e.start;
}

static void add_state(State **set, int *n, State *s, int *seen) {
    if (!s) return;
    if (seen[s - states]) return;
    seen[s - states] = 1;
    if (s->c == -1) {
        add_state(set, n, s->out1, seen);
        add_state(set, n, s->out2, seen);
        return;
    }
    set[(*n)++] = s;
}

static int match(State *start, const char *text) {
    State *curr[1024], *next[1024];
    int cn = 0, nn = 0;
    int seen[1024] = {0};
    add_state(curr, &cn, start, seen);
    for (int i = 0; text[i]; i++) {
        nn = 0;
        memset(seen, 0, sizeof(seen));
        for (int j = 0; j < cn; j++) {
            State *s = curr[j];
            if (s->c >= 0 && s->c == (unsigned char)text[i]) {
                add_state(next, &nn, s->out1, seen);
            }
        }
        memcpy(curr, next, sizeof(State *) * nn);
        cn = nn;
        if (cn == 0) return 0;
    }
    for (int i = 0; i < cn; i++) if (curr[i]->is_accept) return 1;
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <regex> <text>\n", argv[0]);
        return 1;
    }
    State *nfa = compile(argv[1]);
    puts(match(nfa, argv[2]) ? "MATCH" : "NO MATCH");
    return 0;
}
