#!/usr/bin/env python3
"""Salva o pseudocódigo de um resultado JSON do REA (procedure_pseudo_code) em trabalho/pseudocodigo.
Uso: python3 -I rea_salva.py <resultado.json> <dir_pseudocodigo> [rotulo]
Grava <endereco>.c com cabeçalho (Evidence ID) e acrescenta uma linha a INDICE.tsv."""
import json, os, sys
r = json.load(open(sys.argv[1]))
proc = r["parameters"]["procedure"]
nome = f"{proc}.c"
txt = r["raw_result"]["value"] if isinstance(r["raw_result"], dict) else r["raw_result"]
with open(os.path.join(sys.argv[2], nome), "w", encoding="utf-8") as f:
    f.write(f"// Evidence {r['evidence_id']} — {r['provider']['id']} {r['provider'].get('version')}\n")
    f.write(f"// limitações: {json.dumps(r['raw_result'].get('limitations', []), ensure_ascii=False)}\n")
    f.write(txt)
rot = sys.argv[3] if len(sys.argv) > 3 else ""
with open(os.path.join(sys.argv[2], "INDICE.tsv"), "a", encoding="utf-8") as f:
    f.write(f"{proc}\t{r['evidence_id']}\t{rot}\n")
print(nome, r["evidence_id"], len(txt.splitlines()), "linhas")
