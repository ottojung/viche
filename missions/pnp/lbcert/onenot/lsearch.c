// Live-set search for the one-NOT generator (onenot.py): is there a circuit of <= k binary gates
// (AND-type, NOTs free) equal to goal/~goal on the sampled rows?  Rows j < P are f = 1, row P + j
// is the f = 0 partner of row j; live words must separate every pair (the kernel search's pruning
// in the template of the merged L-meta-14150).  LSEARCH_PAIRS_ONLY=1 keeps exactly that pruning,
// so the state count is a proxy for the kernel's work (~2k states/s).  Memo by 64-bit hashes: a
// collision could only produce a false "none", which the Lean compile gate then rejects.
// build: cc -O2 -o lsearch lsearch.c
// stdin: n P k limit  then n words in hex.   stdout: none | found | limit   stderr: states=N
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXL 8
#define MAXS 20
typedef struct { uint64_t l[MAXL]; } W;
static int NL, P, NIN;
static W FULL, LOW, GOAL, NGOAL, ZERO;
static long long COUNT, LIMIT; static int FULLSEP = 1;

static int weq(const W *a, const W *b) { return memcmp(a, b, sizeof(W)) == 0; }
static W wand(W a, W b) { for (int i = 0; i < NL; i++) a.l[i] &= b.l[i]; return a; }
static W wor(W a, W b) { for (int i = 0; i < NL; i++) a.l[i] |= b.l[i]; return a; }
static W wnot(W a) { for (int i = 0; i < NL; i++) a.l[i] = ~a.l[i] & FULL.l[i]; return a; }
static W canon(W a) { return (a.l[0] & 1) ? wnot(a) : a; }
static int wcmp(const void *x, const void *y) { return memcmp(x, y, sizeof(W)); }
static int getbit(const W *a, int j) { return (a->l[j >> 6] >> (j & 63)) & 1; }

static int cut(W *S, int ns) {
    W c = ZERO;
    for (int t = 0; t < ns; t++) {
        W sh = ZERO;
        int q = P >> 6, r = P & 63;
        for (int i = 0; i < NL; i++) {
            uint64_t lo = (i + q < NL) ? S[t].l[i + q] : 0;
            uint64_t hi = (i + q + 1 < NL) ? S[t].l[i + q + 1] : 0;
            sh.l[i] = r ? ((lo >> r) | (hi << (64 - r))) : lo;
        }
        for (int i = 0; i < NL; i++) c.l[i] |= (S[t].l[i] ^ sh.l[i]);
    }
    for (int i = 0; i < NL; i++) if ((c.l[i] & LOW.l[i]) != LOW.l[i]) return 0;
    return 1;
}

// stronger pruning: every f = 1 row must differ from every f = 0 row on some live word
static uint32_t *STAMP; static uint32_t GEN = 0;
static int fullsep(W *S, int ns) {
    if (ns > 20) return 1;
    GEN++;
    for (int j = 0; j < P; j++) {
        uint32_t sig = 0;
        for (int t = 0; t < ns; t++) sig |= (uint32_t)getbit(&S[t], j) << t;
        STAMP[sig] = GEN;
    }
    for (int j = P; j < 2 * P; j++) {
        uint32_t sig = 0;
        for (int t = 0; t < ns; t++) sig |= (uint32_t)getbit(&S[t], j) << t;
        if (STAMP[sig] == GEN) return 0;
    }
    return 1;
}

static uint64_t *TAB; static uint64_t TMASK; static uint64_t TFILL;
static uint64_t mix(uint64_t h) { h ^= h >> 33; h *= 0xff51afd7ed558ccdULL; h ^= h >> 33; h *= 0xc4ceb9fe1a85ec53ULL; h ^= h >> 33; return h; }
static uint64_t keyof(W *S, int ns, int g) {
    W c[MAXS];
    for (int t = 0; t < ns; t++) c[t] = canon(S[t]);
    qsort(c, ns, sizeof(W), wcmp);
    uint64_t h = 0x9e3779b97f4a7c15ULL * (g + 1);
    for (int t = 0; t < ns; t++) for (int i = 0; i < NL; i++) h = mix(h ^ c[t].l[i]) + t;
    return h | 1;
}
static int seen(uint64_t k) {
    for (uint64_t i = k & TMASK;; i = (i + 1) & TMASK) { if (TAB[i] == k) return 1; if (!TAB[i]) return 0; }
}
static void add(uint64_t k) {
    if (TFILL > (TMASK / 4) * 3) return;
    for (uint64_t i = k & TMASK;; i = (i + 1) & TMASK) { if (TAB[i] == k) return; if (!TAB[i]) { TAB[i] = k; TFILL++; return; } }
}

