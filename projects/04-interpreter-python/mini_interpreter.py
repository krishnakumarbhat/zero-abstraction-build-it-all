from dataclasses import dataclass
import sys


@dataclass
class Token:
    kind: str
    value: str


KEYWORDS = {"fn", "print"}


def lex(src: str):
    tokens = []
    i = 0
    while i < len(src):
        c = src[i]
        if c in " \t\r":
            i += 1
            continue
        if c == "\n":
            tokens.append(Token("NEWLINE", "\\n"))
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            tokens.append(Token("NUMBER", src[i:j]))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            ident = src[i:j]
            tokens.append(Token(ident.upper() if ident in KEYWORDS else "IDENT", ident))
            i = j
            continue
        if c in "+-*/=(),{}":
            tokens.append(Token(c, c))
            i += 1
            continue
        raise SyntaxError(f"unexpected char: {c}")
    tokens.append(Token("EOF", ""))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def cur(self):
        return self.toks[self.i]

    def eat(self, kind=None):
        t = self.cur()
        if kind and t.kind != kind:
            raise SyntaxError(f"expected {kind}, got {t.kind}")
        self.i += 1
        return t

    def skip_newlines(self):
        while self.cur().kind == "NEWLINE":
            self.eat("NEWLINE")

    def parse(self):
        stmts = []
        self.skip_newlines()
        while self.cur().kind != "EOF":
            stmts.append(self.statement())
            self.skip_newlines()
        return ("PROGRAM", stmts)

    def statement(self):
        t = self.cur()
        if t.kind == "FN":
            return self.fn_def()
        if t.kind == "PRINT":
            self.eat("PRINT")
            return ("PRINT", self.expr())
        if t.kind == "IDENT" and self.toks[self.i + 1].kind == "=":
            name = self.eat("IDENT").value
            self.eat("=")
            return ("ASSIGN", name, self.expr())
        return ("EXPR", self.expr())

    def fn_def(self):
        self.eat("FN")
        name = self.eat("IDENT").value
        self.eat("(")
        params = []
        if self.cur().kind != ")":
            params.append(self.eat("IDENT").value)
            while self.cur().kind == ",":
                self.eat(",")
                params.append(self.eat("IDENT").value)
        self.eat(")")
        self.eat("{")
        self.skip_newlines()
        body = []
        while self.cur().kind != "}":
            body.append(self.statement())
            self.skip_newlines()
        self.eat("}")
        return ("FN", name, params, body)

    def expr(self):
        node = self.term()
        while self.cur().kind in ("+", "-"):
            op = self.eat().kind
            node = ("BIN", op, node, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.cur().kind in ("*", "/"):
            op = self.eat().kind
            node = ("BIN", op, node, self.factor())
        return node

    def factor(self):
        t = self.cur()
        if t.kind == "NUMBER":
            return ("NUM", int(self.eat("NUMBER").value))
        if t.kind == "IDENT":
            name = self.eat("IDENT").value
            if self.cur().kind == "(":
                self.eat("(")
                args = []
                if self.cur().kind != ")":
                    args.append(self.expr())
                    while self.cur().kind == ",":
                        self.eat(",")
                        args.append(self.expr())
                self.eat(")")
                return ("CALL", name, args)
            return ("VAR", name)
        if t.kind == "(":
            self.eat("(")
            node = self.expr()
            self.eat(")")
            return node
        raise SyntaxError(f"unexpected token: {t.kind}")


class Env:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def set(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(name)


class Function:
    def __init__(self, params, body, closure):
        self.params = params
        self.body = body
        self.closure = closure

    def call(self, args):
        if len(args) != len(self.params):
            raise TypeError("argument count mismatch")
        local = Env(self.closure)
        for n, v in zip(self.params, args):
            local.set(n, v)
        result = None
        for stmt in self.body:
            result = eval_stmt(stmt, local)
        return result


def eval_expr(node, env):
    t = node[0]
    if t == "NUM":
        return node[1]
    if t == "VAR":
        return env.get(node[1])
    if t == "BIN":
        op, left, right = node[1], node[2], node[3]
        a, b = eval_expr(left, env), eval_expr(right, env)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a // b
    if t == "CALL":
        fn_name, args = node[1], node[2]
        fn = env.get(fn_name)
        if not isinstance(fn, Function):
            raise TypeError(f"{fn_name} is not callable")
        return fn.call([eval_expr(a, env) for a in args])
    raise RuntimeError(f"unknown expr node: {t}")


def eval_stmt(node, env):
    t = node[0]
    if t == "ASSIGN":
        _, name, expr = node
        value = eval_expr(expr, env)
        env.set(name, value)
        return value
    if t == "PRINT":
        value = eval_expr(node[1], env)
        print(value)
        return value
    if t == "EXPR":
        return eval_expr(node[1], env)
    if t == "FN":
        _, name, params, body = node
        env.set(name, Function(params, body, env))
        return None
    raise RuntimeError(f"unknown stmt node: {t}")


def run(src: str):
    tokens = lex(src)
    ast = Parser(tokens).parse()
    env = Env()
    for stmt in ast[1]:
        eval_stmt(stmt, env)


def main():
    if len(sys.argv) != 2:
        print("usage: python3 mini_interpreter.py <file>")
        raise SystemExit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        run(f.read())


if __name__ == "__main__":
    main()
