/*
 * nonce_bruteforce.c — the textbook baseline for lukehutch/SAT-benchmarks
 * sha256-64r-nonce-scaling: try every value of the k unknown low bits of W[0]
 * and run the full 64-round FIPS 180-4 compression (with feed-forward) on each,
 * until the digest matches. No SAT, no circuit, no clever tricks.
 *
 * The instance is rebuilt exactly as src/main.rs builds it:
 *   blk = pad_single_block("SAT-Benchmarks-SHA256-64R-Nonce-Scaling-v1"); blk[0] = 0x9E3779B9;
 *   target = compress(blk); unknowns = bits 0..k-1 of blk[0].
 * Candidates are tried in plain ascending order from 0, so for k = 32 the hit is
 * at 0x9E3779B9 / 2^32 = 0.618 of the space (the benchmark's sweep reaches it at 0.616).
 *
 * Two engines: portable C, and the ARMv8 SHA-256 instructions (one core, one lane).
 * Build:  clang -O3 -mcpu=native -o nonce_bruteforce nonce_bruteforce.c
 * Usage:  ./nonce_bruteforce K [c|hw]
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#if defined(__ARM_FEATURE_SHA2) || defined(__aarch64__)
#include <arm_neon.h>
#define HAVE_ARM_SHA 1
#endif

static const uint32_t K256[64] = {
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                               0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

#define ROR(x,n) (((x)>>(n))|((x)<<(32-(n))))

static void compress_c(const uint32_t blk[16], uint32_t out[8]) {
    uint32_t w[64];
    memcpy(w, blk, 64);
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROR(w[i-15],7) ^ ROR(w[i-15],18) ^ (w[i-15]>>3);
        uint32_t s1 = ROR(w[i-2],17) ^ ROR(w[i-2],19) ^ (w[i-2]>>10);
        w[i] = w[i-16] + s0 + w[i-7] + s1;
    }
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h + (ROR(e,6)^ROR(e,11)^ROR(e,25)) + ((e&f)^(~e&g)) + K256[i] + w[i];
        uint32_t t2 = (ROR(a,2)^ROR(a,13)^ROR(a,22)) + ((a&b)^(a&c)^(b&c));
        h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    out[0]=a+IV[0]; out[1]=b+IV[1]; out[2]=c+IV[2]; out[3]=d+IV[3];
    out[4]=e+IV[4]; out[5]=f+IV[5]; out[6]=g+IV[6]; out[7]=h+IV[7];
}

#ifdef HAVE_ARM_SHA
__attribute__((target("sha2")))
static void compress_hw(const uint32_t blk[16], uint32_t out[8]) {
    uint32x4_t s0 = vld1q_u32(IV), s1 = vld1q_u32(IV+4);
    uint32x4_t m0 = vld1q_u32(blk), m1 = vld1q_u32(blk+4),
               m2 = vld1q_u32(blk+8), m3 = vld1q_u32(blk+12);
    uint32x4_t a0 = s0, a1 = s1, t, tmp;
    for (int i = 0; i < 16; i++) {
        t = vaddq_u32(m0, vld1q_u32(K256 + 4*i));
        tmp = a0;
        a0 = vsha256hq_u32(a0, a1, t);
        a1 = vsha256h2q_u32(a1, tmp, t);
        if (i < 12) {
            uint32x4_t n = vsha256su1q_u32(vsha256su0q_u32(m0, m1), m2, m3);
            m0 = m1; m1 = m2; m2 = m3; m3 = n;
        } else { m0 = m1; m1 = m2; m2 = m3; }
    }
    vst1q_u32(out, vaddq_u32(a0, s0));
    vst1q_u32(out+4, vaddq_u32(a1, s1));
}
#endif

static void pad_single_block(const char *msg, uint32_t blk[16]) {
    uint8_t b[64] = {0};
    size_t n = strlen(msg);
    memcpy(b, msg, n);
    b[n] = 0x80;
    uint64_t bits = (uint64_t)n * 8;
    for (int i = 0; i < 8; i++) b[63-i] = (uint8_t)(bits >> (8*i));
    for (int i = 0; i < 16; i++)
        blk[i] = (uint32_t)b[4*i]<<24 | (uint32_t)b[4*i+1]<<16 | (uint32_t)b[4*i+2]<<8 | b[4*i+3];
}

int main(int argc, char **argv) {
    int k = argc > 1 ? atoi(argv[1]) : 32;
    int hw = argc > 2 && strcmp(argv[2], "hw") == 0;
    if (k < 1 || k > 32) { fprintf(stderr, "K must be 1..32\n"); return 2; }
    void (*compress)(const uint32_t*, uint32_t*) = compress_c;
#ifdef HAVE_ARM_SHA
    if (hw) compress = compress_hw;
#endif
    uint32_t blk[16], target[8], out[8];
    pad_single_block("SAT-Benchmarks-SHA256-64R-Nonce-Scaling-v1", blk);
    blk[0] = 0x9E3779B9u;
    compress_c(blk, target);              /* the instance's target digest */
    printf("target ");
    for (int i = 0; i < 8; i++) printf("%08x", target[i]);
    printf("\n");
    uint32_t mask = k == 32 ? 0xFFFFFFFFu : ((1u << k) - 1);
    uint32_t high = blk[0] & ~mask;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t tried = 0, found = 0, nonce = 0;
    for (uint64_t x = 0; x <= mask; x++) {
        blk[0] = high | (uint32_t)x;
        compress(blk, out);
        tried++;
        if (out[0] == target[0] && memcmp(out, target, 32) == 0) { found = 1; nonce = blk[0]; break; }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double s = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("k=%d engine=%s %s nonce=0x%08llx tried=%llu time=%.3fs rate=%.1fM/s\n",
           k, hw ? "armv8-sha2" : "portable-c", found ? "SAT" : "NOTFOUND",
           (unsigned long long)nonce, (unsigned long long)tried, s, tried / s / 1e6);
    if (found) {                           /* independent check of the witness */
        uint32_t chk[8]; compress_c(blk, chk);
        if (memcmp(chk, target, 32) != 0) { puts("VERIFY FAILED"); return 1; }
    }
    return found ? 0 : 1;
}
