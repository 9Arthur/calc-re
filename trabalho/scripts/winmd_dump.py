#!/usr/bin/env python3
"""Leitor mínimo de metadados ECMA-335 / WinRT (.winmd), só biblioteca padrão, somente leitura.

Uso: python3 -I winmd_dump.py <arquivo.winmd> <saida.json> [<saida.txt>]

Extrai, por TypeDef: tipo (interface/classe/enum/struct/delegate), base, interfaces implementadas
(com atributos da InterfaceImpl, ex. DefaultAttribute), GUID (GuidAttribute), demais atributos
(Activatable, Static, Composable, ExclusiveTo, Version, Contract...), métodos com assinatura
decodificada, propriedades (get/set), eventos (add/remove), campos e constantes de enum.
Referências: ECMA-335 6ª ed., Partição II §22-24 (tabelas, heaps, assinaturas).
"""
import json, struct, sys

TABLE_NAMES = {0x00: "Module", 0x01: "TypeRef", 0x02: "TypeDef", 0x03: "FieldPtr", 0x04: "Field",
               0x05: "MethodPtr", 0x06: "MethodDef", 0x07: "ParamPtr", 0x08: "Param", 0x09: "InterfaceImpl",
               0x0A: "MemberRef", 0x0B: "Constant", 0x0C: "CustomAttribute", 0x0D: "FieldMarshal",
               0x0E: "DeclSecurity", 0x0F: "ClassLayout", 0x10: "FieldLayout", 0x11: "StandAloneSig",
               0x12: "EventMap", 0x13: "EventPtr", 0x14: "Event", 0x15: "PropertyMap", 0x16: "PropertyPtr",
               0x17: "Property", 0x18: "MethodSemantics", 0x19: "MethodImpl", 0x1A: "ModuleRef",
               0x1B: "TypeSpec", 0x1C: "ImplMap", 0x1D: "FieldRVA", 0x20: "Assembly",
               0x21: "AssemblyProcessor", 0x22: "AssemblyOS", 0x23: "AssemblyRef",
               0x24: "AssemblyRefProcessor", 0x25: "AssemblyRefOS", 0x26: "File", 0x27: "ExportedType",
               0x28: "ManifestResource", 0x29: "NestedClass", 0x2A: "GenericParam", 0x2B: "MethodSpec",
               0x2C: "GenericParamConstraint"}

# índices codificados: (tabelas, bits de tag)
CODED = {
    "TypeDefOrRef": ([0x02, 0x01, 0x1B], 2),
    "HasConstant": ([0x04, 0x08, 0x17], 2),
    "HasCustomAttribute": ([0x06, 0x04, 0x01, 0x02, 0x08, 0x09, 0x0A, 0x00, 0x0E, 0x17, 0x14, 0x11, 0x1A,
                            0x1B, 0x20, 0x23, 0x26, 0x27, 0x28, 0x2A, 0x2C, 0x2B], 5),
    "HasFieldMarshal": ([0x04, 0x08], 1),
    "HasDeclSecurity": ([0x02, 0x06, 0x20], 2),
    "MemberRefParent": ([0x02, 0x01, 0x1A, 0x06, 0x1B], 3),
    "HasSemantics": ([0x14, 0x17], 1),
    "MethodDefOrRef": ([0x06, 0x0A], 1),
    "MemberForwarded": ([0x04, 0x06], 1),
    "Implementation": ([0x26, 0x23, 0x27], 2),
    "CustomAttributeType": ([None, None, 0x06, 0x0A, None], 3),
    "ResolutionScope": ([0x00, 0x1A, 0x23, 0x01], 2),
    "TypeOrMethodDef": ([0x02, 0x06], 1),
}

