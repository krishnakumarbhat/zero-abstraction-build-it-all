import hashlib
import os
import sys
import zlib


def repo_path(*parts):
    return os.path.join(".git", *parts)


def cmd_init():
    os.makedirs(repo_path("objects"), exist_ok=True)
    os.makedirs(repo_path("refs", "heads"), exist_ok=True)
    os.makedirs(repo_path("refs", "tags"), exist_ok=True)
    with open(repo_path("HEAD"), "w", encoding="utf-8") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized empty Git repository in .git")


def hash_object(data: bytes, obj_type: str = "blob", write: bool = False) -> str:
    header = f"{obj_type} {len(data)}\0".encode("utf-8")
    full = header + data
    sha1 = hashlib.sha1(full).hexdigest()

    if write:
        obj_dir = repo_path("objects", sha1[:2])
        obj_file = repo_path("objects", sha1[:2], sha1[2:])
        os.makedirs(obj_dir, exist_ok=True)
        with open(obj_file, "wb") as f:
            f.write(zlib.compress(full))

    return sha1


def read_object(sha1: str) -> tuple[str, bytes]:
    obj_file = repo_path("objects", sha1[:2], sha1[2:])
    with open(obj_file, "rb") as f:
        raw = zlib.decompress(f.read())
    header, body = raw.split(b"\0", 1)
    obj_type, _size = header.decode("utf-8").split(" ", 1)
    return obj_type, body


def cmd_hash_object(argv):
    write = "-w" in argv
    file_arg = argv[-1]
    with open(file_arg, "rb") as f:
        data = f.read()
    print(hash_object(data, "blob", write=write))


def cmd_cat_file(argv):
    if len(argv) != 2 or argv[0] != "-p":
        print("usage: cat-file -p <sha1>")
        raise SystemExit(1)
    obj_type, body = read_object(argv[1])
    if obj_type in ("blob", "commit", "tag"):
        sys.stdout.write(body.decode("utf-8", errors="replace"))
    else:
        sys.stdout.buffer.write(body)


def main():
    if len(sys.argv) < 2:
        print("usage: mini_git.py <command>")
        raise SystemExit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "init":
        cmd_init()
    elif cmd == "hash-object":
        cmd_hash_object(args)
    elif cmd == "cat-file":
        cmd_cat_file(args)
    else:
        print(f"unknown command: {cmd}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
