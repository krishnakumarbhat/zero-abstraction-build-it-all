package main

import (
    "bufio"
    "fmt"
    "io"
    "net"
    "strconv"
    "strings"
    "sync"
    "time"
)

type item struct {
    value string
}

type store struct {
    mu   sync.RWMutex
    data map[string]item
}

func newStore() *store {
    return &store{data: make(map[string]item)}
}

func (s *store) set(key, value string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.data[key] = item{value: value}
}

func (s *store) get(key string) (string, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    v, ok := s.data[key]
    return v.value, ok
}

func (s *store) del(key string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    delete(s.data, key)
}

func readLine(r *bufio.Reader) (string, error) {
    line, err := r.ReadString('\n')
    if err != nil {
        return "", err
    }
    return strings.TrimSuffix(strings.TrimSuffix(line, "\n"), "\r"), nil
}

func parseRESPArray(r *bufio.Reader) ([]string, error) {
    first, err := r.ReadByte()
    if err != nil {
        return nil, err
    }
    if first != '*' {
        return nil, fmt.Errorf("expected array")
    }

    nLine, err := readLine(r)
    if err != nil {
        return nil, err
    }
    n, err := strconv.Atoi(nLine)
    if err != nil || n < 0 {
        return nil, fmt.Errorf("invalid array length")
    }

    parts := make([]string, 0, n)
    for i := 0; i < n; i++ {
        t, err := r.ReadByte()
        if err != nil {
            return nil, err
        }
        if t != '$' {
            return nil, fmt.Errorf("expected bulk string")
        }
        lLine, err := readLine(r)
        if err != nil {
            return nil, err
        }
        l, err := strconv.Atoi(lLine)
        if err != nil || l < 0 {
            return nil, fmt.Errorf("invalid bulk length")
        }

        buf := make([]byte, l)
        if _, err := io.ReadFull(r, buf); err != nil {
            return nil, err
        }
        if _, err := r.ReadByte(); err != nil {
            return nil, err
        }
        if _, err := r.ReadByte(); err != nil {
            return nil, err
        }
        parts = append(parts, string(buf))
    }

    return parts, nil
}

func simpleString(s string) string { return "+" + s + "\r\n" }
func bulkString(s string) string   { return "$" + strconv.Itoa(len(s)) + "\r\n" + s + "\r\n" }
func nullBulk() string             { return "$-1\r\n" }
func errString(s string) string    { return "-ERR " + s + "\r\n" }

func handleConn(conn net.Conn, s *store) {
    defer conn.Close()
    reader := bufio.NewReader(conn)

    for {
        parts, err := parseRESPArray(reader)
        if err != nil {
            if err != io.EOF {
                _, _ = conn.Write([]byte(errString("protocol error")))
            }
            return
        }
        if len(parts) == 0 {
            _, _ = conn.Write([]byte(errString("empty command")))
            continue
        }

        cmd := strings.ToUpper(parts[0])
        switch cmd {
        case "PING":
            if len(parts) == 2 {
                _, _ = conn.Write([]byte(bulkString(parts[1])))
            } else {
                _, _ = conn.Write([]byte(simpleString("PONG")))
            }
        case "SET":
            if len(parts) < 3 {
                _, _ = conn.Write([]byte(errString("wrong number of arguments for 'set'")))
                continue
            }
            key := parts[1]
            value := parts[2]
            s.set(key, value)

            if len(parts) >= 5 && strings.ToUpper(parts[3]) == "PX" {
                ms, parseErr := strconv.Atoi(parts[4])
                if parseErr == nil && ms >= 0 {
                    time.AfterFunc(time.Duration(ms)*time.Millisecond, func() {
                        s.del(key)
                    })
                }
            }

            _, _ = conn.Write([]byte(simpleString("OK")))
        case "GET":
            if len(parts) != 2 {
                _, _ = conn.Write([]byte(errString("wrong number of arguments for 'get'")))
                continue
            }
            if v, ok := s.get(parts[1]); ok {
                _, _ = conn.Write([]byte(bulkString(v)))
            } else {
                _, _ = conn.Write([]byte(nullBulk()))
            }
        default:
            _, _ = conn.Write([]byte(errString("unknown command '" + strings.ToLower(parts[0]) + "'")))
        }
    }
}

func main() {
    ln, err := net.Listen("tcp", ":6379")
    if err != nil {
        panic(err)
    }
    defer ln.Close()

    db := newStore()
    fmt.Println("mini-redis listening on :6379")

    for {
        conn, err := ln.Accept()
        if err != nil {
            continue
        }
        go handleConn(conn, db)
    }
}
