package main

import (
    "bufio"
    "fmt"
    "net"
    "strings"
)

type request struct {
    Method  string
    Path    string
    Version string
    Headers map[string]string
}

func parseRequest(conn net.Conn) (*request, error) {
    rd := bufio.NewReader(conn)

    line, err := rd.ReadString('\n')
    if err != nil {
        return nil, err
    }
    line = strings.TrimSpace(line)
    parts := strings.Split(line, " ")
    if len(parts) != 3 {
        return nil, fmt.Errorf("bad request line")
    }

    req := &request{
        Method:  parts[0],
        Path:    parts[1],
        Version: parts[2],
        Headers: map[string]string{},
    }

    for {
        h, err := rd.ReadString('\n')
        if err != nil {
            return nil, err
        }
        h = strings.TrimSpace(h)
        if h == "" {
            break
        }
        kv := strings.SplitN(h, ":", 2)
        if len(kv) == 2 {
            req.Headers[strings.TrimSpace(strings.ToLower(kv[0]))] = strings.TrimSpace(kv[1])
        }
    }

    return req, nil
}

func writeResponse(conn net.Conn, status string, contentType string, body string) {
    response := fmt.Sprintf(
        "HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s",
        status,
        contentType,
        len(body),
        body,
    )
    _, _ = conn.Write([]byte(response))
}

func handle(conn net.Conn) {
    defer conn.Close()

    req, err := parseRequest(conn)
    if err != nil {
        writeResponse(conn, "400 Bad Request", "text/plain", "bad request")
        return
    }

    if req.Method == "GET" && req.Path == "/" {
        writeResponse(conn, "200 OK", "text/plain", "hello from mini http server\n")
        return
    }
    if req.Method == "GET" && req.Path == "/health" {
        writeResponse(conn, "200 OK", "text/plain", "ok\n")
        return
    }
    writeResponse(conn, "404 Not Found", "text/plain", "not found\n")
}

func main() {
    ln, err := net.Listen("tcp", ":8080")
    if err != nil {
        panic(err)
    }
    defer ln.Close()

    fmt.Println("mini-http listening on :8080")
    for {
        conn, err := ln.Accept()
        if err != nil {
            continue
        }
        go handle(conn)
    }
}