# colunas: s=#Strings, g=#GUID, b=#Blob, 2/4=constantes, T:<tabela>=índice simples, C:<codificado>
SCHEMA = {
    0x00: [("Generation", 2), ("Name", "s"), ("Mvid", "g"), ("EncId", "g"), ("EncBaseId", "g")],
    0x01: [("ResolutionScope", "C:ResolutionScope"), ("TypeName", "s"), ("TypeNamespace", "s")],
    0x02: [("Flags", 4), ("TypeName", "s"), ("TypeNamespace", "s"), ("Extends", "C:TypeDefOrRef"),
           ("FieldList", "T:04"), ("MethodList", "T:06")],
    0x03: [("Field", "T:04")],
    0x04: [("Flags", 2), ("Name", "s"), ("Signature", "b")],
    0x05: [("Method", "T:06")],
    0x06: [("RVA", 4), ("ImplFlags", 2), ("Flags", 2), ("Name", "s"), ("Signature", "b"), ("ParamList", "T:08")],
    0x07: [("Param", "T:08")],
    0x08: [("Flags", 2), ("Sequence", 2), ("Name", "s")],
    0x09: [("Class", "T:02"), ("Interface", "C:TypeDefOrRef")],
    0x0A: [("Class", "C:MemberRefParent"), ("Name", "s"), ("Signature", "b")],
    0x0B: [("Type", 2), ("Parent", "C:HasConstant"), ("Value", "b")],
    0x0C: [("Parent", "C:HasCustomAttribute"), ("Type", "C:CustomAttributeType"), ("Value", "b")],
    0x0D: [("Parent", "C:HasFieldMarshal"), ("NativeType", "b")],
    0x0E: [("Action", 2), ("Parent", "C:HasDeclSecurity"), ("PermissionSet", "b")],
    0x0F: [("PackingSize", 2), ("ClassSize", 4), ("Parent", "T:02")],
    0x10: [("Offset", 4), ("Field", "T:04")],
    0x11: [("Signature", "b")],
    0x12: [("Parent", "T:02"), ("EventList", "T:14")],
    0x13: [("Event", "T:14")],
    0x14: [("EventFlags", 2), ("Name", "s"), ("EventType", "C:TypeDefOrRef")],
    0x15: [("Parent", "T:02"), ("PropertyList", "T:17")],
    0x16: [("Property", "T:17")],
    0x17: [("Flags", 2), ("Name", "s"), ("Type", "b")],
    0x18: [("Semantics", 2), ("Method", "T:06"), ("Association", "C:HasSemantics")],
    0x19: [("Class", "T:02"), ("MethodBody", "C:MethodDefOrRef"), ("MethodDeclaration", "C:MethodDefOrRef")],
    0x1A: [("Name", "s")],
    0x1B: [("Signature", "b")],
    0x1C: [("MappingFlags", 2), ("MemberForwarded", "C:MemberForwarded"), ("ImportName", "s"), ("ImportScope", "T:1A")],
    0x1D: [("RVA", 4), ("Field", "T:04")],
    0x20: [("HashAlgId", 4), ("MajorVersion", 2), ("MinorVersion", 2), ("BuildNumber", 2), ("RevisionNumber", 2),
           ("Flags", 4), ("PublicKey", "b"), ("Name", "s"), ("Culture", "s")],
    0x21: [("Processor", 4)],
    0x22: [("OSPlatformID", 4), ("OSMajorVersion", 4), ("OSMinorVersion", 4)],
    0x23: [("MajorVersion", 2), ("MinorVersion", 2), ("BuildNumber", 2), ("RevisionNumber", 2), ("Flags", 4),
           ("PublicKeyOrToken", "b"), ("Name", "s"), ("Culture", "s"), ("HashValue", "b")],
    0x24: [("Processor", 4), ("AssemblyRef", "T:23")],
    0x25: [("OSPlatformId", 4), ("OSMajorVersion", 4), ("OSMinorVersion", 4), ("AssemblyRef", "T:23")],
    0x26: [("Flags", 4), ("Name", "s"), ("HashValue", "b")],
    0x27: [("Flags", 4), ("TypeDefId", 4), ("TypeName", "s"), ("TypeNamespace", "s"), ("Implementation", "C:Implementation")],
    0x28: [("Offset", 4), ("Flags", 4), ("Name", "s"), ("Implementation", "C:Implementation")],
    0x29: [("NestedClass", "T:02"), ("EnclosingClass", "T:02")],
    0x2A: [("Number", 2), ("Flags", 2), ("Owner", "C:TypeOrMethodDef"), ("Name", "s")],
    0x2B: [("Method", "C:MethodDefOrRef"), ("Instantiation", "b")],
    0x2C: [("Owner", "T:2A"), ("Constraint", "C:TypeDefOrRef")],
}

