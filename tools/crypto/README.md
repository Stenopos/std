# Crypto generators

The constants and test vectors in `crypto/` are generated, not typed in.
These scripts reproduce them:

| Script | Writes |
|--------|--------|
| `gen_sha.py <crypto-dir>` | `sha256.sten`, `sha512.sten`: round and initial-hash constants computed exactly from the primes' cube and square roots |
| `gen_sha_tests.py <crypto-dir>` | `test_sha.sten`: expected digests from Python's `hashlib` |
| `gen_ed25519.py <crypto-dir> <this-dir> ed25519.sten.in` | `ed25519.sten`: the field constants (d, 2d, the base point, sqrt(-1)) and the group order, derived from the curve by `ref_ed25519.py` |
| `gen_ed_tests.py <crypto-dir> <this-dir>` | `test_ed25519.sten`: signatures from OpenSSL and Python's `cryptography`, plus invalid cases |

`ref_ed25519.py` is a Python model of the verifier with the same structure as
the Stenopos code; the test generator checks every case against it.

```bash
cd tools/crypto
python3 gen_sha.py ../../crypto
python3 gen_ed25519.py ../../crypto . ed25519.sten.in
```

Regenerating `sha*.sten` and `ed25519.sten` must produce identical files.
The test generators make new keys and signatures each run.
