#!/usr/bin/env python3
"""Validação independente do parser PRI (pri_dump.py). Só biblioteca padrão, só leitura.

Uso:
    python3 -I pri_valida.py <resources.pri principal> <dir_tsv_principal> \
        [<resources.pri de recursos> <dir_tsv_recursos>] [--ids <cengine-ids.json>] [--saida <arquivo.json>]

Reimplementa, sem importar pri_dump.py, o caminho nome -> item -> candidato -> data item, usando
caminhos de código diferentes onde o formato tem redundância:
  * item -> entrada pela tabela de 1323 u16 do esquema (pri_dump usa o campo 'index' de cada entrada);
  * nome completo pela lista de filhos do ScopeEx (pri_dump sobe pelo campo 'parent');
  * grupos de iteminfo esparsos (pacotes de recursos) e esquema externo conferido pela referência.
Depois compara o resultado com os TSV gerados por pri_dump.py e roda checagens de conteúdo:
  1. fronteiras: todo data item de string começa logo após um NUL (ou no início do bloco) e termina em NUL
     -> uma tabela de offsets desalinhada produziria strings começando no meio de outra;
  2. valores previsíveis (dígitos, nomes de funções, operadores) nos idiomas disponíveis;
  3. alinhamento EN/PT das mesmas chaves (invariantes: só símbolos/dígitos iguais, placeholders %n iguais);
  4. chaves de CEngineStrings pedidas pelo motor (cengine-ids.json) que não existem no esquema.
"""
import json
import os
import re
import struct
import sys
import zlib


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def secoes(d):
    toc, ini, n = u32(d, 0x10), u32(d, 0x14), u16(d, 0x18)
    out = []
    for i in range(n):
        ident = d[toc + 32 * i: toc + 32 * i + 16].decode("ascii")
        off, ln = u32(d, toc + 32 * i + 24), u32(d, toc + 32 * i + 28)
        a = ini + off
        out.append((ident.rstrip("\0 "), a + 32, a + ln - 8))  # conteúdo [ini, fim)
    return out


def esquema(d, c0, c1):
    """Retorna dict com versão/checksum/nome único e lista item -> nome completo (via ScopeEx)."""
    if c0 == c1:
        return None
    p = c0 + 8 + 16  # u16 1, u16 ulen, u16 nlen, u16 0, char[16]
    major, minor, _, chk, nsc, nit = struct.unpack_from("<HHIIII", d, p)
    p += 20
    q = p
    while d[q:q + 2] != b"\0\0":
        q += 2
    unico = d[p:q].decode("utf-16-le")
    q += 2
    while d[q:q + 2] != b"\0\0":
        q += 2
    q += 2 + 2  # nome + u16 0
    p = q + 4  # u16 maior caminho, u16 0
    nnomes, _, _, uni_chars, _, asc_len = struct.unpack_from("<IIIIII", d, p)
    p += 24
    ent = [struct.unpack_from("<HHHBBHH", d, p + 12 * k) for k in range(nnomes)]
    p += 12 * nnomes
    scopeex = [struct.unpack_from("<HHH", d, p + 8 * k) for k in range(nsc)]
    p += 8 * nsc
    item_tab = list(struct.unpack_from(f"<{nit}H", d, p))
    p += 2 * nit
    uni, asc = p, p + 2 * uni_chars

    def nome(k):
        _, fpl, _, nlen, fl, noff, _ = ent[k]
        if fpl == 0:
            return ""
        o = noff | ((fl & 0xF) << 16)
        if fl & 0x20:
            return d[asc + o: d.index(b"\0", asc + o)].decode("ascii")
        e = uni + 2 * o
        f = e
        while d[f:f + 2] != b"\0\0":
            f += 2
        return d[e:f].decode("utf-16-le")

    # caminho completo descendo da raiz pelos filhos do ScopeEx (sem usar o campo 'parent')
    caminho = {}
    raiz = scopeex[0][0]
    pilha = [(raiz, "")]
    while pilha:
        k, pref = pilha.pop()
        nm = nome(k)
        cam = f"{pref}/{nm}" if pref and nm else (nm or pref)
        caminho[k] = cam
        if ent[k][4] & 0x10:
            idx_esc = ent[k][6]
            si, cc, fc = scopeex[idx_esc]
            assert si == k, "ScopeEx não aponta para a própria entrada"
            for c in range(fc, fc + cc):
                pilha.append((c, cam))
    itens = [caminho[item_tab[i]] for i in range(nit)]
    # CRC32 do esquema, recalculado aqui de forma independente
    crc = 0

    def soma(s):
        nonlocal crc
        b = ("".join(ch.lower() if "A" <= ch <= "Z" else ch for ch in s) + "\0").encode("utf-16-le")
        crc = zlib.crc32(struct.pack("<i", len(b)) + b, crc)

    soma(unico)
    # o nome curto fica entre o nome único e o u16 0
    p2 = c0 + 24 + 20 + 2 * (len(unico) + 1)
    f = p2
    while d[f:f + 2] != b"\0\0":
        f += 2
    soma(d[p2:f].decode("utf-16-le"))
    crc = zlib.crc32(struct.pack("<HHiiiI", major, minor, 0, 0, 1, nsc), crc)
    for si, _, _ in scopeex:
        soma(caminho[si])
    crc = zlib.crc32(struct.pack("<iiiI", 0, 0, 1, nit), crc)
    for i in range(nit):
        soma(itens[i])
    return {"versao": (major, minor), "checksum": chk, "crc_recalculado": crc, "escopos": nsc, "itens": nit,
            "nome_unico": unico, "nomes_itens": itens, "filhos_raiz": {
                caminho[c]: scopeex[ent[c][6]][1] for c in range(scopeex[0][2], scopeex[0][2] + scopeex[0][1])
                if ent[c][4] & 0x10}}


