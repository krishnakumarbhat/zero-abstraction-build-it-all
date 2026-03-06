#!/usr/bin/env python3
import re
import socket
import sys
import tkinter as tk
from html.parser import HTMLParser
from urllib.parse import urlparse


def http_get(url: str) -> str:
    u = urlparse(url)
    host = u.hostname
    port = u.port or 80
    path = u.path or "/"
    if u.query:
        path += "?" + u.query
    with socket.create_connection((host, port), timeout=5) as s:
        req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        data = b""
        while True:
            d = s.recv(4096)
            if not d:
                break
            data += d
    return data.split(b"\r\n\r\n", 1)[1].decode("utf-8", errors="ignore")


class DOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.css_blocks = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.css_blocks.append(data)
        else:
            t = data.strip()
            if t:
                self.texts.append(t)


def parse_css(css_text: str):
    rules = {}
    for m in re.finditer(r"([a-zA-Z0-9#\.]+)\s*\{([^}]*)\}", css_text):
        sel = m.group(1).strip()
        body = m.group(2)
        props = {}
        for decl in body.split(";"):
            if ":" in decl:
                k, v = decl.split(":", 1)
                props[k.strip()] = v.strip()
        rules[sel] = props
    return rules


def layout_lines(texts, width=80):
    lines = []
    for t in texts:
        while len(t) > width:
            lines.append(t[:width])
            t = t[width:]
        lines.append(t)
    return lines


def paint(lines):
    root = tk.Tk()
    root.title("Toy Browser")
    c = tk.Canvas(root, width=800, height=600, bg="white")
    c.pack(fill="both", expand=True)
    y = 20
    for line in lines:
        c.create_text(20, y, anchor="w", text=line, fill="black")
        y += 20
        if y > 580:
            break
    root.mainloop()


def self_test():
    css = parse_css("h1 { color: red; } p { margin: 2; }")
    assert css["h1"]["color"] == "red"
    lines = layout_lines(["hello"])
    assert lines[0] == "hello"
    print("ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        sys.exit(0)
    if len(sys.argv) < 2:
        print("usage: browser.py <url>")
        sys.exit(1)
    html = http_get(sys.argv[1])
    p = DOMParser()
    p.feed(html)
    _ = parse_css("\n".join(p.css_blocks))
    lines = layout_lines(p.texts)
    paint(lines)
