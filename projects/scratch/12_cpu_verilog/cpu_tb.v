`timescale 1ns/1ps
module cpu_tb;
  reg clk = 0;
  reg reset = 1;
  cpu uut(.clk(clk), .reset(reset));

  always #5 clk = ~clk;

  initial begin
    uut.rf.regs[1] = 10;
    uut.rf.regs[2] = 7;
    uut.imem[0] = {6'b000000, 5'd1, 5'd2, 5'd3, 5'd0, 6'h20};
    #12 reset = 0;
    #20;
    if (uut.rf.regs[3] !== 17) begin
      $display("FAIL got %d", uut.rf.regs[3]);
      $finish_and_return(1);
    end
    $display("PASS");
    $finish;
  end
endmodule
