#!/usr/bin/env python3
"""Lê bytes de um PE pelo endereço virtual (somente leitura).
Uso: python3 -I pe_va.py <pe> <va_hex> <n> [i32|u64|hex|utf16]"""
import struct, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from rtti_vtables import load

def read(path, va, n):
    d, ib, secs = load(path)
    r = va - ib
    for s in secs:
        if s["va"] <= r < s["va"] + max(s["vs"], s["rs"]):
            o = r - s["va"] + s["rp"]
            return d[o:o + n], o
    raise ValueError(hex(va))

if __name__ == "__main__":
    path, va, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
    fmt = sys.argv[4] if len(sys.argv) > 4 else "hex"
    b, off = read(path, va, n)
    print(f"# va={va:#x} file_off={off:#x}")
    if fmt == "i32":
        print([struct.unpack_from("<i", b, i)[0] for i in range(0, len(b) - 3, 4)])
    elif fmt == "u64":
        print([hex(struct.unpack_from("<Q", b, i)[0]) for i in range(0, len(b) - 7, 8)])
    elif fmt == "utf16":
        print(b.decode("utf-16-le", "replace"))
    else:
        print(b.hex(" "))
