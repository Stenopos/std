# Reference model of the Stenopos ed25519 verifier: TweetNaCl's structure
# (16 limbs of 16 bits, extended coordinates), constants derived from the
# curve, plus RFC 8032's S < L check. Used to validate the algorithm and to
# print the constants for the Stenopos port.
import hashlib
P = 2**255 - 19
Lq = 2**252 + 27742317777372353535851937790883648493
def inv(x): return pow(x, P - 2, P)
d = (-121665 * inv(121666)) % P
I_ = pow(2, (P - 1) // 4, P)
By = 4 * inv(5) % P
xx = (By * By - 1) * inv(d * By * By + 1) % P
Bx = pow(xx, (P + 3) // 8, P)
if (Bx * Bx - xx) % P: Bx = Bx * I_ % P
if Bx & 1: Bx = P - Bx
def limbs(v): return [(v >> (16 * i)) & 0xffff for i in range(16)]
C = {"D": limbs(d), "D2": limbs(2 * d % P), "X": limbs(Bx), "Y": limbs(By), "I": limbs(I_)}
Lb = [(Lq >> (8 * i)) & 0xff for i in range(32)]
gf0 = [0] * 16; gf1 = [1] + [0] * 15

def car(o):
    o = o[:]
    for i in range(16):
        o[i] += 1 << 16
        c = o[i] >> 16
        if i < 15: o[i + 1] += c - 1
        else: o[0] += 38 * (c - 1)
        o[i] -= c << 16
    return o
def A(a, b): return [a[i] + b[i] for i in range(16)]
def Z(a, b): return [a[i] - b[i] for i in range(16)]
def M(a, b):
    t = [0] * 31
    for i in range(16):
        for j in range(16): t[i + j] += a[i] * b[j]
    for i in range(15): t[i] += 38 * t[i + 16]
    return car(car(t[:16]))
def S(a): return M(a, a)
def inv25519(i):
    c = i[:]
    for a in range(253, -1, -1):
        c = S(c)
        if a != 2 and a != 4: c = M(c, i)
    return c
def pow2523(i):
    c = i[:]
    for a in range(250, -1, -1):
        c = S(c)
        if a != 1: c = M(c, i)
    return c
def pack25519(n):
    t = car(car(car(n)))
    for _ in range(2):
        m = [0] * 16
        m[0] = t[0] - 0xffed
        for i in range(1, 15):
            m[i] = t[i] - 0xffff - ((m[i - 1] >> 16) & 1)
            m[i - 1] &= 0xffff
        m[15] = t[15] - 0x7fff - ((m[14] >> 16) & 1)
        b = (m[15] >> 16) & 1
        m[14] &= 0xffff
        if b == 0: t = m
    out = []
    for i in range(16): out += [t[i] & 0xff, t[i] >> 8]
    return out
def neq(a, b): return pack25519(a) != pack25519(b)
def par(a): return pack25519(a)[0] & 1
def unpack25519(n):
    o = [n[2 * i] + (n[2 * i + 1] << 8) for i in range(16)]
    o[15] &= 0x7fff
    return o
def add(p, q):
    a = M(Z(p[1], p[0]), Z(q[1], q[0]))
    b = M(A(p[0], p[1]), A(q[0], q[1]))
    c = M(M(p[3], q[3]), C["D2"])
    dd = M(p[2], q[2]); dd = A(dd, dd)
    e = Z(b, a); f = Z(dd, c); g = A(dd, c); h = A(b, a)
    return [M(e, f), M(h, g), M(g, f), M(e, h)]
def pack(p):
    zi = inv25519(p[2])
    tx = M(p[0], zi); ty = M(p[1], zi)
    r = pack25519(ty); r[31] ^= par(tx) << 7
    return r
def scalarmult(q, s):
    p = [gf0, gf1, gf1, gf0]
    for i in range(255, -1, -1):
        if (s[i // 8] >> (i & 7)) & 1:
            p = add(p, q)                 # add then double, as cswap/add/add/cswap does
            q = add(q, q)
        else:
            q = add(q, p)
            p = add(p, p)
    return p
def scalarbase(s): return scalarmult([C["X"], C["Y"], gf1, M(C["X"], C["Y"])], s)
def modL(x):
    x = x[:]
    for i in range(63, 31, -1):
        carry = 0
        j = i - 32
        while j < i - 12:
            x[j] += carry - 16 * x[i] * Lb[j - (i - 32)]
            carry = (x[j] + 128) >> 8
            x[j] -= carry << 8
            j += 1
        x[j] += carry
        x[i] = 0
    carry = 0
    for j in range(32):
        x[j] += carry - (x[31] >> 4) * Lb[j]
        carry = x[j] >> 8
        x[j] &= 255
    for j in range(32): x[j] -= carry * Lb[j]
    r = [0] * 32
    for i in range(32):
        x[i + 1] += x[i] >> 8
        r[i] = x[i] & 255
    return r
def unpackneg(p):
    r2 = gf1[:]
    r1 = unpack25519(p)
    num = S(r1); den = M(num, C["D"]); num = Z(num, r2); den = A(r2, den)
    den2 = S(den); den4 = S(den2); den6 = M(den4, den2)
    t = M(M(den6, num), den)
    t = pow2523(t)
    t = M(M(M(t, num), den), den)
    r0 = M(t, den)
    chk = M(S(r0), den)
    if neq(chk, num): r0 = M(r0, C["I"])
    chk = M(S(r0), den)
    if neq(chk, num): return None
    if par(r0) == (p[31] >> 7): r0 = Z(gf0, r0)
    return [r0, r1, r2, M(r0, r1)]
def s_lt_L(s):
    for i in range(31, -1, -1):
        if s[i] < Lb[i]: return True
        if s[i] > Lb[i]: return False
    return False
def verify(pk, msg, sig):
    if len(pk) != 32 or len(sig) != 64: return False
    if not s_lt_L(sig[32:]): return False
    q = unpackneg(pk)
    if q is None: return False
    h = modL(list(hashlib.sha512(bytes(sig[:32]) + bytes(pk) + bytes(msg)).digest()) + [0] * 0)
    p = scalarmult(q, h)
    p = add(p, scalarbase(sig[32:]))
    return pack(p) == list(sig[:32])

if __name__ == "__main__":
    import sys
    for k, v in C.items(): print(k, [hex(x) for x in v])
    print("L", Lb)
