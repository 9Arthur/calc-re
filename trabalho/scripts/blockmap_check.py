#!/usr/bin/env python3
"""Confere os arquivos de um pacote APPX/MSIX extraído contra o seu AppxBlockMap.xml.

Uso: python3 -I blockmap_check.py <pasta_do_pacote>
Para cada <File>: tamanho declarado == tamanho no disco e SHA-256 (base64) de cada bloco de 64 KiB
não comprimido == <Block Hash>. Só leitura.
"""
import base64, hashlib, os, sys
import xml.etree.ElementTree as ET

NS = "{http://schemas.microsoft.com/appx/2010/blockmap}"
BLOCK = 65536


def main(pkg):
    root = ET.parse(os.path.join(pkg, "AppxBlockMap.xml")).getroot()
    print(f"HashMethod={root.get('HashMethod')}")
    tot = ok = blocos = 0
    for f in root.iter(NS + "File"):
        name, size = f.get("Name"), int(f.get("Size"))
        hashes = [b.get("Hash") for b in f.findall(NS + "Block")]
        p = os.path.join(pkg, *name.split("\\"))
        tot += 1
        if not os.path.exists(p):
            print(f"AUSENTE {name}")
            continue
        d = open(p, "rb").read()
        calc = [base64.b64encode(hashlib.sha256(d[i:i + BLOCK]).digest()).decode()
                for i in range(0, len(d), BLOCK)]
        good = len(d) == size and calc == hashes
        ok += good
        blocos += len(hashes)
        if not good or name.lower().endswith((".pri", ".xml")):
            print(f"{'OK   ' if good else 'FALHA'} {name} declarado={size} disco={len(d)} blocos={len(hashes)}"
                  + (f" sha256={hashlib.sha256(d).hexdigest()}" if name.lower().endswith('.pri') else ""))
    print(f"arquivos no BlockMap: {tot}; conferem: {ok}; blocos conferidos: {blocos}")


if __name__ == "__main__":
    main(sys.argv[1])
