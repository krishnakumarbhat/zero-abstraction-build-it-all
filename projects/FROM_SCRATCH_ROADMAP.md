# From-Scratch Build Roadmap (No Libraries)

Build everything from scratch.

- Do not use high-level helper libraries/frameworks that solve the core problem for you.
- Use standard libraries and OS/system primitives only where necessary.
- Implement core algorithms, parsers, protocols, data structures, and execution loops yourself.

## 1) Build your own Blockchain / Cryptocurrency

Best Language: Go (for easy concurrency and standard crypto libraries) or Python.

Step-by-Step Roadmap:

1. Block Structure: Define a class/struct for a Block containing an index, timestamp, data (transactions), the previous block's hash, and its own hash.
2. Hashing: Implement SHA-256 hashing using the standard library to uniquely identify blocks.
3. The Chain: Create the genesis block and write logic to validate that every new block’s prev_hash perfectly matches the actual hash of the preceding block.
4. Proof of Work: Implement a mining algorithm that increments a nonce value until the block's hash starts with a specific number of zeroes.
5. P2P Network: Use raw TCP sockets to connect multiple nodes so they can broadcast and sync new blocks.

## 2) Build your own Command-Line Tool

Best Language: C or Go.

Step-by-Step Roadmap:

1. Argv Parsing: Read the command-line arguments passed into your program's main function.
2. Flag Handling: Write string-matching logic to parse flags (like -v or --help) without using built-in parsing libraries.
3. Standard I/O: Read input from stdin and print out to stdout and stderr.
4. Core Logic: Implement the tool's purpose (e.g., a custom grep or cat clone) by manipulating strings or reading files byte-by-byte.
5. Exit Codes: Ensure your program returns 0 on success and 1 (or higher) on failure for shell scripting compatibility.

## 3) Build your own Database (Python)

Best Language: Python.

Step-by-Step Roadmap:

1. Append-Only Log: Write a function that appends new key-value pairs to the end of a plain text or binary file (this guarantees fast writes).
2. In-Memory Index: Create a Python dictionary that maps a Key to its specific byte offset (file position) in the log file.
3. Point Lookups: Implement a read function that uses the dictionary index to seek directly to the correct byte in the file and return the value.
4. Compaction: Write a background process that reads the log, removes overwritten or deleted keys, and writes a fresh, compressed log file.
5. Basic Query Language: Parse simple text strings (like SET key value or GET key) to interact with the database.

## 4) Build your own Docker (Container Runtime)

Best Language: Go or C (requires direct access to Linux system calls).

Step-by-Step Roadmap:

1. Chroot: Use the chroot system call to change the root directory of your process, trapping it in an isolated filesystem.
2. Namespaces: Use the unshare or clone system calls to create isolated PID, Mount, and Network namespaces (so the container cannot see host processes).
3. Cgroups: Write to the /sys/fs/cgroup filesystem to strictly limit the CPU and Memory the process is allowed to use.
4. Image Unpacking: Download a base filesystem tarball (like Alpine Linux) and extract it into your chroot directory.
5. Execution: Use exec to launch a shell or application inside this perfectly isolated environment.

## 5) Build your own Emulator / Virtual Machine

Best Language: C or C++.

Step-by-Step Roadmap:

1. Memory & Registers: Define arrays to represent the system's RAM (e.g., 4KB) and the CPU's internal registers.
2. Fetch Cycle: Read the next instruction (opcode) from the memory array based on the Program Counter (PC).
3. Decode Cycle: Use bitwise operators (&, |, >>) to mask the opcode and figure out what instruction it represents.
4. Execute Cycle: Write the logic for each instruction (e.g., add two registers, jump to a new memory address).
5. I/O Loop: Map specific memory addresses to terminal output or keyboard input to interact with the virtual machine.

## 6) Build your own Front-end Framework (JS)

Best Language: JavaScript.

Step-by-Step Roadmap:

