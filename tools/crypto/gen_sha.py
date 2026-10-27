# Generates std/crypto/sha256.sten and sha512.sten. The round constants are the
# fractional parts of the cube roots (K) and square roots (H) of the first
# primes, computed exactly with integer roots, then checked against hashlib by
# the generated tests.
import sys
out = sys.argv[1]

def primes(n):
    ps, c = [], 2
    while len(ps) < n:
        if all(c % p for p in ps): ps.append(c)
        c += 1
    return ps

def icbrt(n):
    x = 1 << ((n.bit_length() + 2) // 3)
    while True:
        y = (2 * x + n // (x * x)) // 3
        if y >= x: break
        x = y
    while x ** 3 > n: x -= 1
    while (x + 1) ** 3 <= n: x += 1
    return x

import math
def frac_cbrt(p, bits): return icbrt(p << (3 * bits)) & ((1 << bits) - 1)
def frac_sqrt(p, bits): return math.isqrt(p << (2 * bits)) & ((1 << bits) - 1)

def hexlit(v, bits):
    s = format(v, '0%dx' % (bits // 4))
    return "0x" + "_".join(s[i:i+8] for i in range(0, len(s), 8))

def table(name, vals, bits, ty):
    lines = [f"func {name}() -> List[{ty}] {{", f"    List[{ty}] t = list_new()"]
    for v in vals:
        lines.append(f"    t.push({hexlit(v, bits)})")
    lines += ["    return t", "}"]
    return "\n".join(lines)

def gen(bits):
    ty = "uint32" if bits == 32 else "uint64"
    nrounds = 64 if bits == 32 else 80
    block = 64 if bits == 32 else 128
    lenbytes = 8 if bits == 32 else 16
    wb = bits // 8
    name = "sha256" if bits == 32 else "sha512"
    if bits == 32:
        S0, S1, s0, s1 = (2, 13, 22), (6, 11, 25), (7, 18, 3), (17, 19, 10)
    else:
        S0, S1, s0, s1 = (28, 34, 39), (14, 18, 41), (1, 8, 7), (19, 61, 6)
    K = [frac_cbrt(p, bits) for p in primes(nrounds)]
    H = [frac_sqrt(p, bits) for p in primes(8)]
    src = f'''// Stenopos standard library — {name.upper()} (FIPS 180-4).
// Pure Stenopos, no FFI. A byte buffer is a List[int32] of values 0..255 (as in
// std.bytes). The constants are the fractional parts of the cube roots (K) and
// square roots (H0) of the first primes; tests check digests against FIPS 180
// vectors. Not constant-time with respect to the message length, which is
// public; the data itself only flows through fixed-time operations.

module std.crypto.{name}

{table("round_constants", K, bits, ty)}

{table("initial_hash", H, bits, ty)}

func rotr({ty} x, {ty} n) -> {ty} {{
    return (x >> n) | (x << ({bits} - n))
}}

// The message padded to a whole number of {block}-byte blocks: a 0x80 byte,
// zeros, then the length in bits as a {lenbytes * 8}-bit big-endian integer.
func pad(List[int32] msg) -> List[int32] {{
    List[int32] out = list_new()
    for (b in msg) {{
        out.push(b & 255)
    }}
    out.push(128)
    while (out.len() % {block} != {block - lenbytes}) {{
        out.push(0)
    }}
    uint64 nbits = wrapping_mul(cast[uint64](msg.len()), 8)
    int32 z = 0
    while (z < {lenbytes - 8}) {{
        out.push(0)
        z = z + 1
    }}
    int32 sh = 56
    while (sh >= 0) {{
        out.push(cast[int32]((nbits >> cast[uint64](sh)) & 255))
        sh = sh - 8
    }}
    return out
}}

// Word `j` of the padded message, big-endian.
func word_at(List[int32] p, int64 j) -> {ty} {{
    {ty} w = 0
    int64 k = 0
    while (k < {wb}) {{
        w = (w << 8) | cast[{ty}](p.get(j * {wb} + k))
        k = k + 1
    }}
    return w
}}

// The {name.upper()} digest of `msg`: {bits // 4} bytes.
pub func {name}(List[int32] msg) -> List[int32] {{
    List[{ty}] kk = round_constants()
    List[{ty}] h = initial_hash()
    List[int32] p = pad(msg)
    int64 nblocks = p.len() / {block}
    int64 blk = 0
    while (blk < nblocks) {{
        List[{ty}] w = list_new()
        int64 t = 0
        while (t < 16) {{
            w.push(word_at(p, blk * 16 + t))
            t = t + 1
        }}
        while (t < {nrounds}) {{
            {ty} w15 = w.get(t - 15)
            {ty} w2 = w.get(t - 2)
            {ty} sg0 = rotr(w15, {s0[0]}) ^ rotr(w15, {s0[1]}) ^ (w15 >> {s0[2]})
            {ty} sg1 = rotr(w2, {s1[0]}) ^ rotr(w2, {s1[1]}) ^ (w2 >> {s1[2]})
            w.push(wrapping_add(wrapping_add(sg1, w.get(t - 7)), wrapping_add(sg0, w.get(t - 16))))
            t = t + 1
        }}
        {ty} a = h.get(0)
        {ty} b = h.get(1)
        {ty} c = h.get(2)
        {ty} d = h.get(3)
        {ty} e = h.get(4)
        {ty} f = h.get(5)
        {ty} g = h.get(6)
        {ty} hh = h.get(7)
        t = 0
        while (t < {nrounds}) {{
            {ty} bs1 = rotr(e, {S1[0]}) ^ rotr(e, {S1[1]}) ^ rotr(e, {S1[2]})
            {ty} ch = (e & f) ^ (~e & g)
            {ty} t1 = wrapping_add(wrapping_add(wrapping_add(hh, bs1), wrapping_add(ch, kk.get(t))), w.get(t))
            {ty} bs0 = rotr(a, {S0[0]}) ^ rotr(a, {S0[1]}) ^ rotr(a, {S0[2]})
            {ty} maj = (a & b) ^ (a & c) ^ (b & c)
            {ty} t2 = wrapping_add(bs0, maj)
            hh = g
            g = f
            f = e
            e = wrapping_add(d, t1)
            d = c
            c = b
            b = a
            a = wrapping_add(t1, t2)
            t = t + 1
        }}
        h.set(0, wrapping_add(h.get(0), a))
        h.set(1, wrapping_add(h.get(1), b))
        h.set(2, wrapping_add(h.get(2), c))
        h.set(3, wrapping_add(h.get(3), d))
        h.set(4, wrapping_add(h.get(4), e))
        h.set(5, wrapping_add(h.get(5), f))
        h.set(6, wrapping_add(h.get(6), g))
        h.set(7, wrapping_add(h.get(7), hh))
        blk = blk + 1
    }}
    List[int32] out = list_new()
    for (v in h) {{
        int32 sh = {bits - 8}
        while (sh >= 0) {{
            out.push(cast[int32]((v >> cast[{ty}](sh)) & 255))
            sh = sh - 8
        }}
    }}
    return out
}}

// The digest of a string's bytes.
pub func {name}_str(str s) -> List[int32] {{
    List[int32] b = list_new()
    int64 i = 0
    while (i < s.len()) {{
        b.push(s.byte_at(i))
        i = i + 1
    }}
    return {name}(b)
}}
'''
    open(f"{out}/{name}.sten", "w").write(src)

gen(32); gen(64)