ELEM = {0x01: "void", 0x02: "Boolean", 0x03: "Char16", 0x04: "Int8", 0x05: "UInt8", 0x06: "Int16",
        0x07: "UInt16", 0x08: "Int32", 0x09: "UInt32", 0x0A: "Int64", 0x0B: "UInt64", 0x0C: "Single",
        0x0D: "Double", 0x0E: "String", 0x18: "IntPtr", 0x19: "UIntPtr", 0x1C: "Object"}


def load_pe(path):
    d = open(path, "rb").read()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    osz = struct.unpack_from("<H", d, e + 20)[0]
    opt = e + 24
    magic = struct.unpack_from("<H", d, opt)[0]
    dd = opt + (96 if magic == 0x10B else 112)
    secs = []
    s = opt + osz
    for _ in range(nsec):
        vs, va, rs, rp = struct.unpack_from("<IIII", d, s + 8)
        secs.append((va, max(vs, rs), rp))
        s += 40

    def rva2off(r):
        for va, sz, rp in secs:
            if va <= r < va + sz:
                return r - va + rp
        raise ValueError(hex(r))

    cli_rva = struct.unpack_from("<I", d, dd + 14 * 8)[0]
    cli = rva2off(cli_rva)
    md_rva, md_size = struct.unpack_from("<II", d, cli + 8)
    return d, rva2off(md_rva)