1. Virtual DOM: Create a JS function that returns a plain JavaScript object representing an HTML structure (tag name, props, children).
2. Mounting: Write a render function that takes this Virtual DOM object and converts it into actual document.createElement nodes on the webpage.
3. Reactivity: Implement a basic State or Signal system. When a variable changes, trigger a re-render.
4. Diffing Algorithm: Write a recursive function that compares the old Virtual DOM tree with the new Virtual DOM tree to find exactly what changed.
5. Patching: Apply only those specific changes to the real HTML DOM to keep performance high.

## 7) Build your own Git

Best Language: C or Python.

Step-by-Step Roadmap:

1. Initialization: Create a command that builds the .git directory structure, including objects and refs folders.
2. Hashing: Implement a function to hash file contents using SHA-1.
3. Blobs: Write file contents (compressed using standard zlib) into the .git/objects folder, named by their hash.
4. Trees: Create directory tree objects that map file names to their respective blob hashes.
5. Commits: Create commit objects that point to a top-level tree, record the author, and link to a parent commit.

## 8) Build your own Memory Allocator

Best Language: C.

Step-by-Step Roadmap:

1. System Call: Use mmap or sbrk to request a large, raw chunk of memory directly from the operating system kernel.
2. Free List: Build a linked list data structure inside that memory chunk to keep track of which blocks are free and which are in use.
3. Malloc: Write logic to search the free list for a block large enough to satisfy the user's request, split the block if it's too big, and return a pointer.
4. Free: Write logic to take a pointer, mark its block as free, and add it back to the free list.
5. Coalescing: Write a background check that merges adjacent free blocks together to prevent memory fragmentation.

## 9) Build your own Network Stack

Best Language: C.

Step-by-Step Roadmap:

1. Virtual Interface: Open a TUN/TAP device on Linux to read and write raw network packets from user space.
2. Ethernet Layer: Parse the raw bytes to extract MAC addresses and the payload.
3. IP Layer: Decode IPv4 headers to verify checksums, source IPs, and destination IPs.
4. ICMP Layer: Implement logic to detect ping requests and construct a valid ping reply packet.
5. UDP/TCP: Build a simple state machine to strip UDP/TCP headers and route the payload to a specific port in your code.

## 10) Build your own Neural Network

Best Language: C, Python (NumPy), or Go.

Step-by-Step Roadmap:

1. Initialization: Create matrices for weights and vectors for biases, filling them with random small numbers.
2. Forward Pass: Implement matrix multiplication (dot product) to pass input data through the network layers, applying an activation function (like ReLU or Sigmoid) at each step.
3. Loss Calculation: Write a function (like Mean Squared Error) to measure how far off the network's prediction was from the truth.
4. Backpropagation: Use calculus (the chain rule) to calculate the gradient of the loss with respect to every weight in the network.
5. Gradient Descent: Update the weights by subtracting a small fraction of the gradient to improve the network's accuracy over time.

## 11) Build your own Operating System

Best Language: Assembly (x86) and C.

Step-by-Step Roadmap:

1. Bootloader: Write 16-bit Assembly that the BIOS loads. Switch the CPU into 32-bit Protected Mode.
2. Kernel Entry: Jump from Assembly into your C code's main() function.
3. VGA Driver: Write directly to memory address 0xB8000 to print characters and colors to the screen without an underlying OS.
4. Interrupts: Set up an Interrupt Descriptor Table (IDT) to catch hardware events like keyboard presses.
5. Memory Management: Build a physical page allocator to keep track of available system RAM.

## 12) Build your own Processor (Verilog)

Best Language: Verilog.

Step-by-Step Roadmap:

1. ALU (Arithmetic Logic Unit): Write the logic gates to perform addition, subtraction, AND, and OR operations based on a control signal.
2. Register File: Create an array of flip-flops to store temporary values (registers) that can be read and written simultaneously.
3. Instruction Fetch: Build a Program Counter (PC) that increments on every clock cycle to fetch the next 32-bit instruction from memory.
4. Control Unit: Write the logic that looks at the instruction opcode and flips the correct switches to route data through the ALU and memory.
5. Integration: Wire the ALU, registers, and memory together into a single-cycle datapath.

## 13) Build your own Programming Language

