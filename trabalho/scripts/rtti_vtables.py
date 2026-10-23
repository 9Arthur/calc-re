#!/usr/bin/env python3
"""Recupera classes RTTI MSVC x64 e seus vftables de um PE (somente leitura).

Uso: python3 -I rtti_vtables.py <pe> <saida.json>

Layout x64 (offsets relativos à imagem = RVA):
  TypeDescriptor:          +0 pVFTable(8) +8 spare(8) +0x10 name ".?AV...@@\0"
  CompleteObjectLocator:   +0 signature(4)=1 +4 offset(4) +8 cdOffset(4)
                           +0xC pTypeDescriptor(RVA) +0x10 pClassDescriptor(RVA) +0x14 pSelf(RVA)
  vftable:                 precedido (em -8) por ponteiro absoluto para o COL.
"""
import json, re, struct, sys


def load(path):
    d = open(path, "rb").read()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, e + 6)[0]
    osz = struct.unpack_from("<H", d, e + 20)[0]
    ib = struct.unpack_from("<Q", d, e + 24 + 24)[0]
    s = e + 24 + osz
    secs = []
    for _ in range(n):
        name = d[s:s + 8].rstrip(b"\0").decode()
        vs, va, rs, rp = struct.unpack_from("<IIII", d, s + 8)
        ch = struct.unpack_from("<I", d, s + 36)[0]
        secs.append(dict(name=name, va=va, vs=vs, rp=rp, rs=rs, ch=ch))
        s += 40
    return d, ib, secs


def demangle_simple(raw):
    """'.?AVFoo@Bar@@' -> 'Bar::Foo'. Nomes com templates/lambdas ficam crus."""
    body = raw[4:-2]
    if any(c in body for c in "?$<"):
        return None
    return "::".join(reversed(body.split("@")))


def main():
    path, outp = sys.argv[1], sys.argv[2]
    d, ib, secs = load(path)

    def off2rva(o):
        for s in secs:
            if s["rp"] <= o < s["rp"] + s["rs"]:
                return s["va"] + o - s["rp"]

    def rva2off(r):
        for s in secs:
            if s["va"] <= r < s["va"] + s["rs"]:
                return r - s["va"] + s["rp"]

    text = [s for s in secs if s["ch"] & 0x20000000]  # executáveis

    def is_code(va):
        r = va - ib
        return any(s["va"] <= r < s["va"] + s["vs"] for s in text)

    # 1. TypeDescriptors
    tds = {}
    for m in re.finditer(rb"\.\?A[VU][\x21-\x7e]+?@@\0", d):
        rva = off2rva(m.start() - 0x10)
        if rva is not None:
            tds[rva] = m.group()[:-1].decode()
    # 2. COLs: varre seções não executáveis em passos de 4
    cols = {}
    for s in secs:
        if s["ch"] & 0x20000000:
            continue
        base = s["rp"]
        for o in range(base, base + s["rs"] - 24, 4):
            sig, offs, cdo, ptd, pcd, pself = struct.unpack_from("<IIIIII", d, o)
            if sig == 1 and ptd in tds and pself == s["va"] + o - base:
                cols[pself] = dict(td=ptd, offset=offs, cd_offset=cdo)
    # 3. vftables: ponteiro absoluto para COL seguido de ponteiros para código
    col_vas = {ib + r: r for r in cols}
    classes = {}
    for s in secs:
        if s["ch"] & 0x20000000:
            continue
        base = s["rp"]
        for o in range(base, base + s["rs"] - 16, 8):
            v = struct.unpack_from("<Q", d, o)[0]
            if v not in col_vas:
                continue
            vft_va = ib + s["va"] + o + 8 - base
            entries = []
            p = o + 8
            # termina no primeiro slot que não aponta para código (ex.: o COL do próximo vftable)
            while p + 8 <= base + s["rs"]:
                f = struct.unpack_from("<Q", d, p)[0]
                if not is_code(f):
                    break
                entries.append(hex(f))
                p += 8
            col = cols[col_vas[v]]
            raw = tds[col["td"]]
            classes.setdefault(raw, dict(raw=raw, name=demangle_simple(raw),
                                         type_descriptor=hex(ib + col["td"]), vftables=[]))
            classes[raw]["vftables"].append(dict(vftable=hex(vft_va), col=hex(v),
                                                 this_offset=col["offset"], entries=entries))
    out = dict(file=path, image_base=hex(ib), type_descriptors=len(tds), cols=len(cols),
               classes_with_vftable=len(classes), classes=sorted(classes.values(), key=lambda c: c["raw"]))
    json.dump(out, open(outp, "w"), indent=1)
    print(f"{path}: TD={len(tds)} COL={len(cols)} classes c/ vftable={len(classes)} -> {outp}")


if __name__ == "__main__":
    main()
