#!/usr/bin/env python3
"""Procura, em binários, os IIDs (GUID binário, 16 bytes little-endian) das interfaces de um .winmd.
Uso: python3 -I iid_scan.py <winmd.json> <saida.json> <pe1> [<pe2> ...]"""
import json, struct, sys, uuid

def guid_bytes(g):
    return uuid.UUID(g).bytes_le

def main():
    w = json.load(open(sys.argv[1]))
    ifaces = [t for t in w["types"] if t["kind"] in ("interface", "delegate") and t["guid"]]
    out = {}
    for pe in sys.argv[3:]:
        d = open(pe, "rb").read()
        hits = []
        for t in ifaces:
            b = guid_bytes(t["guid"])
            offs, i = [], d.find(b)
            while i != -1:
                offs.append(hex(i))
                i = d.find(b, i + 1)
            if offs:
                hits.append(dict(interface=t["name"], kind=t["kind"], guid=t["guid"], file_offsets=offs))
        out[pe] = dict(n_interfaces=len(ifaces), n_found=len(hits), hits=hits)
        print(f"{pe}: {len(hits)}/{len(ifaces)} IIDs encontrados")
    json.dump(out, open(sys.argv[2], "w"), indent=1)

if __name__ == "__main__":
    main()
