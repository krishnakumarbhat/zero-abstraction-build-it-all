package main

import (
    "crypto/sha1"
    "encoding/binary"
    "fmt"
    "io"
    "net"
    "net/http"
    "net/url"
    "os"
    "strconv"
)

type parser struct {
    data []byte
    i    int
}

func (p *parser) peek() byte { return p.data[p.i] }

func (p *parser) parse() (any, error) {
    switch p.peek() {
    case 'i':
        p.i++
        start := p.i
        for p.data[p.i] != 'e' {
            p.i++
        }
        val, err := strconv.ParseInt(string(p.data[start:p.i]), 10, 64)
        if err != nil {
            return nil, err
        }
        p.i++
        return val, nil
    case 'l':
        p.i++
        var out []any
        for p.data[p.i] != 'e' {
            v, err := p.parse()
            if err != nil {
                return nil, err
            }
            out = append(out, v)
        }
        p.i++
        return out, nil
    case 'd':
        p.i++
        out := map[string]any{}
        for p.data[p.i] != 'e' {
            k, err := p.parse()
            if err != nil {
                return nil, err
            }
            v, err := p.parse()
            if err != nil {
                return nil, err
            }
            out[string(k.([]byte))] = v
        }
        p.i++
        return out, nil
    default:
        start := p.i
        for p.data[p.i] != ':' {
            p.i++
        }
        l, err := strconv.Atoi(string(p.data[start:p.i]))
        if err != nil {
            return nil, err
        }
        p.i++
        s := p.data[p.i : p.i+l]
        p.i += l
        return s, nil
    }
}

func decodeBencode(b []byte) (any, error) {
    p := &parser{data: b}
    return p.parse()
}

func extractInfoHash(meta map[string]any) ([]byte, error) {
    info, ok := meta["info"].(map[string]any)
    if !ok {
        return nil, fmt.Errorf("missing info dict")
    }
    name := string(info["name"].([]byte))
    length := info["length"].(int64)
    pieceLength := info["piece length"].(int64)
    payload := []byte(fmt.Sprintf("%s:%d:%d", name, length, pieceLength))
    h := sha1.Sum(payload)
    return h[:], nil
}

func parseTorrent(path string) (map[string]any, error) {
    b, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    v, err := decodeBencode(b)
    if err != nil {
        return nil, err
    }
    d, ok := v.(map[string]any)
    if !ok {
        return nil, fmt.Errorf("invalid torrent root")
    }
    return d, nil
}

func trackerPeers(meta map[string]any) ([]string, error) {
    announce := string(meta["announce"].([]byte))
    infoHash, err := extractInfoHash(meta)
    if err != nil {
        return nil, err
    }
    info := meta["info"].(map[string]any)
    left := info["length"].(int64)

    q := url.Values{}
    q.Set("peer_id", "-ZA0001-123456789012")
    q.Set("port", "6881")
    q.Set("uploaded", "0")
    q.Set("downloaded", "0")
    q.Set("left", fmt.Sprintf("%d", left))
    q.Set("compact", "1")

    u, err := url.Parse(announce)
    if err != nil {
        return nil, err
    }
    u.RawQuery = q.Encode()
    req, _ := http.NewRequest("GET", u.String(), nil)
    req.URL.RawQuery += "&info_hash=" + string(infoHash)

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    body, _ := io.ReadAll(resp.Body)

    v, err := decodeBencode(body)
    if err != nil {
        return nil, err
    }
    d := v.(map[string]any)
    compact, ok := d["peers"].([]byte)
    if !ok {
        return nil, fmt.Errorf("tracker did not return compact peers")
    }

    peers := []string{}
    for i := 0; i+6 <= len(compact); i += 6 {
        ip := net.IPv4(compact[i], compact[i+1], compact[i+2], compact[i+3]).String()
        port := binary.BigEndian.Uint16(compact[i+4 : i+6])
        peers = append(peers, fmt.Sprintf("%s:%d", ip, port))
    }
    return peers, nil
}

func main() {
    if len(os.Args) != 3 {
        fmt.Println("usage: go run . <parse|peers> <torrent-file>")
        os.Exit(1)
    }

    cmd := os.Args[1]
    path := os.Args[2]

    meta, err := parseTorrent(path)
    if err != nil {
        panic(err)
    }

    info := meta["info"].(map[string]any)
    switch cmd {
    case "parse":
        fmt.Println("announce:", string(meta["announce"].([]byte)))
        fmt.Println("name:", string(info["name"].([]byte)))
        fmt.Println("length:", info["length"].(int64))
        fmt.Println("piece length:", info["piece length"].(int64))
    case "peers":
        peers, err := trackerPeers(meta)
        if err != nil {
            panic(err)
        }
        for _, p := range peers {
            fmt.Println(p)
        }
    default:
        fmt.Println("unknown command")
    }
}