static int rec(W *S, int ns, int g) {
    if (ns == 1 && (weq(&S[0], &GOAL) || weq(&S[0], &NGOAL))) return 1;
    if (g == 0 || ns - 1 > g) return 0;
    uint64_t key = keyof(S, ns, g);
    if (seen(key)) return 0;
    if (++COUNT > LIMIT) { puts("limit"); exit(0); }
    if (!cut(S, ns) || (FULLSEP && !fullsep(S, ns))) { add(key); return 0; }
    W cs[MAXS];
    for (int t = 0; t < ns; t++) cs[t] = canon(S[t]);
    for (int i = 0; i < ns; i++) for (int j = i + 1; j < ns; j++) {
        W a = S[i], b = S[j], na = wnot(a), nb = wnot(b);
        W rest[MAXS]; int nr = 0;
        for (int t = 0; t < ns; t++) if (t != i && t != j) rest[nr++] = S[t];
        W zs[4] = { wand(a, b), wor(a, b), wand(a, nb), wand(b, na) };
        for (int o = 0; o < 4; o++) {
            W z = zs[o], cz = canon(z);
            if (weq(&cz, &ZERO)) continue;
            int dup = 0;
            for (int t = 0; t < ns; t++) if (weq(&cz, &cs[t])) { dup = 1; break; }
            if (dup) continue;
            for (int keep = 0; keep < 4; keep++) {
                W T[MAXS]; int nt = 0;
                for (int t = 0; t < nr; t++) T[nt++] = rest[t];
                if (keep & 1) T[nt++] = a;
                if (keep & 2) T[nt++] = b;
                T[nt++] = z;
                if (nt - 1 > g - 1 || nt > MAXS) continue;
                if (rec(T, nt, g - 1)) return 1;
            }
        }
    }
    add(key);
    return 0;
}

static W parsehex(const char *s) {
    W w; memset(&w, 0, sizeof w);
    int len = strlen(s), bit = 0;
    for (int p = len - 1; p >= 0; p--) {
        char ch = s[p]; int v;
        if (ch >= '0' && ch <= '9') v = ch - '0'; else if (ch >= 'a' && ch <= 'f') v = ch - 'a' + 10;
        else if (ch >= 'A' && ch <= 'F') v = ch - 'A' + 10; else continue;
        for (int b = 0; b < 4; b++, bit++) if ((v >> b) & 1) w.l[bit >> 6] |= 1ULL << (bit & 63);
    }
    return w;
}

int main(void) {
    int k; char buf[4096];
    if (scanf("%d %d %d %lld", &NIN, &P, &k, &LIMIT) != 4) return 2;
    NL = (2 * P + 63) / 64;
    if (NL > MAXL) { puts("toolarge"); return 0; }
    memset(&FULL, 0, sizeof(W)); memset(&LOW, 0, sizeof(W)); memset(&ZERO, 0, sizeof(W));
    for (int j = 0; j < 2 * P; j++) FULL.l[j >> 6] |= 1ULL << (j & 63);
    for (int j = 0; j < P; j++) LOW.l[j >> 6] |= 1ULL << (j & 63);
    GOAL = LOW; NGOAL = wnot(LOW);
    W in[32];
    for (int i = 0; i < NIN; i++) { if (scanf("%4095s", buf) != 1) return 2; in[i] = parsehex(buf); }
    if (getenv("LSEARCH_PAIRS_ONLY")) FULLSEP = 0;
    STAMP = calloc(1u << 20, sizeof(uint32_t));
    TMASK = (1ULL << 26) - 1;
    TAB = calloc(TMASK + 1, sizeof(uint64_t));
    for (int mask = 1; mask < (1 << NIN); mask++) {
        W S[MAXS]; int ns = 0;
        for (int i = 0; i < NIN; i++) if ((mask >> i) & 1) S[ns++] = in[i];
        if (ns - 1 > k || !cut(S, ns)) continue;
        if (rec(S, ns, k)) { puts("found"); fprintf(stderr, "states=%lld\n", COUNT); return 0; }
    }
    puts("none");
    fprintf(stderr, "states=%lld\n", COUNT);
    return 0;
}