def decisao(d, c0):
    nd, nq, ns, ndec, nidx, _ = struct.unpack_from("<6H", d, c0)
    p = c0 + 12
    decs = [struct.unpack_from("<HH", d, p + 4 * k) for k in range(ndec)]
    p += 4 * ndec
    sets = [struct.unpack_from("<HH", d, p + 4 * k) for k in range(ns)]
    p += 4 * ns
    quals = [struct.unpack_from("<HHHH", d, p + 8 * k)[0] for k in range(nq)]
    p += 8 * nq
    dist = [struct.unpack_from("<HHHHI", d, p + 12 * k) for k in range(nd)]
    p += 12 * nd
    idx = list(struct.unpack_from(f"<{nidx}H", d, p))
    p += 2 * nidx
    vals = p

    def val(o):
        e = vals + 2 * o
        f = e
        while d[f:f + 2] != b"\0\0":
            f += 2
        return d[e:f].decode("utf-16-le")

    lang_set = []
    for first, n in sets:
        ls = [val(dist[quals[idx[first + j]]][4]) for j in range(n)
              if dist[quals[idx[first + j]]][1] == 0]  # tipo 0 = Language
        lang_set.append(ls[0] if ls else "")
    return [[lang_set[idx[f + j]] for j in range(n)] for f, n in decs]


def dataitems(d, c0):
    n_s, n_b, tot = u16(d, c0 + 4), u16(d, c0 + 6), u32(d, c0 + 8)
    p = c0 + 12
    ini = p + 4 * n_s + 8 * n_b
    its = [(ini + u16(d, p + 4 * k), u16(d, p + 4 * k + 2)) for k in range(n_s)]
    p += 4 * n_s
    its += [(ini + u32(d, p + 8 * k), u32(d, p + 8 * k + 4)) for k in range(n_b)]
    return its, n_s, ini


