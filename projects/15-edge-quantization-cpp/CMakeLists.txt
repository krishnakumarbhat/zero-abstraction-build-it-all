cmake_minimum_required(VERSION 3.16)
project(edge_quantization_engine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(quant_engine src/main.cpp)

target_compile_options(quant_engine PRIVATE -O3 -march=native)