class Metadata:
    def __init__(self, path):
        d, md = load_pe(path)
        self.d = d
        assert d[md:md + 4] == b"BSJB"
        vlen = struct.unpack_from("<I", d, md + 12)[0]
        self.version = d[md + 16:md + 16 + vlen].rstrip(b"\0").decode()
        p = md + 16 + vlen + 2
        nstreams = struct.unpack_from("<H", d, p)[0]
        p += 2
        self.streams = {}
        for _ in range(nstreams):
            off, size = struct.unpack_from("<II", d, p)
            p += 8
            end = d.index(b"\0", p)
            name = d[p:end].decode()
            p = (end + 4) & ~3
            self.streams[name] = (md + off, size)
        self.strings_off = self.streams["#Strings"][0]
        self.blob_off = self.streams["#Blob"][0]
        self.guid_off = self.streams["#GUID"][0]
        self._read_tables()

    def string(self, i):
        o = self.strings_off + i
        return self.d[o:self.d.index(b"\0", o)].decode("utf-8")

    def blob(self, i):
        o = self.blob_off + i
        n, k = self.cuint(self.d, o)
        return self.d[o + k:o + k + n]

    def guid(self, i):
        if i == 0:
            return None
        o = self.guid_off + (i - 1) * 16
        return fmt_guid(self.d[o:o + 16])

    @staticmethod
    def cuint(b, o):
        x = b[o]
        if x & 0x80 == 0:
            return x, 1
        if x & 0xC0 == 0x80:
            return ((x & 0x3F) << 8) | b[o + 1], 2
        return ((x & 0x1F) << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3], 4

    def _read_tables(self):
        d = self.d
        t = self.streams.get("#~") or self.streams.get("#-")
        o = t[0]
        heap = d[o + 6]
        valid = struct.unpack_from("<Q", d, o + 8)[0]
        p = o + 24
        self.rows = {}
        for i in range(64):
            if valid >> i & 1:
                self.rows[i] = struct.unpack_from("<I", d, p)[0]
                p += 4
        sz_s = 4 if heap & 1 else 2
        sz_g = 4 if heap & 2 else 2
        sz_b = 4 if heap & 4 else 2

        def idx_size(col):
            if col == "s":
                return sz_s
            if col == "g":
                return sz_g
            if col == "b":
                return sz_b
            if isinstance(col, int):
                return col
            if col.startswith("T:"):
                return 2 if self.rows.get(int(col[2:], 16), 0) < 0x10000 else 4
            tabs, bits = CODED[col[2:]]
            m = max(self.rows.get(x, 0) for x in tabs if x is not None)
            return 2 if m < (1 << (16 - bits)) else 4

        self.tables = {}
        for tid in sorted(self.rows):
            cols = SCHEMA[tid]
            sizes = [idx_size(c) for _, c in cols]
            rows = []
            for _ in range(self.rows[tid]):
                r = {}
                for (name, col), sz in zip(cols, sizes):
                    v = struct.unpack_from("<H" if sz == 2 else "<I", d, p)[0]
                    p += sz
                    if col == "s":
                        v = self.string(v)
                    elif isinstance(col, str) and col.startswith("C:"):
                        tabs, bits = CODED[col[2:]]
                        v = (tabs[v & ((1 << bits) - 1)], v >> bits)  # (tabela, linha 1-based)
                    r[name] = v
                rows.append(r)
            self.tables[TABLE_NAMES[tid]] = rows

    def t(self, name):
        return self.tables.get(name, [])

    # ---------- nomes de tipo ----------
    def typedef_name(self, row1):
        r = self.t("TypeDef")[row1 - 1]
        return f"{r['TypeNamespace']}.{r['TypeName']}" if r["TypeNamespace"] else r["TypeName"]

    def typeref_name(self, row1):
        r = self.t("TypeRef")[row1 - 1]
        return f"{r['TypeNamespace']}.{r['TypeName']}" if r["TypeNamespace"] else r["TypeName"]

    def tdor_name(self, coded):
        tab, row = coded
        if row == 0:
            return None
        if tab == 0x02:
            return self.typedef_name(row)
        if tab == 0x01:
            return self.typeref_name(row)
        if tab == 0x1B:
            sig = self.blob(self.t("TypeSpec")[row - 1]["Signature"])
            return self.sig_type(sig, [0])
        return f"<{tab}:{row}>"

    # ---------- assinaturas ----------
    def sig_type(self, b, pos):
        e = b[pos[0]]
        pos[0] += 1
        if e in ELEM:
            return ELEM[e]
        if e in (0x11, 0x12):  # valuetype / class
            v, k = self.cuint(b, pos[0])
            pos[0] += k
            tab = [0x02, 0x01, 0x1B][v & 3]
            return self.tdor_name((tab, v >> 2))
        if e == 0x1D:  # SZARRAY
            return self.sig_type(b, pos) + "[]"
        if e == 0x10:  # BYREF
            return self.sig_type(b, pos) + "&"
        if e == 0x0F:
            return self.sig_type(b, pos) + "*"
        if e == 0x15:  # GENERICINST
            pos[0] += 0  # byte seguinte: CLASS/VALUETYPE
            pos[0] += 1
            v, k = self.cuint(b, pos[0])
            pos[0] += k
            tab = [0x02, 0x01, 0x1B][v & 3]
            base = self.tdor_name((tab, v >> 2))
            n, k = self.cuint(b, pos[0])
            pos[0] += k
            args = [self.sig_type(b, pos) for _ in range(n)]
            return f"{base.split('`')[0]}<{', '.join(args)}>"
        if e in (0x13, 0x1E):  # VAR / MVAR
            v, k = self.cuint(b, pos[0])
            pos[0] += k
            return f"!{v}" if e == 0x13 else f"!!{v}"
        if e in (0x1F, 0x20):  # CMOD_REQD / CMOD_OPT
            v, k = self.cuint(b, pos[0])
            pos[0] += k
            mod = self.tdor_name(([0x02, 0x01, 0x1B][v & 3], v >> 2))
            inner = self.sig_type(b, pos)
            return f"{inner} modreq({mod})" if e == 0x1F else inner
        return f"<elem 0x{e:02x}>"

    def method_sig(self, b):
        pos = [0]
        cc = b[0]
        pos[0] = 1
        if cc & 0x10:
            _, k = self.cuint(b, pos[0])
            pos[0] += k
        n, k = self.cuint(b, pos[0])
        pos[0] += k
        ret = self.sig_type(b, pos)
        params = [self.sig_type(b, pos) for _ in range(n)]
        return ret, params

    def field_sig(self, b):
        return self.sig_type(b, [1])

    def prop_sig(self, b):
        pos = [1]
        n, k = self.cuint(b, pos[0])
        pos[0] += k
        return self.sig_type(b, pos)


def fmt_guid(g):
    a, b_, c = struct.unpack_from("<IHH", g, 0)
    return f"{a:08x}-{b_:04x}-{c:04x}-{g[8:10].hex()}-{g[10:16].hex()}"


