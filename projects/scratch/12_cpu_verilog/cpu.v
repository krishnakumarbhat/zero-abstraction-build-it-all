module alu(input [31:0] a, input [31:0] b, input [1:0] op, output reg [31:0] y);
  always @(*) begin
    case(op)
      2'b00: y = a + b;
      2'b01: y = a - b;
      2'b10: y = a & b;
      2'b11: y = a | b;
    endcase
  end
endmodule

module regfile(input clk, input we, input [4:0] ra1, input [4:0] ra2, input [4:0] wa, input [31:0] wd,
               output [31:0] rd1, output [31:0] rd2);
  reg [31:0] regs[0:31];
  assign rd1 = regs[ra1];
  assign rd2 = regs[ra2];
  always @(posedge clk) begin
    if (we && wa != 0) regs[wa] <= wd;
  end
endmodule

module cpu(input clk, input reset);
  reg [31:0] pc;
  reg [31:0] imem[0:255];
  wire [31:0] instr = imem[pc[9:2]];

  wire [4:0] rs = instr[25:21];
  wire [4:0] rt = instr[20:16];
  wire [4:0] rd = instr[15:11];
  wire [5:0] opcode = instr[31:26];
  wire [5:0] funct = instr[5:0];

  wire [31:0] rd1, rd2;
  reg we;
  reg [4:0] wa;
  reg [1:0] aluop;
  wire [31:0] y;

  regfile rf(clk, we, rs, rt, wa, y, rd1, rd2);
  alu a1(rd1, rd2, aluop, y);

  always @(*) begin
    we = 0;
    wa = rd;
    aluop = 2'b00;
    if (opcode == 0) begin
      we = 1;
      case (funct)
        6'h20: aluop = 2'b00;
        6'h22: aluop = 2'b01;
        6'h24: aluop = 2'b10;
        6'h25: aluop = 2'b11;
        default: begin we = 0; aluop = 2'b00; end
      endcase
    end
  end

  always @(posedge clk or posedge reset) begin
    if (reset) pc <= 0;
    else pc <= pc + 4;
  end
endmodule