Best Language: C (Compiler) and Assembly (Output).

Step-by-Step Roadmap:

1. Lexical Analysis: Write a scanner that reads raw text and groups characters into tokens (e.g., INT_KEYWORD, IDENTIFIER, EQUALS).
2. Parsing: Write a recursive descent parser that converts the tokens into an Abstract Syntax Tree (AST) representing the grammar of your language.
3. Semantic Analysis: Traverse the AST to check for errors, like using a variable before it is declared or type mismatches.
4. Code Generation: Traverse the AST one final time and emit raw x86 Assembly strings for each node (e.g., translating a + b into add eax, ebx).
5. Assembly Output: Save the generated strings to a .s file.

## 14) Build your own Regex Engine

Best Language: C.

Step-by-Step Roadmap:

1. Regex Parser: Convert the regular expression string into a tree structure handling operators like *, |, and ().
2. NFA Construction: Convert the parsed tree into a Non-deterministic Finite Automaton (a state machine where one input can lead to multiple states) using Thompson's construction.
3. State Machine Simulation: Write an execution loop that feeds the input string into the NFA, tracking all possible active states simultaneously.
4. Character Classes: Add support for ranges like [a-z] by modifying the state transitions.
5. Matching: If any of the active states reach the accept state at the end of the input string, return a successful match.

## 15) Build your own Search Engine

Best Language: Python.

Step-by-Step Roadmap:

1. Web Crawler: Use standard socket HTTP requests to download raw HTML from a seed URL, parse href tags to find new links, and queue them up.
2. Text Extraction: Strip out HTML tags and script blocks to isolate the pure text content of the page.
3. Tokenization: Split the text into individual words, lowercase them, and remove common stop words (like the, and, is).
4. Inverted Index: Build a massive dictionary where the keys are words, and the values are lists of Document IDs that contain that word.
5. Ranking Engine: Implement TF-IDF (Term Frequency-Inverse Document Frequency) to score and sort the Document IDs based on how relevant they are to a search query.

## 16) Build your own Text Editor (Without Libraries)

Best Language: C.

Step-by-Step Roadmap:

1. Raw Mode: Use POSIX termios system calls to disable terminal echoing and line-buffering, allowing you to read keystrokes instantly.
2. Input Loop: Write a loop that listens for byte sequences, distinguishing normal characters from arrow keys or escape sequences.
3. Gap Buffer: Implement a Gap Buffer data structure to hold the text efficiently in memory (allowing fast insertions and deletions near the cursor).
4. Screen Rendering: Use ANSI escape sequences to clear the screen, move the cursor, and redraw the entire text buffer to the terminal on every keystroke.
5. File I/O: Add functionality to save the in-memory buffer to a file and load text from a file upon startup.

## 17) Build your own Web Browser

Best Language: C++ or Python.

Step-by-Step Roadmap:

1. HTTP Client: Use raw TCP sockets to connect to a server, send a GET request, and receive the raw HTML response.
2. HTML Parser: Write a state machine to parse the HTML tags and build a DOM (Document Object Model) tree in memory.
3. CSS Parser: Parse style blocks to map rules (like color: red) to specific elements in the DOM.
4. Layout Engine: Traverse the DOM tree and calculate the exact X, Y coordinates, width, and height for every element based on block/inline rules.
5. Painting: Use a basic graphics library (the only library you might need for OS-level pixel drawing) to paint text and rectangles onto a window based on your layout calculations.

## 18) Build your own Web Server

Best Language: C.

Step-by-Step Roadmap:

1. Socket Setup: Create a TCP socket, bind it to port 80 (or 8080), and set it to listen for incoming connections.
2. Accept Loop: Block the main thread until a client connects, then accept the connection to get a client socket.
3. Request Parsing: Read the raw byte stream from the client and parse the HTTP method (GET) and the requested file path.
4. File System Reading: Open the requested file from your hard drive and read its contents into a buffer.
5. Response Construction: Manually construct an HTTP response string (e.g., HTTP/1.1 200 OK\r\n\r\n) followed by the file contents, send it back through the client socket, and close the connection.
