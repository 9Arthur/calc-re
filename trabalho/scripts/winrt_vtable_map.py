#!/usr/bin/env python3
"""Liga métodos WinRT (.winmd) aos slots das vftables C++/CX recuperadas por RTTI.

Uso: python3 -I winrt_vtable_map.py <winmd.json> <rtti_hierarquia.json> <saida.json> [<saida.md>]

Regra observada em CalcViewModel.dll (StandardCalculatorViewModel, ver relatorio/01-arquitetura.md):
na vftable com this_offset da interface, os slots 0-5 são IUnknown+IInspectable, o slot 6+k é o thunk
ABI do k-ésimo método da interface (ordem das linhas MethodDef no .winmd) e, quando a vftable tem
pelo menos 6+2M entradas, o slot 6+M+k é a implementação C++ virtual correspondente.
A posição da interface no objeto vem do mdisp do BaseClassDescriptor (RTTI).
"""
import json, sys


def main():
    wm, hj, outp = sys.argv[1:4]
    w = json.load(open(wm))
    h = json.load(open(hj))
    types = {t["name"]: t for t in w["types"]}
    rtti = {c["name"]: c for c in h["classes"]}
    out = []
    for t in w["types"]:
        if t["kind"] != "class":
            continue
        cxx = t["name"].replace(".", "::")
        targets = []
        if cxx in rtti:
            for i in t["interfaces"]:
                targets.append((cxx, i["interface"], "DefaultAttribute" in i["attrs"]))
        ns, _, short = cxx.rpartition("::")
        fac = f"{ns}::__{short}ActivationFactory"
        for a in t["attributes"]:
            if a["attr"] in ("StaticAttribute", "ActivatableAttribute", "ComposableAttribute") and a["args"] \
                    and isinstance(a["args"][0], str) and a["args"][0] in types and fac in rtti:
                targets.append((fac, a["args"][0], False))
        for cls, iface, default in targets:
            it = types.get(iface)
            if not it:
                continue
            c = rtti[cls]
            ib = iface.replace(".", "::")
            base = next((b for b in c["bases"] if b["name"] == ib), None)
            if base is None:
                continue
            vt = next((v for v in c["vftables"] if v["this_offset"] == base["mdisp"]), None)
            M = len(it["methods"])
            if vt is None or M == 0 or len(vt["entries"]) < 6 + M:
                continue
            has_impl = len(vt["entries"]) >= 6 + 2 * M
            rows = []
            for k, m in enumerate(it["methods"]):
                rows.append(dict(method=m["name"], sig=f"{m['ret']} {m['name']}({', '.join(m['params'])})",
                                 abi=vt["entries"][6 + k],
                                 impl=vt["entries"][6 + M + k] if has_impl else None))
            out.append(dict(runtime_class=t["name"], cxx_class=cls, interface=iface, guid=it["guid"],
                            default=default, vftable=vt["vftable"], this_offset=vt["this_offset"],
                            n_slots=len(vt["entries"]), methods=rows))
    json.dump(out, open(outp, "w"), indent=1)
    if len(sys.argv) > 4:
        L = ["# Mapa método WinRT → vftable C++/CX (CalcViewModel.dll)", "",
             "Gerado por `trabalho/scripts/winrt_vtable_map.py`. `abi` = thunk ABI (slot 6+k);",
             "`impl` = implementação virtual C++ (slot 6+M+k), quando a vftable a contém.", ""]
        for e in out:
            L.append(f"## {e['runtime_class']} — {e['interface'].rsplit('.', 1)[1]}"
                     f"{' (padrão)' if e['default'] else ''}")
            L.append(f"vftable {e['vftable']} (this+{e['this_offset']:#x}, {e['n_slots']} slots), IID {e['guid']}")
            L.append("")
            L.append("| # | método | thunk ABI | implementação |")
            L.append("|---:|---|---|---|")
            for k, r in enumerate(e["methods"]):
                L.append(f"| {k} | `{r['sig']}` | {r['abi']} | {r['impl'] or '—'} |")
            L.append("")
        open(sys.argv[4], "w").write("\n".join(L))
    print(f"{len(out)} interfaces mapeadas, {sum(len(e['methods']) for e in out)} métodos")


if __name__ == "__main__":
    main()
