#!/usr/bin/env python3
import hashlib
import os
import sys
import time
import zlib


def repo_paths():
    g = ".git"
    return {
        "git": g,
        "objects": os.path.join(g, "objects"),
        "refs": os.path.join(g, "refs", "heads"),
        "head": os.path.join(g, "HEAD"),
    }


def init_repo():
    p = repo_paths()
    os.makedirs(p["objects"], exist_ok=True)
    os.makedirs(p["refs"], exist_ok=True)
    if not os.path.exists(p["head"]):
        with open(p["head"], "w", encoding="utf-8") as f:
            f.write("ref: refs/heads/main\n")
    print("Initialized empty mini git repo")


def hash_object(data: bytes, obj_type: str = "blob", write: bool = True) -> str:
    header = f"{obj_type} {len(data)}\0".encode("utf-8")
    full = header + data
    oid = hashlib.sha1(full).hexdigest()
    if write:
        p = repo_paths()
        d = os.path.join(p["objects"], oid[:2])
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, oid[2:])
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(zlib.compress(full))
    return oid


def write_tree(root: str = ".") -> str:
    entries = []
    for name in sorted(os.listdir(root)):
        if name == ".git":
            continue
        p = os.path.join(root, name)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                oid = hash_object(f.read(), "blob")
            entries.append(f"100644 {name}\0".encode("utf-8") + bytes.fromhex(oid))
    data = b"".join(entries)
    return hash_object(data, "tree")


def get_head_commit():
    ref = os.path.join(".git", "refs", "heads", "main")
    if os.path.exists(ref):
        return open(ref, "r", encoding="utf-8").read().strip() or None
    return None


def commit(message: str, author: str = "you <you@example.com>") -> str:
    tree = write_tree(".")
    parent = get_head_commit()
    now = int(time.time())
    lines = [f"tree {tree}"]
    if parent:
        lines.append(f"parent {parent}")
    lines.append(f"author {author} {now} +0000")
    lines.append(f"committer {author} {now} +0000")
    lines.append("")
    lines.append(message)
    oid = hash_object("\n".join(lines).encode("utf-8"), "commit")
    ref = os.path.join(".git", "refs", "heads", "main")
    os.makedirs(os.path.dirname(ref), exist_ok=True)
    with open(ref, "w", encoding="utf-8") as f:
        f.write(oid + "\n")
    return oid


def self_test():
    wd = ".mini_git_test"
    if os.path.exists(wd):
        import shutil
        shutil.rmtree(wd)
    os.makedirs(wd)
    cur = os.getcwd()
    os.chdir(wd)
    try:
        init_repo()
        with open("hello.txt", "w", encoding="utf-8") as f:
            f.write("hello")
        oid = commit("first")
        assert len(oid) == 40
        print("ok")
    finally:
        os.chdir(cur)


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        self_test()
        return
    if len(argv) < 2:
        print("usage: pygit.py init|hash-object <file>|write-tree|commit <msg>")
        return
    cmd = argv[1]
    if cmd == "init":
        init_repo()
    elif cmd == "hash-object" and len(argv) >= 3:
        with open(argv[2], "rb") as f:
            print(hash_object(f.read(), "blob"))
    elif cmd == "write-tree":
        print(write_tree("."))
    elif cmd == "commit" and len(argv) >= 3:
        print(commit(argv[2]))
    else:
        print("bad args")


if __name__ == "__main__":
    main(sys.argv)
