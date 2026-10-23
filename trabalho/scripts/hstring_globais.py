#!/usr/bin/env python3
"""Recupera, nos inicializadores estáticos de CalcViewModel.dll, os pares
HSTRING global -> literal UTF-16 (padrão: lea rcx,[literal] ... lea r9,[global] ... call
WindowsCreateStringReference). Somente leitura. Uso: python3 -I hstring_globais.py <pe> <saida.json>"""
import json, struct, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from rtti_vtables import load

def main():
    d, ib, secs = load(sys.argv[1])
    text = next(s for s in secs if s["name"] == ".text")
    data = next(s for s in secs if s["name"] == ".data")
    rd = next(s for s in secs if s["name"] == ".rdata")
    def rva2off(r):
        for s in secs:
            if s["va"] <= r < s["va"] + s["rs"]:
                return r - s["va"] + s["rp"]
    leas = []  # (rva_instr, reg, target_rva)
    t0, t1 = text["rp"], text["rp"] + text["rs"]
    for o in range(t0, t1 - 7):
        if d[o + 1] == 0x8D and d[o] in (0x48, 0x4C) and d[o + 2] in (0x0D, 0x05, 0x15):
            reg = {(0x48, 0x0D): "rcx", (0x4C, 0x0D): "r9", (0x4C, 0x05): "r8", (0x48, 0x15): "rdx"}.get((d[o], d[o + 2]))
            if not reg:
                continue
            rva = text["va"] + (o - t0)
            tgt = rva + 7 + struct.unpack_from("<i", d, o + 3)[0]
            leas.append((rva, reg, tgt))
    out = {}
    for i, (rva, reg, tgt) in enumerate(leas):
        if reg != "r9" or not (data["va"] <= tgt < data["va"] + data["vs"]):
            continue
        # literal: lea rcx mais próximo antes (até 0x40 bytes) apontando para .rdata
        for j in range(i - 1, max(-1, i - 6), -1):
            r2, reg2, t2 = leas[j]
            if rva - r2 > 0x40:
                break
            if reg2 == "rcx" and rd["va"] <= t2 < rd["va"] + rd["vs"]:
                o2 = rva2off(t2)
                end = o2
                while d[end:end + 2] != b"\0\0":
                    end += 2
                s = d[o2:end].decode("utf-16-le", "replace")
                out[hex(ib + tgt)] = dict(literal=s, literal_va=hex(ib + t2), init_instr=hex(ib + rva))
                break
    json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
    print(len(out), "globais HSTRING resolvidos")

if __name__ == "__main__":
    main()
