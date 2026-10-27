# Generates std/crypto/test_ed25519.sten. Valid signatures come from OpenSSL,
# or (for the empty message, which OpenSSL 3.0 can't sign) from the
# cryptography package; invalid cases are derived from them and confirmed
# invalid by the Python reference model.
import subprocess, sys, os, tempfile
sys.path.insert(0, sys.argv[2])
import ref_ed25519 as r
out = sys.argv[1]
def sign(msg):
    if msg == b"":
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization as ser
        k = Ed25519PrivateKey.generate()
        pk = k.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw)
        return pk, k.sign(msg)
    d = tempfile.mkdtemp()
    k = os.path.join(d, "k.pem"); m = os.path.join(d, "m"); s = os.path.join(d, "s")
    subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", k], check=True, capture_output=True)
    open(m, "wb").write(msg)
    subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", k, "-rawin", "-in", m, "-out", s], check=True)
    pk = subprocess.run(["openssl", "pkey", "-in", k, "-pubout", "-outform", "DER"], check=True, capture_output=True).stdout[-32:]
    return pk, open(s, "rb").read()
cases = []   # (name, pk, msg, sig, expected)
msgs = [b"", b"\x72", b"hello", bytes(range(256)) * 4]
keys = []
for i, m in enumerate(msgs):
    pk, sig = sign(m)
    keys.append((pk, m, sig))
    cases.append((f"valid, {len(m)}-byte message", pk, m, sig, True))
pk, m, sig = keys[2]
cases.append(("wrong message", pk, b"hellp", sig, False))
cases.append(("wrong key", keys[1][0], m, sig, False))
t = bytearray(sig); t[3] ^= 0x10; cases.append(("tampered R", pk, m, bytes(t), False))
t = bytearray(sig); t[45] ^= 0x01; cases.append(("tampered S", pk, m, bytes(t), False))
s_int = int.from_bytes(sig[32:], "little") + r.Lq
t = sig[:32] + s_int.to_bytes(32, "little"); cases.append(("S + L (non-canonical S)", pk, m, t, False))
# A public key that is not a curve point.
for y in range(2, 1000):
    enc = list(y.to_bytes(32, "little"))
    if r.unpackneg(enc) is None:
        cases.append(("key not on the curve", bytes(enc), m, sig, False)); break
cases.append(("short signature", pk, m, sig[:63], False))
cases.append(("short key", pk[:31], m, sig, False))
for name, cpk, cm, cs, want in cases:
    assert r.verify(list(cpk), list(cm), list(cs)) == want, name
def hx(b): return b.hex()
lines = ['''// Tests for std.crypto.ed25519. Valid signatures were made by OpenSSL and by
// Python's cryptography package (independent implementations); each invalid
// case is derived from a valid one.

module std.crypto.ed25519_tests

import std.crypto.ed25519.{ed25519_verify}
import std.hex.{hex_decode}

func check(str pk, str msg, str sig, bool want, str name) -> int32 {
    bool got = ed25519_verify(hex_decode(pk), hex_decode(msg), hex_decode(sig))
    if (got == want) {
        println("  ok   {name}")
        return 0
    }
    println("  FAIL {name}: got {got}")
    return 1
}

func main() -> void {
    int32 fails = 0
    println("std.crypto ed25519 tests:")''']
for name, cpk, cm, cs, want in cases:
    lines.append(f'    fails += check("{hx(cpk)}", "{hx(cm)}", "{hx(cs)}", {str(want).lower()}, "{name}")')
lines.append('''    if (fails > 0) {
        fail("FAIL: {fails} check(s) failed")
    }
    println("PASS: all std.crypto ed25519 checks passed")
}''')
open(f"{out}/test_ed25519.sten", "w").write("\n".join(lines) + "\n")
print(len(cases), "cases")
