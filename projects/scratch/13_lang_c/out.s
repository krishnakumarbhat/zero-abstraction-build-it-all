.intel_syntax noprefix
.global _start
_start:
  mov eax, 2
  add eax, 3
  ; a = eax
  mov eax, a
  add eax, 4
  ; b = eax
  mov eax, 60
  xor edi, edi
  syscall
