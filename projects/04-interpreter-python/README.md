# 04 - Build Your Own Interpreter (Python)

## Features (MVP)

- Lexer: tokenizes numbers, identifiers, operators, keywords
- Parser: recursive-descent into AST
- Tree-walk evaluator
- Environment with lexical scoping
- Functions and closures

## Language (mini)

- Variable assignment: `x = 2 + 3`
- Print: `print x`
- Function def:

```txt
fn add(a, b) {
  a + b
}
```

- Function call: `print add(2, 3)`

## Run

```bash
python3 mini_interpreter.py examples/sample.min
```