def resolver(caminho, esquema_externo=None):
    d = open(caminho, "rb").read()
    secs = secoes(d)
    sch = dec = None
    di = {}
    rm = None
    for i, (ident, a, b) in enumerate(secs):
        if ident == "[mrm_hschemaex]":
            sch = esquema(d, a, b)
        elif ident == "[mrm_decn_info]":
            dec = decisao(d, a)
        elif ident == "[mrm_dataitem]":
            di[i] = dataitems(d, a)
        elif ident == "[mrm_res_map2_]":
            rm = (a, b)
    a, b = rm
    env_len, n_env, _, ref_len, _, nrvt, ni2g, nig = struct.unpack_from("<8H", d, a)
    nii, ncand = u32(d, a + 16), u32(d, a + 20)
    p = a + 32 + env_len
    ref = None
    if ref_len:
        maj, mnr, _, chk, nsc, nit = struct.unpack_from("<HHIIII", d, p)
        q = p + 32
        f = q
        while d[f:f + 2] != b"\0\0":
            f += 2
        ref = {"versao": (maj, mnr), "checksum": chk, "escopos": nsc, "itens": nit,
               "nome_unico": d[q:f].decode("utf-16-le")}
    p += ref_len
    tipos = [u32(d, p + 8 * k + 4) for k in range(nrvt)]
    p += 8 * nrvt
    i2g = [struct.unpack_from("<HH", d, p + 4 * k) for k in range(ni2g)]
    p += 4 * ni2g
    ig = [struct.unpack_from("<HH", d, p + 4 * k) for k in range(nig)]
    p += 4 * nig
    ii = [struct.unpack_from("<HH", d, p + 4 * k) for k in range(nii)]
    p += 4 * nii
    cands = [struct.unpack_from("<BBHHH", d, p + 8 * k) for k in range(ncand)]
    if sch is None:
        sch = esquema_externo
        assert ref and all(ref[k] == sch[k] for k in ("versao", "checksum", "escopos", "itens", "nome_unico")), \
            "referência de esquema não confere com o esquema externo"
    valores = {}  # nome -> {idioma: (valor, seção, item, offset)}
    for first_item, g in i2g:
        size, fii = ig[g] if g < len(ig) else (1, g - len(ig))
        for k in range(size):
            dec_i, fc = ii[fii + k]
            nome = sch["nomes_itens"][first_item + k]
            for j, lang in enumerate(dec[dec_i]):
                t, vt, src, item, sec = cands[fc + j]
                assert t == 1 and src == 0
                off, ln = di[sec][0][item]
                raw = d[off:off + ln]
                vtn = tipos[vt]
                if vtn == 2:  # EmbeddedData
                    continue
                if vtn in (0, 1):
                    v = raw.decode("utf-16-le")
                elif vtn in (3, 5):
                    v = raw.decode("ascii")
                else:
                    v = raw.decode("utf-8")
                valores.setdefault(nome, {})[lang] = (v.rstrip("\0"), sec, item, off)
    # checagem de fronteiras de string em todos os data items (exceto blobs binários)
    fronteira_ruim = []
    for sec, (its, n_s, ini) in di.items():
        for k, (off, ln) in enumerate(its[:n_s]):
            raw = d[off:off + ln]
            if raw[:4] == b"XBF\0":
                continue
            larg = 2 if (ln >= 2 and raw[-2:] == b"\0\0" and ln % 2 == 0 and b"\0" in raw[1::2]) else 1
            antes_ok = off == ini or d[off - larg:off] == b"\0" * larg or d[off - 1] == 0
            if not (raw.endswith(b"\0") and antes_ok):
                fronteira_ruim.append((sec, k, hex(off)))
    return {"dados": d, "esquema": sch, "ref": ref, "valores": valores, "fronteira_ruim": fronteira_ruim,
            "n_strings": sum(v[1] for v in di.values())}


def ler_tsv(dirr):
    out = {}
    for fn in os.listdir(dirr):
        if not fn.endswith(".tsv") or fn.startswith("xbf"):
            continue
        esc = fn[:-4]
        with open(os.path.join(dirr, fn), encoding="utf-8") as f:
            next(f)
            for ln in f:
                k, lang, v = ln.rstrip("\n").split("\t")
                v = re.sub(r"\\(.)", lambda m: {"t": "\t", "r": "\r", "n": "\n", "\\": "\\"}[m.group(1)], v)
                k = re.sub(r"\\(.)", lambda m: {"t": "\t", "r": "\r", "n": "\n", "\\": "\\"}[m.group(1)], k)
                out.setdefault(f"{esc}/{k}", {})[lang] = v
    return out


# Valores previsíveis [I quanto à expectativa; O quanto ao valor lido]
R = "Resources/"
AP = "/[using:Windows.UI.Xaml.Automation]AutomationProperties/Name"
KC = "/[using:CalculatorApp.Common]KeyboardShortcutManager/Character"
DIG_EN = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
DIG_PT = ["Zero", "Um", "Dois", "Três", "Quatro", "Cinco", "Seis", "Sete", "Oito", "Nove"]
ESPERADO = {
    "EN-US": {**{f"{R}num{i}Button{KC}": str(i) for i in range(10)},
              **{f"{R}num{i}Button{AP}": DIG_EN[i] for i in range(10)},
              f"{R}sinButton{AP}": "Sine", f"{R}cosButton{AP}": "Cosine", f"{R}tanButton{AP}": "Tangent",
              "CEngineStrings/13": "+", "CEngineStrings/14": "-", "CEngineStrings/11": "÷",
              "CEngineStrings/12": "×", "CEngineStrings/48": "(", "CEngineStrings/49": ")",
              "CEngineStrings/41": "=", "CEngineStrings/22": "sin", "CEngineStrings/24": "tan",
              "CEngineStrings/25": "sinh", "CEngineStrings/26": "cosh", "CEngineStrings/27": "tanh",
              "CEngineStrings/28": "ln", "CEngineStrings/29": "log", "CEngineStrings/68": "cos₀",
              "CEngineStrings/74": "cosᵣ", "CEngineStrings/80": "cos₉",
              "CEngineStrings/99": "Cannot divide by zero"},
    "PT-BR": {**{f"{R}num{i}Button{AP}": DIG_PT[i] for i in range(10)}},
}


