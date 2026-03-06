all: os-image.bin

boot.bin: boot.asm
	nasm -f bin boot.asm -o boot.bin

kernel.o: kernel.c
	gcc -m32 -ffreestanding -fno-pic -c kernel.c -o kernel.o

kernel.bin: kernel.o linker.ld
	ld -m elf_i386 -T linker.ld -o kernel.elf kernel.o
	objcopy -O binary kernel.elf kernel.bin

os-image.bin: boot.bin kernel.bin
	cat boot.bin kernel.bin > os-image.bin

clean:
	rm -f *.bin *.o *.elf
