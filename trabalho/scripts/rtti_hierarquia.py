#!/usr/bin/env python3
"""Hierarquia de classes RTTI MSVC x64 (somente leitura). Complementa rtti_vtables.py.

Uso: python3 -I rtti_hierarquia.py <pe> <rtti_vtables.json> <saida.json>

Layout x64 (RVAs de 32 bits):
  CompleteObjectLocator:     +0x10 pClassDescriptor
  ClassHierarchyDescriptor:  +0 signature +4 attributes(1=herança múltipla, 2=virtual)
                             +8 numBaseClasses +0xC pBaseClassArray
  BaseClassArray:            numBaseClasses × RVA de BaseClassDescriptor (o 1º é a própria classe)
  BaseClassDescriptor:       +0 pTypeDescriptor +4 numContainedBases +8 mdisp +0xC pdisp
                             +0x10 vdisp +0x14 attributes +0x18 pClassDescriptor
"""
import json, re, struct, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from rtti_vtables import load  # noqa: E402

BASIC = {"X": "void", "_N": "bool", "_W": "wchar_t", "D": "char", "E": "uint8_t", "H": "int",
         "I": "unsigned", "J": "long", "K": "unsigned long", "_J": "int64", "_K": "uint64",
         "M": "float", "N": "double", "F": "short", "G": "unsigned short", "C": "int8_t"}


class Undname:
    """Demangler mínimo para nomes de tipo RTTI ('.?AV...@@'). Cobre nomes, namespaces,
    templates (?$), back-references (0-9), ponteiros/handles C++/CX (PE$AA = ^) e tipos básicos.
    O que não entende fica entre colchetes, cru."""

    def __init__(self, s):
        self.s, self.i, self.names = s, 0, []

    def peek(self, n=1):
        return self.s[self.i:self.i + n]

    def simple_name(self):
        c = self.peek()
        if c.isdigit():
            self.i += 1
            return self.names[int(c)] if int(c) < len(self.names) else f"<br{c}>"
        if self.peek(2) == "?$":
            self.i += 2
            saved = self.names
            self.names = []
            n = self.raw_ident()
            args = self.template_args()
            self.names = saved
            full = f"{n}<{', '.join(args)}>"
            self.names.append(full)
            return full
        if self.peek(2) == "?A":  # namespace anônimo
            j = self.s.index("@", self.i)
            self.i = j + 1
            return "`anonymous namespace'"
        n = self.raw_ident()
        self.names.append(n)
        return n

    def raw_ident(self):
        j = self.s.index("@", self.i)
        n = self.s[self.i:j]
        self.i = j + 1
        return n

    def qualified(self):
        parts = []
        while self.i < len(self.s) and self.peek() != "@":
            parts.append(self.simple_name())
        self.i += 1
        return "::".join(reversed(parts))

    def template_args(self):
        args = []
        while self.i < len(self.s) and self.peek() != "@":
            args.append(self.type())
        self.i += 1
        return args

    def type(self):
        c = self.peek()
        if self.peek(2) in BASIC:
            self.i += 2
            return BASIC[self.s[self.i - 2:self.i]]
        if c in "VUTW":
            self.i += 1
            if c == "W":  # enum: W4Nome
                self.i += 1
            return self.qualified()
        if c in "PQAB":
            self.i += 1
            handle = False
            if self.peek(4) == "E$AA":
                self.i += 4
                handle = True
            elif self.peek(2) in ("EA", "EB"):
                self.i += 2
            elif self.peek() in "AB":
                self.i += 1
            t = self.type()
            return t + ("^" if handle else ("&" if c in "AB" else "*"))
        if c == "$":
            if self.peek(2) == "$0":
                self.i += 2
                return self.number()
            if self.peek(3) in ("$$Q", "$$V", "$$Z"):
                self.i += 3
                return ""
            if self.peek(3) == "$$A":
                self.i += 3
                return "<fn>"
        if c in BASIC:
            self.i += 1
            return BASIC[c]
        if c.isdigit():
            self.i += 1
            return self.names[int(c)] if int(c) < len(self.names) else f"<br{c}>"
        rest = self.s[self.i:]
        self.i = len(self.s)
        return f"[{rest}]"

    def number(self):
        c = self.peek()
        neg = c == "?"
        if neg:
            self.i += 1
            c = self.peek()
        if c.isdigit():
            self.i += 1
            v = int(c) + 1
        else:
            j = self.s.index("@", self.i)
            v = int(self.s[self.i:j].translate(str.maketrans("ABCDEFGHIJKLMNOP", "0123456789abcdef")) or "0", 16)
            self.i = j + 1
        return str(-v if neg else v)


def undname(raw):
    try:
        u = Undname(raw[4:])
        return u.qualified()
    except Exception:
        return raw


def main():
    path, vtjson, outp = sys.argv[1:4]
    d, ib, secs = load(path)

    def rva2off(r):
        for s in secs:
            if s["va"] <= r < s["va"] + max(s["rs"], s["vs"]):
                return r - s["va"] + s["rp"]

    def u32(rva, k=0):
        return struct.unpack_from("<I", d, rva2off(rva) + k)[0]

    def td_name(rva):
        o = rva2off(rva) + 0x10
        return d[o:d.index(b"\0", o)].decode()

    vt = json.load(open(vtjson))
    out = []
    for c in vt["classes"]:
        col = int(c["vftables"][0]["col"], 16) - ib
        chd = u32(col, 0x10)
        attrs, nbase, bca = u32(chd, 4), u32(chd, 8), u32(chd, 0xC)
        bases = []
        for k in range(nbase):
            bcd = u32(bca, 4 * k)
            bases.append(dict(name=undname(td_name(u32(bcd, 0))), contained=u32(bcd, 4),
                              mdisp=struct.unpack_from("<i", d, rva2off(bcd) + 8)[0],
                              attributes=u32(bcd, 0x14)))
        out.append(dict(name=undname(c["raw"]), raw=c["raw"], type_descriptor=c["type_descriptor"],
                        chd=hex(ib + chd), chd_attributes=attrs,
                        bases=bases[1:],  # bases[0] é a própria classe
                        vftables=[dict(vftable=v["vftable"], this_offset=v["this_offset"], n=len(v["entries"]),
                                       entries=v["entries"]) for v in c["vftables"]]))
    # TypeDescriptors sem vftable (só nome): úteis para tipos lançados em exceção, etc.
    with_vt = {c["raw"] for c in vt["classes"]}
    others = sorted({m.group()[:-1].decode() for m in re.finditer(rb"\.\?A[VU][\x21-\x7e]+?@@\0", d)} - with_vt)
    json.dump(dict(file=path, classes=out, td_sem_vftable=[dict(raw=r, name=undname(r)) for r in others]),
              open(outp, "w"), indent=1)
    print(f"{len(out)} classes c/ vftable, {len(others)} TDs sem vftable -> {outp}")


if __name__ == "__main__":
    main()
