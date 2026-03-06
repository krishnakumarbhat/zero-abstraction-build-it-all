#!/usr/bin/env python3
import math
import re
import socket
import sys
from collections import Counter, defaultdict, deque
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


STOP = {"the", "and", "is", "a", "an", "to", "of", "in", "for", "on", "with"}


class LinkTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.text_parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip = True
        if tag == "a":
            for k, v in attrs:
                if k == "href":
                    self.links.append(v)

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            self.text_parts.append(data)


def http_get(url: str) -> str:
    u = urlparse(url)
    host = u.hostname
    port = u.port or 80
    path = u.path or "/"
    if u.query:
        path += "?" + u.query
    with socket.create_connection((host, port), timeout=3) as s:
        req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode("utf-8"))
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    body = data.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in data else b""
    return body.decode("utf-8", errors="ignore")


def tokenize(text: str):
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP]


class SearchEngine:
    def __init__(self):
        self.docs = {}
        self.tf = {}
        self.df = defaultdict(int)
        self.index = defaultdict(list)

    def add_doc(self, doc_id: int, text: str):
        toks = tokenize(text)
        self.docs[doc_id] = text
        c = Counter(toks)
        self.tf[doc_id] = c
        for w in c:
            self.df[w] += 1
            self.index[w].append(doc_id)

    def score(self, query: str):
        q = tokenize(query)
        N = max(len(self.docs), 1)
        scores = defaultdict(float)
        for term in q:
            postings = self.index.get(term, [])
            idf = math.log((N + 1) / (1 + self.df.get(term, 0))) + 1.0
            for d in postings:
                tf = self.tf[d][term]
                scores[d] += tf * idf
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def crawl(seed: str, limit: int = 5):
    q = deque([seed])
    seen = {seed}
    docs = []
    while q and len(docs) < limit:
        u = q.popleft()
        try:
            html = http_get(u)
        except Exception:
            continue
        p = LinkTextParser()
        p.feed(html)
        docs.append((u, " ".join(p.text_parts)))
        for l in p.links:
            nxt = urljoin(u, l)
            if urlparse(nxt).scheme == "http" and nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return docs


def self_test():
    se = SearchEngine()
    se.add_doc(1, "hello world world")
    se.add_doc(2, "goodbye world")
    r = se.score("hello")
    assert r and r[0][0] == 1
    print("ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        sys.exit(0)
    if len(sys.argv) < 3:
        print("usage: search.py <seed-url> <query>")
        sys.exit(1)
    seed, query = sys.argv[1], sys.argv[2]
    docs = crawl(seed, limit=5)
    se = SearchEngine()
    for i, (_, text) in enumerate(docs, 1):
        se.add_doc(i, text)
    print(se.score(query))
