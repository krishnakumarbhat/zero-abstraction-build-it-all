#!/usr/bin/env bash
set -euo pipefail

echo "== Smoke tests (best effort) =="

has() { command -v "$1" >/dev/null 2>&1; }

if has go; then
  echo "[01] blockchain_go"
  (cd 01_blockchain_go && go run . test >/dev/null)

  echo "[04] container_go (build only)"
  (cd 04_container_go && go build .)
fi

if has gcc; then
  echo "[02] cli_tool_c"
  (cd 02_cli_tool_c && gcc -O2 -Wall -Wextra -std=c11 main.c -o cli_tool && echo "hello" | ./cli_tool hello >/dev/null)

  echo "[08] allocator_c"
  (cd 08_allocator_c && gcc -O2 -Wall -Wextra -std=c11 allocator.c -o allocator && ./allocator >/dev/null)

  echo "[09] network_stack_c"
  (cd 09_network_stack_c && gcc -O2 -Wall -Wextra -std=c11 main.c -o netstack && ./netstack >/dev/null)

  echo "[13] lang_c"
  (cd 13_lang_c && gcc -O2 -Wall -Wextra -std=c11 main.c -o tinycc && ./tinycc >/dev/null)

  echo "[14] regex_engine_c"
  (cd 14_regex_engine_c && gcc -O2 -Wall -Wextra -std=c11 main.c -o regex && ./regex "a*b" aaab >/dev/null)

  echo "[16] text_editor_c (build only)"
  (cd 16_text_editor_c && gcc -O2 -Wall -Wextra -std=c11 editor.c -o editor)

  echo "[18] web_server_c (build only)"
  (cd 18_web_server_c && gcc -O2 -Wall -Wextra -std=c11 server.c -o server)
fi

if has g++; then
  echo "[05] vm_cpp"
  (cd 05_vm_cpp && g++ -O2 -Wall -Wextra -std=c++17 main.cpp -o vm && ./vm >/dev/null)
fi

if has python3; then
  echo "[03] db_python"
  (cd 03_db_python && python3 db.py --self-test >/dev/null)

  echo "[07] git_python"
  (cd 07_git_python && python3 pygit.py --self-test >/dev/null)

  echo "[10] neural_net_python"
  (cd 10_neural_net_python && python3 nn.py --self-test >/dev/null)

  echo "[15] search_engine_python"
  (cd 15_search_engine_python && python3 search.py --self-test >/dev/null)

  echo "[17] web_browser_python"
  (cd 17_web_browser_python && python3 browser.py --self-test >/dev/null)
fi

if has iverilog; then
  echo "[12] cpu_verilog"
  (cd 12_cpu_verilog && iverilog -o cpu_tb cpu.v cpu_tb.v && vvp cpu_tb >/dev/null)
fi

echo "Smoke tests completed."
