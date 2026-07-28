/*
 * Compact Keccak-256 (Ethereum variant: no SHA3 domain separation).
 * Public domain style implementation adapted for embedded reuse.
 */
#include "keccak256.h"

#include <string.h>

#define KECCAK_ROUNDS 24

static const uint64_t keccakf_rndc[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL, 0x800000000000808aULL,
    0x8000000080008000ULL, 0x000000000000808bULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL, 0x000000000000008aULL,
    0x0000000000000088ULL, 0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL, 0x8000000000008089ULL,
    0x8000000000008003ULL, 0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800aULL, 0x800000008000000aULL, 0x8000000080008081ULL,
    0x8000000000008080ULL, 0x0000000080000001ULL, 0x8000000080008008ULL};

static const int keccakf_rotc[24] = {1,  3,  6,  10, 15, 21, 28, 36, 45, 55, 2,  14,
                                    27, 41, 56, 8,  25, 43, 62, 18, 39, 61, 20, 44};

static const int keccakf_piln[24] = {10, 7,  11, 17, 18, 3, 5,  16, 8,  21, 24, 4,
                                    15, 23, 19, 13, 12, 2, 20, 14, 22, 9,  6,  1};

static uint64_t rotl64(uint64_t x, int y) { return (x << y) | (x >> (64 - y)); }

static void keccakf(uint64_t st[25]) {
    int i, j, round;
    uint64_t t, bc[5];

    for (round = 0; round < KECCAK_ROUNDS; round++) {
        for (i = 0; i < 5; i++) {
            bc[i] = st[i] ^ st[i + 5] ^ st[i + 10] ^ st[i + 15] ^ st[i + 20];
        }
        for (i = 0; i < 5; i++) {
            t = bc[(i + 4) % 5] ^ rotl64(bc[(i + 1) % 5], 1);
            for (j = 0; j < 25; j += 5) {
                st[j + i] ^= t;
            }
        }
        t = st[1];
        for (i = 0; i < 24; i++) {
            j = keccakf_piln[i];
            bc[0] = st[j];
            st[j] = rotl64(t, keccakf_rotc[i]);
            t = bc[0];
        }
        for (j = 0; j < 25; j += 5) {
            for (i = 0; i < 5; i++) {
                bc[i] = st[j + i];
            }
            for (i = 0; i < 5; i++) {
                st[j + i] ^= (~bc[(i + 1) % 5]) & bc[(i + 2) % 5];
            }
        }
        st[0] ^= keccakf_rndc[round];
    }
}

void airgap_keccak256(const uint8_t *data, size_t len, uint8_t out[32]) {
    uint64_t st[25];
    uint8_t temp[144];
    size_t i, rsiz = 136; /* rate for 256-bit output */
    size_t rsizw = rsiz / 8;

    memset(st, 0, sizeof(st));

    for (; len >= rsiz; len -= rsiz, data += rsiz) {
        for (i = 0; i < rsizw; i++) {
            uint64_t t;
            memcpy(&t, data + i * 8, 8);
            st[i] ^= t;
        }
        keccakf(st);
    }

    memset(temp, 0, rsiz);
    memcpy(temp, data, len);
    temp[len++] = 0x01; /* Keccak pad (Ethereum), not SHA3 0x06 */
    temp[rsiz - 1] |= 0x80;

    for (i = 0; i < rsizw; i++) {
        uint64_t t;
        memcpy(&t, temp + i * 8, 8);
        st[i] ^= t;
    }
    keccakf(st);

    memcpy(out, st, 32);
}
