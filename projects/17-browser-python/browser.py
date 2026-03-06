#!/usr/bin/env python3
import argparse
import socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


@dataclass
class Node:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    children: List["Node"] = field(default_factory=list)
    text: str = ""
    computed: Dict[str, str] = field(default_factory=dict)


@dataclass
class CSSRule:
    selector: str
    declarations: Dict[str, str]


def fetch_http(url: str, timeout: float = 5.0) -> Tuple[str, Dict[str, str], str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", ""):
        raise ValueError("Only http:// URLs are supported")

    host = parsed.hostname
    if not host:
        raise ValueError("Missing host in URL")
    port = parsed.port or 80
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: close\r\n"
        "User-Agent: mini-browser/0.1\r\n"
        "Accept: text/html,*/*\r\n"
        "\r\n"
    ).encode("utf-8")

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(request)
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)

    raw = b"".join(chunks)
    if b"\r\n\r\n" not in raw:
        raise RuntimeError("Invalid HTTP response")
    header_bytes, body_bytes = raw.split(b"\r\n\r\n", 1)

    header_text = header_bytes.decode("iso-8859-1", errors="replace")
    header_lines = header_text.split("\r\n")
    status_line = header_lines[0] if header_lines else ""
    headers: Dict[str, str] = {}
    for line in header_lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    body = body_bytes.decode("utf-8", errors="replace")
    return status_line, headers, body


def parse_attrs(raw: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    i = 0
    n = len(raw)
    while i < n:
        while i < n and raw[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and not raw[i].isspace() and raw[i] != "=":
            i += 1
        key = raw[start:i].strip().lower()
        while i < n and raw[i].isspace():
            i += 1
        value = ""
        if i < n and raw[i] == "=":
            i += 1
            while i < n and raw[i].isspace():
                i += 1
            if i < n and raw[i] in ('"', "'"):
                quote = raw[i]
                i += 1
                start = i
                while i < n and raw[i] != quote:
                    i += 1
                value = raw[start:i]
                if i < n and raw[i] == quote:
                    i += 1
            else:
                start = i
                while i < n and not raw[i].isspace():
                    i += 1
                value = raw[start:i]
        if key:
            attrs[key] = value
    return attrs


def parse_html(html: str) -> Node:
    root = Node("document")
    stack: List[Node] = [root]
    i = 0
    n = len(html)
    text_buf: List[str] = []

    def flush_text() -> None:
        if text_buf:
            text = "".join(text_buf)
            if text.strip():
                stack[-1].children.append(Node("#text", text=text))
            text_buf.clear()

    while i < n:
        c = html[i]
        if c == "<":
            flush_text()
            j = html.find(">", i + 1)
            if j == -1:
                break
            token = html[i + 1 : j].strip()
            if token.startswith("!--"):
                end_comment = html.find("-->", i + 4)
                if end_comment == -1:
                    break
                i = end_comment + 3
                continue

            if token.startswith("/"):
                tag = token[1:].strip().lower()
                while len(stack) > 1 and stack[-1].tag != tag:
                    stack.pop()
                if len(stack) > 1 and stack[-1].tag == tag:
                    stack.pop()
            else:
                self_closing = token.endswith("/")
                if self_closing:
                    token = token[:-1].strip()
                parts = token.split(None, 1)
                tag = parts[0].lower() if parts else "div"
                attrs = parse_attrs(parts[1] if len(parts) > 1 else "")
                node = Node(tag=tag, attrs=attrs)
                stack[-1].children.append(node)
                if not self_closing and tag not in {"br", "img", "meta", "link", "hr", "input"}:
                    stack.append(node)
            i = j + 1
        else:
            text_buf.append(c)
            i += 1

    flush_text()
    return root


def collect_style_blocks(node: Node, out: List[str]) -> None:
    if node.tag == "style":
        text_parts = [child.text for child in node.children if child.tag == "#text"]
        if text_parts:
            out.append(" ".join(text_parts))
    for child in node.children:
        collect_style_blocks(child, out)


def parse_css(css: str) -> List[CSSRule]:
    rules: List[CSSRule] = []
    i = 0
    n = len(css)
    while i < n:
        while i < n and css[i].isspace():
            i += 1
        if i >= n:
            break
        sel_start = i
        while i < n and css[i] != "{":
            i += 1
        if i >= n:
            break
        selector = css[sel_start:i].strip()
        i += 1
        body_start = i
        depth = 1
        while i < n and depth > 0:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
            i += 1
        body = css[body_start : i - 1]
        decls: Dict[str, str] = {}
        for part in body.split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                decls[k.strip().lower()] = v.strip()
        if selector and decls:
            rules.append(CSSRule(selector=selector.lower(), declarations=decls))
    return rules


def style_matches(rule: CSSRule, node: Node) -> bool:
    sel = rule.selector
    if sel.startswith("#"):
        return node.attrs.get("id", "") == sel[1:]
    if sel.startswith("."):
        classes = node.attrs.get("class", "").split()
        return sel[1:] in classes
    return node.tag == sel


def apply_styles(node: Node, rules: List[CSSRule]) -> None:
    if node.tag != "#text":
        computed: Dict[str, str] = {}
        for rule in rules:
            if style_matches(rule, node):
                computed.update(rule.declarations)

        if "style" in node.attrs:
            inline = node.attrs["style"]
            for part in inline.split(";"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    computed[k.strip().lower()] = v.strip()
        node.computed = computed

    for child in node.children:
        apply_styles(child, rules)


def text_wrap(text: str, width: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    line = words[0]
    for word in words[1:]:
        if len(line) + 1 + len(word) <= width:
            line += " " + word
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def layout_and_paint(node: Node, width: int = 80) -> str:
    lines: List[str] = []

    def walk(n: Node, depth: int) -> None:
        indent = " " * min(depth * 2, 20)
        if n.tag == "#text":
            for wrapped in text_wrap(n.text.strip(), max(10, width - len(indent))):
                lines.append(indent + wrapped)
            return

        block_tags = {"html", "body", "div", "p", "section", "article", "h1", "h2", "h3", "ul", "ol", "li", "pre"}
        if n.tag in block_tags and n.tag not in {"html", "body"}:
            label = n.tag
            if n.computed:
                style_preview = ", ".join([f"{k}:{v}" for k, v in list(n.computed.items())[:2]])
                label = f"{label} [{style_preview}]"
            lines.append(indent + f"<{label}>")

        child_depth = depth + (1 if n.tag in block_tags else 0)
        for child in n.children:
            walk(child, child_depth)

        if n.tag in {"p", "div", "section", "article", "h1", "h2", "h3", "li"}:
            lines.append("")

    walk(node, 0)
    rendered = "\n".join(lines)
    return rendered.strip() + "\n"


def render_url(url: str, width: int = 80) -> str:
    status, headers, body = fetch_http(url)
    _ = headers
    dom = parse_html(body)

    css_blocks: List[str] = []
    collect_style_blocks(dom, css_blocks)
    rules: List[CSSRule] = []
    for css in css_blocks:
        rules.extend(parse_css(css))

    apply_styles(dom, rules)
    painted = layout_and_paint(dom, width=width)

    out = [f"STATUS: {status}", "", painted]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mini from-scratch browser")
    parser.add_argument("url", help="http:// URL to fetch")
    parser.add_argument("--width", type=int, default=80, help="terminal render width")
    args = parser.parse_args()

    try:
        output = render_url(args.url, width=args.width)
        print(output, end="")
        return 0
    except Exception as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