def ranges(rows, key, total):
    """Para listas tipo FieldList/MethodList: devolve [(ini, fim)) 1-based por linha."""
    out = []
    for i, r in enumerate(rows):
        start = r[key]
        end = rows[i + 1][key] if i + 1 < len(rows) else total + 1
        out.append((start, end))
    return out


def attr_args(md, ctor_params, blob):
    """Decodifica argumentos fixos simples de um CustomAttribute (inteiros, strings, enums Int32, System.Type)."""
    if len(blob) < 2 or blob[:2] != b"\x01\x00":
        return None
    p = 2
    out = []
    for t in ctor_params:
        if t in ("UInt32", "Int32") or t.startswith("Windows.Foundation.Metadata.") or t.endswith("Platform"):
            out.append(struct.unpack_from("<I", blob, p)[0])
            p += 4
        elif t in ("UInt16", "Int16"):
            out.append(struct.unpack_from("<H", blob, p)[0])
            p += 2
        elif t in ("UInt8", "Int8", "Boolean"):
            out.append(blob[p])
            p += 1
        elif t in ("String", "System.Type"):
            if blob[p] == 0xFF:
                out.append(None)
                p += 1
            else:
                n, k = Metadata.cuint(blob, p)
                out.append(blob[p + k:p + k + n].decode("utf-8"))
                p += k + n
        else:
            out.append(f"<{t}>")
            return out
    return out


def dump(path):
    md = Metadata(path)
    TD = md.t("TypeDef")
    F, M, P = md.t("Field"), md.t("MethodDef"), md.t("Property")
    frange = ranges(TD, "FieldList", len(F))
    mrange = ranges(TD, "MethodList", len(M))

    # semântica de métodos
    sem = {}  # (tab,row) -> list[(semantics, method_row)]
    for r in md.t("MethodSemantics"):
        sem.setdefault(r["Association"], []).append((r["Semantics"], r["Method"]))
    # custom attributes por pai
    cas = {}
    for r in md.t("CustomAttribute"):
        tab, row = r["Type"]
        if tab == 0x0A:
            mr = md.t("MemberRef")[row - 1]
            aname = md.tdor_name(mr["Class"]) if mr["Class"][0] in (0x01, 0x02, 0x1B) else "?"
            _, params = md.method_sig(md.blob(mr["Signature"]))
        else:
            # ctor definido no próprio winmd
            owner = next(i + 1 for i, (a, b) in enumerate(mrange) if a <= row < b)
            aname = md.typedef_name(owner)
            _, params = md.method_sig(md.blob(M[row - 1]["Signature"]))
        blob = md.blob(r["Value"])
        val = None
        if aname == "Windows.Foundation.Metadata.GuidAttribute" and len(blob) >= 18:
            val = fmt_guid(blob[2:18])
        else:
            val = attr_args(md, params, blob)
        cas.setdefault(r["Parent"], []).append(dict(attr=aname.replace("Windows.Foundation.Metadata.", ""), args=val))
    consts = {r["Parent"]: (r["Type"], md.blob(r["Value"])) for r in md.t("Constant")}
    impls = {}
    for i, r in enumerate(md.t("InterfaceImpl")):
        impls.setdefault(r["Class"], []).append(dict(interface=md.tdor_name(r["Interface"]),
                                                     attrs=[a["attr"] for a in cas.get((0x09, i + 1), [])]))
    pmap = ranges(md.t("PropertyMap"), "PropertyList", len(P))
    props_of = {r["Parent"]: pmap[i] for i, r in enumerate(md.t("PropertyMap"))}
    E = md.t("Event")
    emap = ranges(md.t("EventMap"), "EventList", len(E))
    events_of = {r["Parent"]: emap[i] for i, r in enumerate(md.t("EventMap"))}

    types = []
    for i, r in enumerate(TD):
        row = i + 1
        name = md.typedef_name(row)
        if name == "<Module>":
            continue
        ext = md.tdor_name(r["Extends"]) if r["Extends"][1] else None
        if r["Flags"] & 0x20:
            kind = "interface"
        elif ext == "System.Enum":
            kind = "enum"
        elif ext == "System.ValueType":
            kind = "struct"
        elif ext == "System.MulticastDelegate":
            kind = "delegate"
        else:
            kind = "class"
        attrs = cas.get((0x02, row), [])
        guid = next((a["args"] for a in attrs if a["attr"] == "GuidAttribute"), None)
        t = dict(name=name, kind=kind, extends=ext, flags=hex(r["Flags"]), guid=guid,
                 attributes=[a for a in attrs if a["attr"] != "GuidAttribute"],
                 interfaces=impls.get(row, []), methods=[], properties=[], events=[], fields=[])
        for m in range(*mrange[i]):
            mr = M[m - 1]
            ret, params = md.method_sig(md.blob(mr["Signature"]))
            # nomes dos parâmetros
            pl = mr["ParamList"]
            pend = M[m]["ParamList"] if m < len(M) else len(md.t("Param")) + 1
            pnames = {pp["Sequence"]: pp["Name"] for pp in md.t("Param")[pl - 1:pend - 1]}
            t["methods"].append(dict(name=mr["Name"], ret=ret, flags=hex(mr["Flags"]),
                                     params=[f"{pt} {pnames.get(k + 1, '')}".strip() for k, pt in enumerate(params)],
                                     attributes=cas.get((0x06, m), [])))
        if row in props_of:
            for p in range(*props_of[row]):
                pr = P[p - 1]
                acc = {s: M[mm - 1]["Name"] for s, mm in sem.get((0x17, p), [])}
                t["properties"].append(dict(name=pr["Name"], type=md.prop_sig(md.blob(pr["Type"])),
                                            get=0x02 in acc, set=0x01 in acc))
        if row in events_of:
            for ev in range(*events_of[row]):
                er = E[ev - 1]
                t["events"].append(dict(name=er["Name"], type=md.tdor_name(er["EventType"])))
        for f in range(*frange[i]):
            fr = F[f - 1]
            fd = dict(name=fr["Name"], type=md.field_sig(md.blob(fr["Signature"])), flags=hex(fr["Flags"]))
            c = consts.get((0x04, f))
            if c:
                ctype, cb = c
                fmtc = {0x08: "<i", 0x09: "<I", 0x02: "<?", 0x04: "<b", 0x05: "<B", 0x06: "<h", 0x07: "<H",
                        0x0A: "<q", 0x0B: "<Q"}.get(ctype)
                fd["value"] = struct.unpack(fmtc, cb)[0] if fmtc else cb.hex()
            t["fields"].append(fd)
        types.append(t)
    return dict(file=path, metadata_version=md.version, mvid=md.guid(md.t("Module")[0]["Mvid"]),
                table_rows={TABLE_NAMES[k]: v for k, v in md.rows.items()}, types=types)


