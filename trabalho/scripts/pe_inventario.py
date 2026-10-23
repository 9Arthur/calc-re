#!/usr/bin/env python3
"""Inventário estático de arquivos PE (somente leitura, biblioteca padrão).

Uso: python3 -I pe_inventario.py <dir_binarios> <saida.json>
Implementado a partir da especificação PE/COFF (Microsoft).
"""
import hashlib, json, os, re, struct, sys, datetime

MACHINES = {0x8664: "x64", 0x14c: "x86", 0xaa64: "arm64", 0x1c4: "arm"}
SUBSYS = {1: "native", 2: "windows_gui", 3: "windows_cui", 9: "wince_gui", 10: "efi_app"}
DIRS = ["export", "import", "resource", "exception", "security", "basereloc", "debug",
        "architecture", "globalptr", "tls", "load_config", "bound_import", "iat",
        "delay_import", "clr_runtime", "reserved"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class PE:
    def __init__(self, data):
        self.d = data
        if data[:2] != b"MZ":
            raise ValueError("sem MZ")
        self.e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if data[self.e_lfanew:self.e_lfanew + 4] != b"PE\0\0":
            raise ValueError("sem PE")
        c = self.e_lfanew + 4
        (self.machine, self.nsec, self.timestamp, _, _, self.opt_size,
         self.characteristics) = struct.unpack_from("<HHIIIHH", data, c)
        o = c + 20
        self.magic = struct.unpack_from("<H", data, o)[0]
        pe32p = self.magic == 0x20B
        if pe32p:
            self.entry = struct.unpack_from("<I", data, o + 16)[0]
            self.image_base = struct.unpack_from("<Q", data, o + 24)[0]
            self.subsystem, self.dllchar = struct.unpack_from("<HH", data, o + 68)
            nrva_off = o + 108
        else:
            self.entry = struct.unpack_from("<I", data, o + 16)[0]
            self.image_base = struct.unpack_from("<I", data, o + 28)[0]
            self.subsystem, self.dllchar = struct.unpack_from("<HH", data, o + 68)
            nrva_off = o + 92
        self.linker = (data[o + 2], data[o + 3])
        n = struct.unpack_from("<I", data, nrva_off)[0]
        self.dirs = {}
        for i in range(min(n, 16)):
            rva, size = struct.unpack_from("<II", data, nrva_off + 4 + 8 * i)
            self.dirs[DIRS[i]] = (rva, size)
        s = o + self.opt_size
        self.sections = []
        for i in range(self.nsec):
            name = data[s:s + 8].rstrip(b"\0").decode("latin-1")
            vsize, va, rsize, rptr = struct.unpack_from("<IIII", data, s + 8)
            ch = struct.unpack_from("<I", data, s + 36)[0]
            self.sections.append(dict(name=name, va=va, vsize=vsize, raw_ptr=rptr, raw_size=rsize, ch=ch))
            s += 40

    def off(self, rva):
        for sec in self.sections:
            if sec["va"] <= rva < sec["va"] + max(sec["vsize"], sec["raw_size"]):
                return rva - sec["va"] + sec["raw_ptr"]
        return None

    def cstr(self, rva):
        o = self.off(rva)
        if o is None:
            return None
        e = self.d.index(b"\0", o)
        return self.d[o:e].decode("latin-1")

    def imports(self):
        rva, size = self.dirs.get("import", (0, 0))
        res = []
        if not rva:
            return res
        o = self.off(rva)
        while True:
            oft, _, _, name_rva, ft = struct.unpack_from("<IIIII", self.d, o)
            if not (oft or name_rva or ft):
                break
            dll = self.cstr(name_rva)
            funcs = []
            t = self.off(oft or ft)
            ptrsz = 8 if self.magic == 0x20B else 4
            flag = 1 << (63 if ptrsz == 8 else 31)
            while t is not None:
                v = struct.unpack_from("<Q" if ptrsz == 8 else "<I", self.d, t)[0]
                if v == 0:
                    break
                if v & flag:
                    funcs.append("#%d" % (v & 0xFFFF))
                else:
                    funcs.append(self.cstr((v & 0x7FFFFFFF) + 2))
                t += ptrsz
            res.append(dict(dll=dll, functions=funcs))
            o += 20
        return res

    def delay_imports(self):
        rva, size = self.dirs.get("delay_import", (0, 0))
        res = []
        if not rva:
            return res
        o = self.off(rva)
        while True:
            attrs, name_rva, _, _, int_rva = struct.unpack_from("<IIIII", self.d, o)
            if not name_rva:
                break
            dll = self.cstr(name_rva)
            funcs = []
            t = self.off(int_rva)
            while t is not None:
                v = struct.unpack_from("<Q", self.d, t)[0]
                if v == 0:
                    break
                funcs.append("#%d" % (v & 0xFFFF) if v >> 63 else self.cstr((v & 0x7FFFFFFF) + 2))
                t += 8
            res.append(dict(dll=dll, functions=funcs))
            o += 32
        return res

    def exports(self):
        rva, size = self.dirs.get("export", (0, 0))
        if not rva:
            return None
        o = self.off(rva)
        (_, _, _, _, name_rva, base, nfunc, nnames, aof, aon, aoo) = struct.unpack_from("<IIHHIIIIIII", self.d, o)
        names = []
        no, oo, fo = self.off(aon), self.off(aoo), self.off(aof)
        for i in range(nnames):
            nrva = struct.unpack_from("<I", self.d, no + 4 * i)[0]
            ordi = struct.unpack_from("<H", self.d, oo + 2 * i)[0]
            frva = struct.unpack_from("<I", self.d, fo + 4 * ordi)[0]
            fwd = rva <= frva < rva + size
            names.append(dict(name=self.cstr(nrva), ordinal=base + ordi, rva=hex(frva),
                              forwarder=self.cstr(frva) if fwd else None))
        return dict(dll_name=self.cstr(name_rva), n_functions=nfunc, n_names=nnames, names=names)

    def debug(self):
        rva, size = self.dirs.get("debug", (0, 0))
        out = []
        if not rva:
            return out
        o = self.off(rva)
        for i in range(size // 28):
            (_, ts, _, _, typ, dsize, drva, dptr) = struct.unpack_from("<IIHHIIII", self.d, o + 28 * i)
            ent = dict(type=typ, size=dsize)
            if typ == 2 and self.d[dptr:dptr + 4] == b"RSDS":
                guid = self.d[dptr + 4:dptr + 20]
                age = struct.unpack_from("<I", self.d, dptr + 20)[0]
                pdb = self.d[dptr + 24:dptr + dsize].split(b"\0")[0].decode("utf-8", "replace")
                g = struct.unpack("<IHH8s", guid)
                ent.update(codeview="RSDS", pdb=pdb, age=age,
                           guid="%08X-%04X-%04X-%s" % (g[0], g[1], g[2], g[3].hex().upper()))
            out.append(ent)
        return out

    def clr(self):
        rva, size = self.dirs.get("clr_runtime", (0, 0))
        if not rva:
            return None
        o = self.off(rva)
        cb, maj, mnr, md_rva, md_size, flags = struct.unpack_from("<IHHIII", self.d, o)
        res = dict(runtime=f"{maj}.{mnr}", flags=hex(flags), metadata_size=md_size)
        mo = self.off(md_rva)
        if mo is not None and self.d[mo:mo + 4] == b"BSJB":
            vlen = struct.unpack_from("<I", self.d, mo + 12)[0]
            res["metadata_version"] = self.d[mo + 16:mo + 16 + vlen].split(b"\0")[0].decode()
        return res

    def version_info(self):
        """Extrai pares chave/valor de StringFileInfo procurando estruturas String UTF-16."""
        rsrc = next((s for s in self.sections if s["name"] == ".rsrc"), None)
        if not rsrc:
            return {}
        blob = self.d[rsrc["raw_ptr"]:rsrc["raw_ptr"] + rsrc["raw_size"]]
        i = blob.find("StringFileInfo".encode("utf-16-le"))
        if i < 0:
            return {}
        out = {}
        keys = ["CompanyName", "FileDescription", "FileVersion", "InternalName", "LegalCopyright",
                "OriginalFilename", "ProductName", "ProductVersion", "Comments"]
        for k in keys:
            kb = k.encode("utf-16-le") + b"\0\0"
            j = blob.find(kb, i)
            if j < 0:
                continue
            v = j + len(kb)
            v += (-v) % 4  # alinhamento DWORD relativo ao início da seção (alinhada)
            e = v
            while e + 1 < len(blob) and blob[e:e + 2] != b"\0\0":
                e += 2
            out[k] = blob[v:e].decode("utf-16-le", "replace")
        return out


def main():
    root, outp = sys.argv[1], sys.argv[2]
    result = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            ent = dict(file=rel, size=os.path.getsize(p), sha256=sha256(p))
            with open(p, "rb") as fh:
                data = fh.read()
            try:
                pe = PE(data)
            except Exception as e:
                ent["pe"] = None
                result.append(ent)
                continue
            ent["pe"] = dict(
                machine=MACHINES.get(pe.machine, hex(pe.machine)),
                magic="PE32+" if pe.magic == 0x20B else "PE32",
                is_dll=bool(pe.characteristics & 0x2000),
                timestamp=pe.timestamp,
                timestamp_utc=datetime.datetime.fromtimestamp(pe.timestamp, datetime.timezone.utc).isoformat(),
                linker="%d.%d" % pe.linker,
                subsystem=SUBSYS.get(pe.subsystem, pe.subsystem),
                dll_characteristics=hex(pe.dllchar),
                image_base=hex(pe.image_base),
                entry_rva=hex(pe.entry),
                sections=[dict(name=s["name"], vsize=s["vsize"], raw_size=s["raw_size"], ch=hex(s["ch"]))
                          for s in pe.sections],
                data_dirs={k: [hex(v[0]), v[1]] for k, v in pe.dirs.items() if v[0]},
                clr=pe.clr(),
                debug=pe.debug(),
                imports=pe.imports(),
                delay_imports=pe.delay_imports(),
                exports=pe.exports(),
                version=pe.version_info(),
            )
            result.append(ent)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)
    print("ok", len(result), "arquivos ->", outp)


if __name__ == "__main__":
    main()
