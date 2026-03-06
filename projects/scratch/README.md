# Zero Abstraction: Build It All (18 Projects)

This workspace contains **18 from-scratch educational implementations** matching your requested topics and languages.

## Projects

1. `01_blockchain_go` - blockchain + PoW + basic P2P sync (Go)
2. `02_cli_tool_c` - custom grep-like CLI parser without arg libraries (C)
3. `03_db_python` - append-only key-value DB with compaction (Python)
4. `04_container_go` - mini container runtime primitives (Go/Linux)
5. `05_vm_cpp` - tiny virtual machine emulator loop (C++)
6. `06_frontend_framework_js` - virtual DOM + diff + patch + state (JavaScript)
7. `07_git_python` - mini git-like object store (Python)
8. `08_allocator_c` - custom allocator over `mmap` + free-list + coalescing (C)
9. `09_network_stack_c` - packet parsing for Ethernet/IP/ICMP (C)
10. `10_neural_net_python` - neural net forward/backprop without ML libs (Python)
11. `11_os_x86` - tiny bootloader + kernel VGA print (x86 ASM + C)
12. `12_cpu_verilog` - single-cycle CPU datapath (Verilog)
13. `13_lang_c` - lexer/parser/semantic/codegen to x86 asm (C)
14. `14_regex_engine_c` - regex parser + NFA simulation (C)
15. `15_search_engine_python` - socket crawler + inverted index + TF-IDF (Python)
16. `16_text_editor_c` - raw terminal editor with gap buffer (C)
17. `17_web_browser_python` - toy browser: HTTP/HTML/CSS/layout/paint (Python)
18. `18_web_server_c` - from-scratch static HTTP server (C)

## Quick smoke tests

Run:

```bash
chmod +x run_smoke_tests.sh
./run_smoke_tests.sh
```

Some projects need elevated privileges or specific tooling (e.g. root for TUN/TAP or privileged ports).
