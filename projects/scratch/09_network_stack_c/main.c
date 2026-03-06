#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t dst[6];
    uint8_t src[6];
    uint16_t ethertype;
} EthHdr;

typedef struct {
    uint8_t ver_ihl;
    uint8_t tos;
    uint16_t total_len;
    uint16_t id;
    uint16_t frag;
    uint8_t ttl;
    uint8_t proto;
    uint16_t checksum;
    uint32_t src;
    uint32_t dst;
} IPv4Hdr;

typedef struct {
    uint8_t type;
    uint8_t code;
    uint16_t checksum;
    uint16_t id;
    uint16_t seq;
} IcmpHdr;

static uint16_t csum(const uint8_t *buf, size_t len) {
    uint32_t sum = 0;
    for (size_t i = 0; i + 1 < len; i += 2) sum += (buf[i] << 8) | buf[i + 1];
    if (len & 1) sum += buf[len - 1] << 8;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (uint16_t)~sum;
}

int main(void) {
    uint8_t pkt[64] = {0};

    EthHdr *e = (EthHdr *)pkt;
    memset(e->dst, 0xaa, 6);
    memset(e->src, 0xbb, 6);
    e->ethertype = htons(0x0800);

    IPv4Hdr *ip = (IPv4Hdr *)(pkt + sizeof(EthHdr));
    ip->ver_ihl = 0x45;
    ip->total_len = htons(sizeof(IPv4Hdr) + sizeof(IcmpHdr));
    ip->ttl = 64;
    ip->proto = 1;
    ip->src = htonl(0x0a000001);
    ip->dst = htonl(0x0a000002);
    ip->checksum = 0;
    ip->checksum = csum((const uint8_t *)ip, sizeof(IPv4Hdr));

    IcmpHdr *icmp = (IcmpHdr *)(pkt + sizeof(EthHdr) + sizeof(IPv4Hdr));
    icmp->type = 8;
    icmp->code = 0;
    icmp->id = htons(1);
    icmp->seq = htons(1);
    icmp->checksum = 0;
    icmp->checksum = csum((const uint8_t *)icmp, sizeof(IcmpHdr));

    printf("EtherType=0x%04x IP.proto=%u ICMP.type=%u\n", ntohs(e->ethertype), ip->proto, icmp->type);

    uint32_t tmp = ip->src;
    ip->src = ip->dst;
    ip->dst = tmp;
    memcpy(e->dst, e->src, 6);
    memset(e->src, 0xcc, 6);
    icmp->type = 0;
    icmp->checksum = 0;
    icmp->checksum = csum((const uint8_t *)icmp, sizeof(IcmpHdr));
    ip->checksum = 0;
    ip->checksum = csum((const uint8_t *)ip, sizeof(IPv4Hdr));

    puts("ICMP echo reply crafted");
    return 0;
}
