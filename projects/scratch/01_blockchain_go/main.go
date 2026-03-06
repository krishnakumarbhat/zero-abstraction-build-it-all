package main

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "net"
    "os"
    "strconv"
    "strings"
    "sync"
    "time"
)

type Block struct {
    Index        int      `json:"index"`
    Timestamp    string   `json:"timestamp"`
    Transactions []string `json:"transactions"`
    PrevHash     string   `json:"prev_hash"`
    Nonce        uint64   `json:"nonce"`
    Hash         string   `json:"hash"`
}

type Blockchain struct {
    Difficulty int
    Chain      []Block
    mutex      sync.Mutex
}

func calculateHash(block Block) string {
    payload := fmt.Sprintf("%d|%s|%s|%s|%d", block.Index, block.Timestamp, strings.Join(block.Transactions, ","), block.PrevHash, block.Nonce)
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}

func mineBlock(block *Block, difficulty int) {
    targetPrefix := strings.Repeat("0", difficulty)
    for {
        h := calculateHash(*block)
        if strings.HasPrefix(h, targetPrefix) {
            block.Hash = h
            return
        }
        block.Nonce++
    }
}

func newGenesis() Block {
    b := Block{Index: 0, Timestamp: time.Now().UTC().Format(time.RFC3339Nano), Transactions: []string{"genesis"}, PrevHash: ""}
    mineBlock(&b, 2)
    return b
}

func newBlockchain(diff int) *Blockchain {
    return &Blockchain{Difficulty: diff, Chain: []Block{newGenesis()}}
}

func (bc *Blockchain) addBlock(txs []string) Block {
    bc.mutex.Lock()
    defer bc.mutex.Unlock()

    prev := bc.Chain[len(bc.Chain)-1]
    b := Block{Index: prev.Index + 1, Timestamp: time.Now().UTC().Format(time.RFC3339Nano), Transactions: txs, PrevHash: prev.Hash}
    mineBlock(&b, bc.Difficulty)
    bc.Chain = append(bc.Chain, b)
    return b
}

func (bc *Blockchain) isValid() bool {
    bc.mutex.Lock()
    defer bc.mutex.Unlock()
    targetPrefix := strings.Repeat("0", bc.Difficulty)
    for i := 1; i < len(bc.Chain); i++ {
        curr := bc.Chain[i]
        prev := bc.Chain[i-1]
        if curr.PrevHash != prev.Hash {
            return false
        }
        if calculateHash(curr) != curr.Hash {
            return false
        }
        if !strings.HasPrefix(curr.Hash, targetPrefix) {
            return false
        }
    }
    return true
}

func startNode(bc *Blockchain, port string, peers []string) error {
    ln, err := net.Listen("tcp", ":"+port)
    if err != nil {
        return err
    }
    fmt.Println("node listening on", port)

    go func() {
        for {
            conn, err := ln.Accept()
            if err != nil {
                continue
            }
            go handleConn(conn, bc)
        }
    }()

    for {
        fmt.Print("tx> ")
        var line string
        if _, err := fmt.Scanln(&line); err != nil {
            continue
        }
        block := bc.addBlock([]string{line})
        payload, _ := json.Marshal(block)
        for _, p := range peers {
            if p == "" {
                continue
            }
            go func(peer string) {
                c, err := net.DialTimeout("tcp", peer, 2*time.Second)
                if err != nil {
                    return
                }
                defer c.Close()
                _, _ = c.Write(payload)
            }(p)
        }
        fmt.Println("mined", block.Index, block.Hash[:16], "...")
    }
}

func handleConn(conn net.Conn, bc *Blockchain) {
    defer conn.Close()
    dec := json.NewDecoder(conn)
    var b Block
    if err := dec.Decode(&b); err != nil {
        return
    }

    bc.mutex.Lock()
    defer bc.mutex.Unlock()
    prev := bc.Chain[len(bc.Chain)-1]
    if b.Index == prev.Index+1 && b.PrevHash == prev.Hash && calculateHash(b) == b.Hash {
        bc.Chain = append(bc.Chain, b)
        fmt.Println("synced block", b.Index)
    }
}

func selfTest() {
    bc := newBlockchain(2)
    bc.addBlock([]string{"alice->bob:10"})
    bc.addBlock([]string{"bob->carol:4"})
    if !bc.isValid() {
        panic("invalid chain")
    }
    fmt.Println("ok")
}

func main() {
    if len(os.Args) > 1 && os.Args[1] == "test" {
        selfTest()
        return
    }

    port := "9000"
    difficulty := 3
    peers := []string{}
    if len(os.Args) > 1 {
        port = os.Args[1]
    }
    if len(os.Args) > 2 {
        if v, err := strconv.Atoi(os.Args[2]); err == nil {
            difficulty = v
        }
    }
    if len(os.Args) > 3 {
        peers = strings.Split(os.Args[3], ",")
    }

    bc := newBlockchain(difficulty)
    fmt.Println("genesis:", bc.Chain[0].Hash)
    if err := startNode(bc, port, peers); err != nil {
        fmt.Println("error:", err)
    }
}