def main():
    args = sys.argv[1:]
    opts = {}
    for o in ("--ids", "--saida"):
        if o in args:
            k = args.index(o)
            opts[o] = args[k + 1]
            del args[k:k + 2]
    rel = {}
    princ = resolver(args[0])
    sch = princ["esquema"]
    rel["principal"] = {"arquivo": args[0], "crc_gravado": hex(sch["checksum"]),
                        "crc_recalculado": hex(sch["crc_recalculado"]), "itens": sch["itens"],
                        "filhos_raiz": sch["filhos_raiz"], "strings_com_fronteira_ruim": princ["fronteira_ruim"],
                        "data_items_string": princ["n_strings"]}
    conj = [(princ, args[1], "principal")]
    if len(args) >= 4:
        rec = resolver(args[2], sch)
        rel["recursos"] = {"arquivo": args[2], "referencia_esquema": {k: (hex(v) if k == "checksum" else v)
                                                                       for k, v in rec["ref"].items()},
                           "strings_com_fronteira_ruim": rec["fronteira_ruim"],
                           "data_items_string": rec["n_strings"]}
        conj.append((rec, args[3], "recursos"))
    # comparação com os TSV do pri_dump
    for res, dirr, tag in conj:
        tsv = ler_tsv(dirr)
        meu = {k: {l: v[0] for l, v in m.items()} for k, m in res["valores"].items()
               if k.split("/", 1)[0] in ("CEngineStrings", "Resources")}
        dif = [k for k in set(tsv) | set(meu) if tsv.get(k) != meu.get(k)]
        rel[tag]["comparacao_tsv"] = {"chaves_validador": len(meu), "chaves_tsv": len(tsv),
                                      "divergencias": sorted(dif)[:20], "n_divergencias": len(dif)}
    # valores previsíveis
    todos = {}
    for res, _, _ in conj:
        for k, m in res["valores"].items():
            for l, v in m.items():
                todos.setdefault(l, {})[k] = v
    prev = []
    for lang, exp in ESPERADO.items():
        for k, v in exp.items():
            got = todos.get(lang, {}).get(k)
            prev.append({"idioma": lang, "chave": k, "esperado": v, "lido": got[0] if got else None,
                         "origem": f"{got[1]}/{got[2]} @{got[3]:#x}" if got else None,
                         "ok": bool(got) and got[0] == v})
    rel["previsiveis"] = {"total": len(prev), "ok": sum(p["ok"] for p in prev),
                          "falhas": [p for p in prev if not p["ok"]]}
    c23 = todos["EN-US"].get("CEngineStrings/23")
    rel["CEngineStrings_23"] = {"valor": c23[0], "origem": f"{c23[1]}/{c23[2]} @{c23[3]:#x}",
                                "bytes": princ["dados"][c23[3]:c23[3] + 4].hex(" "),
                                "ocorrencias_ascii_cos_nul": [hex(m.start()) for m in
                                                              re.finditer(rb"(?<![A-Za-z])cos\0", princ["dados"])],
                                "vizinhos": {k: todos["EN-US"][f"CEngineStrings/{k}"][0] for k in ("22", "24")}}
    # alinhamento EN/PT
    if "PT-BR" in todos:
        en, pt = todos["EN-US"], todos["PT-BR"]
        comuns = sorted(set(en) & set(pt))
        so_simbolo = [k for k in comuns if not re.search(r"[A-Za-zÀ-ÿ]", en[k][0])]
        simb_dif = [(k, en[k][0], pt[k][0]) for k in so_simbolo if en[k][0] != pt[k][0]]
        ph = lambda s: sorted(re.findall(r"%\d+", s))
        ph_dif = [(k, en[k][0], pt[k][0]) for k in comuns if ph(en[k][0]) != ph(pt[k][0])]
        iguais = sum(en[k][0] == pt[k][0] for k in comuns)
        rel["alinhamento_en_pt"] = {"chaves_comuns": len(comuns), "texto_identico": iguais,
                                    "so_simbolos_ou_digitos": len(so_simbolo), "so_simbolos_divergentes": simb_dif,
                                    "placeholders_divergentes": ph_dif,
                                    "chaves_pt_sem_en": sorted(set(pt) - set(en))}
    # chaves do motor ausentes do esquema
    if "--ids" in opts:
        ids = json.load(open(opts["--ids"]))
        nomes = set(sch["nomes_itens"])
        aus = sorted({e["chave"] for e in ids if f"CEngineStrings/{e['chave']}" not in nomes}, key=lambda x: (len(x), x))
        rel["cengine_ausentes"] = {"entradas_tabela": len(ids), "chaves_distintas_ausentes": len(aus),
                                   "entradas_ausentes": sum(f"CEngineStrings/{e['chave']}" not in nomes for e in ids),
                                   "chaves": aus,
                                   "itens_cengine_no_esquema": sum(n.startswith("CEngineStrings/") for n in nomes)}
    js = json.dumps(rel, ensure_ascii=False, indent=1)
    if "--saida" in opts:
        open(opts["--saida"], "w", encoding="utf-8").write(js)
    print(js)


if __name__ == "__main__":
    main()
