package main

import (
    "bufio"
    "bytes"
    "encoding/binary"
    "fmt"
    "io"
    "net"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "sync"
)

var logMu sync.Mutex

func writeFrame(w io.Writer, correlationID int32, payload []byte) error {
    body := new(bytes.Buffer)
    _ = binary.Write(body, binary.BigEndian, correlationID)
    body.Write(payload)

    totalLen := int32(body.Len())
    if err := binary.Write(w, binary.BigEndian, totalLen); err != nil {
        return err
    }
    _, err := w.Write(body.Bytes())
    return err
}

func appendMessage(topic, value string) (int64, error) {
    if err := os.MkdirAll("data", 0755); err != nil {
        return 0, err
    }
    file := filepath.Join("data", topic+".log")

    logMu.Lock()
    defer logMu.Unlock()

    f, err := os.OpenFile(file, os.O_CREATE|os.O_RDWR|os.O_APPEND, 0644)
    if err != nil {
        return 0, err
    }
    defer f.Close()

    stat, _ := f.Stat()
    offset := stat.Size()
    _, err = f.WriteString(value + "\n")
    return offset, err
}

func fetchFromOffset(topic string, offset int64) ([]string, error) {
    file := filepath.Join("data", topic+".log")
    f, err := os.Open(file)
    if err != nil {
        return nil, err
    }
    defer f.Close()

    if _, err := f.Seek(offset, io.SeekStart); err != nil {
        return nil, err
    }

    scanner := bufio.NewScanner(f)
    var out []string
    for scanner.Scan() {
        out = append(out, scanner.Text())
    }
    return out, scanner.Err()
}

func handleConn(conn net.Conn) {
    defer conn.Close()
    reader := bufio.NewReader(conn)

    for {
        var length int32
        if err := binary.Read(reader, binary.BigEndian, &length); err != nil {
            return
        }
        if length <= 8 {
            return
        }

        frame := make([]byte, length)
        if _, err := io.ReadFull(reader, frame); err != nil {
            return
        }

        buf := bytes.NewReader(frame)
        var apiKey int16
        var version int16
        var correlationID int32
        _ = binary.Read(buf, binary.BigEndian, &apiKey)
        _ = binary.Read(buf, binary.BigEndian, &version)
        _ = binary.Read(buf, binary.BigEndian, &correlationID)

        payload, _ := io.ReadAll(buf)

        switch apiKey {
        case 18:
            _ = writeFrame(conn, correlationID, []byte("ApiVersions:18,0,1\n"))
        case 0:
            // payload: topic|value
            parts := strings.SplitN(string(payload), "|", 2)
            if len(parts) != 2 {
                _ = writeFrame(conn, correlationID, []byte("ERR invalid produce payload\n"))
                continue
            }
            off, err := appendMessage(parts[0], parts[1])
            if err != nil {
                _ = writeFrame(conn, correlationID, []byte("ERR "+err.Error()+"\n"))
                continue
            }
            _ = writeFrame(conn, correlationID, []byte("OK offset="+strconv.FormatInt(off, 10)+"\n"))
        case 1:
            // payload: topic|offset
            parts := strings.SplitN(string(payload), "|", 2)
            if len(parts) != 2 {
                _ = writeFrame(conn, correlationID, []byte("ERR invalid fetch payload\n"))
                continue
            }
            off, err := strconv.ParseInt(parts[1], 10, 64)
            if err != nil {
                _ = writeFrame(conn, correlationID, []byte("ERR invalid offset\n"))
                continue
            }
            msgs, err := fetchFromOffset(parts[0], off)
            if err != nil {
                _ = writeFrame(conn, correlationID, []byte("ERR "+err.Error()+"\n"))
                continue
            }
            _ = writeFrame(conn, correlationID, []byte(strings.Join(msgs, "\n")+"\n"))
        default:
            _ = writeFrame(conn, correlationID, []byte(fmt.Sprintf("ERR unknown apikey=%d v=%d\n", apiKey, version)))
        }
    }
}

func main() {
    ln, err := net.Listen("tcp", ":9092")
    if err != nil {
        panic(err)
    }
    defer ln.Close()
    fmt.Println("mini-kafka listening on :9092")

    for {
        conn, err := ln.Accept()
        if err != nil {
            continue
        }
        go handleConn(conn)
    }
}
