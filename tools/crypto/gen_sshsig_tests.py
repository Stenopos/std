# Generates std/crypto/test_sshsig.sten from real `ssh-keygen -Y sign` output
# (OpenSSH, an independent implementation), plus invalid cases derived from it.
import subprocess, sys, os, tempfile
out = sys.argv[1]
d = tempfile.mkdtemp()
def keygen(name):
    k = os.path.join(d, name)
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", k], check=True)
    return k, open(k + ".pub").read().strip()
def sign(key, ns, msg, alg="sha512"):
    m = os.path.join(d, "msg"); open(m, "wb").write(msg)
    if os.path.exists(m + ".sig"):
        os.remove(m + ".sig")              # ssh-keygen would otherwise keep the old one
    subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", key, "-n", ns, "-O", "hashalg=" + alg, m], check=True, capture_output=True, stdin=subprocess.DEVNULL)
    return open(m + ".sig").read()
k1, pub1 = keygen("registry-root")
k2, pub2 = keygen("someone-else")
msg = b'role = "online"\nexpires = "2027-10-27"\n'
s512 = sign(k1, "stenopos-registry", msg)
s256 = sign(k1, "stenopos-registry", msg, "sha256")
sempty = sign(k1, "stenopos-registry", b"")
other_ns = sign(k1, "file", msg)
by_k2 = sign(k2, "stenopos-registry", msg)
lines = s512.splitlines()
tampered = lines[:]; mid = tampered[3]; tampered[3] = mid[:10] + ("A" if mid[10] != "A" else "B") + mid[11:]
assert len({s512, s256, sempty, other_ns, by_k2}) == 5, "every signature must be distinct"
cases = [
    ("valid (sha512)", s512, msg, "stenopos-registry", pub1, True),
    ("valid (sha256)", s256, msg, "stenopos-registry", pub1, True),
    ("valid, empty message", sempty, b"", "stenopos-registry", pub1, True),
    ("wrong message", s512, msg + b" ", "stenopos-registry", pub1, False),
    ("signed in another namespace", other_ns, msg, "stenopos-registry", pub1, False),
    ("checked against another namespace", s512, msg, "file", pub1, False),
    ("signed by another key", by_k2, msg, "stenopos-registry", pub1, False),
    ("checked against another key", s512, msg, "stenopos-registry", pub2, False),
    ("tampered signature", "\n".join(tampered) + "\n", msg, "stenopos-registry", pub1, False),
    ("not base64", "-----BEGIN SSH SIGNATURE-----\n!!!!\n-----END SSH SIGNATURE-----\n", msg, "stenopos-registry", pub1, False),
    ("empty", "", msg, "stenopos-registry", pub1, False),
    ("bad allowed key", s512, msg, "stenopos-registry", "ssh-rsa AAAA", False),
]
def lit(s): return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("{", "\\{").replace("}", "\\}")
src = ['''// Tests for std.crypto.sshsig, from real `ssh-keygen -Y sign` signatures
// (OpenSSH, an independent implementation) and invalid cases derived from them.

module std.crypto.sshsig_tests

import std.crypto.sshsig.{sshsig_verify}
import std.hex.{hex_decode}

func check(str sig, str msg_hex, str ns, str key, bool want, str name) -> int32 {
    bool got = sshsig_verify(sig, hex_decode(msg_hex), ns, key)
    if (got == want) {
        println("  ok   {name}")
        return 0
    }
    println("  FAIL {name}: got {got}")
    return 1
}

func main() -> void {
    int32 fails = 0
    println("std.crypto sshsig tests:")''']
for name, sig, m, ns, key, want in cases:
    src.append(f'    fails += check("{lit(sig)}", "{m.hex()}", "{ns}", "{lit(key)}", {str(want).lower()}, "{name}")')
src.append('''    if (fails > 0) {
        fail("FAIL: {fails} check(s) failed")
    }
    println("PASS: all std.crypto sshsig checks passed")
}''')
open(f"{out}/test_sshsig.sten", "w").write("\n".join(src) + "\n")
# Confirm the valid cases with OpenSSH itself.
allowed = os.path.join(d, "allowed"); open(allowed, "w").write("registry-root " + pub1 + "\n")
m = os.path.join(d, "m"); open(m, "wb").write(msg); sf = os.path.join(d, "m.sig2"); open(sf, "w").write(s512)
r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", allowed, "-I", "registry-root", "-n", "stenopos-registry", "-s", sf], stdin=open(m, "rb"), capture_output=True)
print("openssh verifies the sha512 case:", r.returncode == 0)
