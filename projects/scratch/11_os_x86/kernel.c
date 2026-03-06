void kernel_main(void) {
    volatile char *vga = (volatile char *)0xB8000;
    const char *msg = "Hello from tiny kernel";
    for (int i = 0; msg[i]; i++) {
        vga[i * 2] = msg[i];
        vga[i * 2 + 1] = 0x0F;
    }
    while (1) {
        __asm__ __volatile__("hlt");
    }
}
