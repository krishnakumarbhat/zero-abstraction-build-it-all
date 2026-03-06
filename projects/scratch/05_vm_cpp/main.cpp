#include <cstdint>
#include <iostream>
#include <vector>

struct VM {
    std::vector<uint8_t> mem;
    uint8_t reg[8]{};
    uint16_t pc = 0;
    bool halted = false;

    VM() : mem(4096, 0) {}

    void load(const std::vector<uint8_t> &program) {
        for (size_t i = 0; i < program.size() && i < mem.size(); i++) mem[i] = program[i];
    }

    uint16_t fetch() {
        uint16_t op = (mem[pc] << 8) | mem[pc + 1];
        pc += 2;
        return op;
    }

    void step() {
        uint16_t op = fetch();
        uint8_t code = (op >> 12) & 0xF;
        uint8_t x = (op >> 8) & 0xF;
        uint8_t y = (op >> 4) & 0xF;
        uint8_t kk = op & 0xFF;
        uint16_t nnn = op & 0x0FFF;

        switch (code) {
            case 0x0: halted = true; break;                 // 0x0000 HALT
            case 0x1: reg[x] = kk; break;                   // 1xkk: MOV Rx, imm
            case 0x2: reg[x] = (uint8_t)(reg[x] + reg[y]); break; // 2xy0: ADD Rx, Ry
            case 0x3: pc = nnn; break;                      // 3nnn: JMP
            case 0x4: if (reg[x] != 0) pc = nnn; break;     // 4xnn: JNZ Rx, addr(low 8 bits)
            case 0x5: std::cout << (int)reg[x] << "\n"; break; // 5x00: OUT Rx
            default: halted = true; break;
        }
    }

    void run(int max_steps = 10000) {
        int steps = 0;
        while (!halted && steps++ < max_steps) step();
    }
};

int main() {
    VM vm;
    std::vector<uint8_t> prog = {
        0x11, 0x05, // R1 = 5
        0x12, 0x07, // R2 = 7
        0x21, 0x20, // R1 = R1 + R2
        0x51, 0x00, // print R1 => 12
        0x00, 0x00  // halt
    };
    vm.load(prog);
    vm.run();
    return 0;
}
