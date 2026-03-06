#define _GNU_SOURCE
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>

typedef struct Block {
    size_t size;
    int free;
    struct Block *next;
} Block;

static Block *head = NULL;
static void *arena = NULL;
static size_t arena_size = 1 << 20;

static void init_allocator(void) {
    if (arena) return;
    arena = mmap(NULL, arena_size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (arena == MAP_FAILED) {
        perror("mmap");
        return;
    }
    head = (Block *)arena;
    head->size = arena_size - sizeof(Block);
    head->free = 1;
    head->next = NULL;
}

static void split_block(Block *b, size_t size) {
    if (b->size <= size + sizeof(Block)) return;
    Block *newb = (Block *)((char *)(b + 1) + size);
    newb->size = b->size - size - sizeof(Block);
    newb->free = 1;
    newb->next = b->next;
    b->size = size;
    b->next = newb;
}

void *my_malloc(size_t size) {
    if (!size) return NULL;
    init_allocator();
    Block *cur = head;
    while (cur) {
        if (cur->free && cur->size >= size) {
            split_block(cur, size);
            cur->free = 0;
            return (void *)(cur + 1);
        }
        cur = cur->next;
    }
    return NULL;
}

static void coalesce(void) {
    Block *cur = head;
    while (cur && cur->next) {
        if (cur->free && cur->next->free) {
            cur->size += sizeof(Block) + cur->next->size;
            cur->next = cur->next->next;
        } else {
            cur = cur->next;
        }
    }
}

void my_free(void *ptr) {
    if (!ptr) return;
    Block *b = ((Block *)ptr) - 1;
    b->free = 1;
    coalesce();
}

int main(void) {
    char *a = (char *)my_malloc(64);
    char *b = (char *)my_malloc(128);
    if (!a || !b) return 1;
    strcpy(a, "hello allocator");
    strcpy(b, "second buffer");
    if (strcmp(a, "hello allocator") != 0) return 2;
    my_free(a);
    my_free(b);
    char *c = (char *)my_malloc(256);
    if (!c) return 3;
    strcpy(c, "coalesced");
    puts(c);
    return 0;
}
