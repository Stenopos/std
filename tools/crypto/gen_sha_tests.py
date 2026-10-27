# Generates std/crypto/test_sha.sten: digests of messages around every padding
# boundary, with expected values from Python's hashlib (an independent
# implementation), plus the FIPS 180 "abc" vectors written out by hand.
import hashlib, sys
out = sys.argv[1]
def msg(n):  # a deterministic message of n bytes covering all byte values
    return bytes((i * 31 + 7) % 256 for i in range(n))
lens = [0, 1, 3, 55, 56, 57, 63, 64, 65, 111, 112, 113, 127, 128, 129, 200, 1000]
lines = ['''// Tests for std.crypto.sha256 and std.crypto.sha512. Expected digests come
// from an independent implementation (Python's hashlib), for messages on both
// sides of every padding boundary; the "abc" vectors are FIPS 180-4's.

module std.crypto.sha_tests

import std.crypto.sha256.{sha256, sha256_str}
import std.crypto.sha512.{sha512, sha512_str}
import std.hex.{hex_encode}

func expect_hex(List[int32] got, str want, str name) -> int32 {
    str g = hex_encode(got)
    if (g == want) {
        println("  ok   {name}")
        return 0
    }
    println("  FAIL {name}: got {g}")
    return 1
}

// The test message of `n` bytes: byte i is (i * 31 + 7) % 256.
func msg(int32 n) -> List[int32] {
    List[int32] b = list_new()
    int32 i = 0
    while (i < n) {
        b.push((i * 31 + 7) % 256)
        i = i + 1
    }
    return b
}

func main() -> void {
    int32 fails = 0
    println("std.crypto sha tests:")
    fails += expect_hex(sha256_str("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "sha256 abc (FIPS 180-4)")
    fails += expect_hex(sha512_str("abc"), "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f", "sha512 abc (FIPS 180-4)")''']
for n in lens:
    lines.append(f'    fails += expect_hex(sha256(msg({n})), "{hashlib.sha256(msg(n)).hexdigest()}", "sha256 {n} bytes")')
    lines.append(f'    fails += expect_hex(sha512(msg({n})), "{hashlib.sha512(msg(n)).hexdigest()}", "sha512 {n} bytes")')
lines.append('''    if (fails > 0) {
        fail("FAIL: {fails} check(s) failed")
    }
    println("PASS: all std.crypto sha checks passed")
}''')
open(f"{out}/test_sha.sten", "w").write("\n".join(lines) + "\n")