def render_txt(out):
    L = [f"# {out['file']}  ({out['metadata_version']}, MVID {out['mvid']})", ""]
    for t in out["types"]:
        hdr = f"{t['kind']} {t['name']}"
        if t["extends"] and t["kind"] == "class":
            hdr += f" : {t['extends']}"
        L.append(hdr)
        if t["guid"]:
            L.append(f"    [Guid {t['guid']}]")
        for a in t["attributes"]:
            L.append(f"    [{a['attr']} {a['args']}]")
        for i in t["interfaces"]:
            L.append(f"    implements {i['interface']}" + (f"  {i['attrs']}" if i["attrs"] else ""))
        if t["kind"] == "enum":
            for f in t["fields"]:
                if "value" in f:
                    L.append(f"    {f['name']} = {f['value']}")
        elif t["kind"] == "struct":
            for f in t["fields"]:
                L.append(f"    field {f['type']} {f['name']}")
        for p in t["properties"]:
            L.append(f"    prop {p['type']} {p['name']} {{{' get;' if p['get'] else ''}{' set;' if p['set'] else ''} }}")
        for e in t["events"]:
            L.append(f"    event {e['type']} {e['name']}")
        for m in t["methods"]:
            if t["kind"] == "class" and m["name"].startswith(("get_", "put_", "add_", "remove_")):
                continue
            L.append(f"    {m['ret']} {m['name']}({', '.join(m['params'])})")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    out = dump(sys.argv[1])
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    if len(sys.argv) > 3:
        open(sys.argv[3], "w").write(render_txt(out))
    print(f"{len(out['types'])} tipos; linhas: {out['table_rows']}")
