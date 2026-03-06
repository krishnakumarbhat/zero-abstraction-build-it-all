# 07 - Build Your Own Git (Python)

## Features (MVP)

- `init`: create `.git` directory structure
- `hash-object -w <file>`: blob object with zlib + SHA-1
- `cat-file -p <sha1>`: read and print object contents

## Run

```bash
python3 mini_git.py init
python3 mini_git.py hash-object -w hello.txt
python3 mini_git.py cat-file -p <hash>
```
