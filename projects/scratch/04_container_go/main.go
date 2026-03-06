package main

import (
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "syscall"
)

func must(err error) {
    if err != nil {
        panic(err)
    }
}

func write(path, value string) {
    _ = os.MkdirAll(filepath.Dir(path), 0o755)
    must(os.WriteFile(path, []byte(value), 0o644))
}

func applyCgroup(name string, memoryBytes int, cpuQuota int) {
    base := "/sys/fs/cgroup"
    grp := filepath.Join(base, name)
    _ = os.MkdirAll(grp, 0o755)
    write(filepath.Join(grp, "memory.max"), fmt.Sprintf("%d", memoryBytes))
    write(filepath.Join(grp, "cpu.max"), fmt.Sprintf("%d 100000", cpuQuota))
    write(filepath.Join(grp, "cgroup.procs"), fmt.Sprintf("%d", os.Getpid()))
}

func run() {
    if len(os.Args) < 4 {
        fmt.Println("usage: run <rootfs> <cmd> [args...]")
        os.Exit(1)
    }
    rootfs := os.Args[2]
    cmd := os.Args[3]
    args := os.Args[4:]

    c := exec.Command("/proc/self/exe", append([]string{"init", rootfs, cmd}, args...)...)
    c.Stdin = os.Stdin
    c.Stdout = os.Stdout
    c.Stderr = os.Stderr
    c.SysProcAttr = &syscall.SysProcAttr{
        Cloneflags: syscall.CLONE_NEWUTS | syscall.CLONE_NEWPID | syscall.CLONE_NEWNS | syscall.CLONE_NEWNET,
    }
    must(c.Run())
}

func initContainer() {
    if len(os.Args) < 5 {
        os.Exit(1)
    }
    rootfs := os.Args[2]
    cmd := os.Args[3]
    args := os.Args[4:]

    applyCgroup("mini-container", 256*1024*1024, 50000)
    must(syscall.Sethostname([]byte("mini-container")))
    must(syscall.Chroot(rootfs))
    must(os.Chdir("/"))
    must(syscall.Mount("proc", "/proc", "proc", 0, ""))
    defer syscall.Unmount("/proc", 0)
    must(syscall.Exec(cmd, append([]string{cmd}, args...), os.Environ()))
}

func main() {
    if len(os.Args) < 2 {
        fmt.Println("usage: run <rootfs> <cmd> [args...]")
        return
    }
    switch os.Args[1] {
    case "run":
        run()
    case "init":
        initContainer()
    default:
        fmt.Println("unknown command")
    }
}
