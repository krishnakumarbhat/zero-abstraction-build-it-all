#!/usr/bin/env python3
import os
import sys
import threading
from dataclasses import dataclass


@dataclass
class Record:
    op: str
    key: str
    value: str


class AppendOnlyDB:
    def __init__(self, path: str):
        self.path = path
        self.index = {}
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            open(path, "wb").close()
        self._rebuild_index()

    def _encode(self, rec: Record) -> bytes:
        return f"{rec.op}\t{rec.key}\t{rec.value}\n".encode("utf-8")

    def _decode(self, raw: bytes) -> Record:
        op, key, value = raw.decode("utf-8").rstrip("\n").split("\t", 2)
        return Record(op, key, value)

    def _rebuild_index(self):
        self.index.clear()
        with open(self.path, "rb") as f:
            while True:
                off = f.tell()
                line = f.readline()
                if not line:
                    break
                rec = self._decode(line)
                if rec.op == "SET":
                    self.index[rec.key] = off
                elif rec.op == "DEL" and rec.key in self.index:
                    del self.index[rec.key]

    def set(self, key: str, value: str):
        with self.lock, open(self.path, "ab") as f:
            off = f.tell()
            f.write(self._encode(Record("SET", key, value)))
            self.index[key] = off

    def get(self, key: str):
        off = self.index.get(key)
        if off is None:
            return None
        with open(self.path, "rb") as f:
            f.seek(off)
            rec = self._decode(f.readline())
            return rec.value

    def delete(self, key: str):
        with self.lock, open(self.path, "ab") as f:
            f.write(self._encode(Record("DEL", key, "")))
            self.index.pop(key, None)

    def compact(self):
        tmp = self.path + ".compact"
        with self.lock:
            with open(tmp, "wb") as out:
                new_index = {}
                for key in sorted(self.index.keys()):
                    value = self.get(key)
                    off = out.tell()
                    out.write(self._encode(Record("SET", key, value)))
                    new_index[key] = off
            os.replace(tmp, self.path)
            self.index = new_index


def repl(db: AppendOnlyDB):
    print("Commands: SET k v | GET k | DEL k | COMPACT | EXIT")
    while True:
        try:
            line = input("db> ").strip()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split(" ", 2)
        cmd = parts[0].upper()
        if cmd == "SET" and len(parts) == 3:
            k, v = parts[1], parts[2]
            db.set(k, v)
            print("OK")
        elif cmd == "GET" and len(parts) == 2:
            v = db.get(parts[1])
            print(v if v is not None else "(nil)")
        elif cmd == "DEL" and len(parts) == 2:
            db.delete(parts[1])
            print("OK")
        elif cmd == "COMPACT":
            db.compact()
            print("OK")
        elif cmd in {"EXIT", "QUIT"}:
            break
        else:
            print("ERR")


def self_test():
    p = ".db_test.log"
    if os.path.exists(p):
        os.remove(p)
    db = AppendOnlyDB(p)
    db.set("a", "1")
    db.set("b", "2")
    db.set("a", "3")
    assert db.get("a") == "3"
    db.delete("b")
    assert db.get("b") is None
    db.compact()
    assert db.get("a") == "3"
    os.remove(p)
    print("ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        sys.exit(0)
    db = AppendOnlyDB(sys.argv[1] if len(sys.argv) > 1 else "db.log")
    repl(db)
