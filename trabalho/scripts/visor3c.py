#!/usr/bin/env python3
"""Previsões numéricas da Fase 3c: valor 'verdadeiro' (Decimal, 80 dígitos) + formatação do visor
reproduzindo NumberToString 0x1801300f0 (lido na 3a/3c): trunca para P+2 dígitos (FUN_180130060),
arredonda meia unidade para cima na posição P (ou P+e quando -2<=e<=0 com fração longa), notação
científica se e>P ou (fração longa e e<-2), remove zeros à direita e separador final; agrupamento
de milhar só na parte inteira e só fora da notação científica (pt-BR: ',' decimal, '.' milhar).
Uso: python3 -I visor3c.py  -> imprime a tabela de previsões e a margem até a fronteira de arredondamento."""
from decimal import Decimal as D, getcontext, ROUND_DOWN
getcontext().prec = 90

def pi():
    # Machin
    def atan_inv(n):
        x = D(1) / n; x2 = x * x; s = x; t = x; k = 1
        while True:
            t *= -x2; k += 2; d = t / k
            if abs(d) < D(10) ** -88: return s
            s += d
    return 4 * (4 * atan_inv(5) - atan_inv(239))
PI = pi()

def sin(x):
    s = x; t = x; k = 1
    while True:
        t *= -x * x / ((k + 1) * (k + 2)); k += 2
        if abs(t) < D(10) ** -88: return s
        s += t
def cos(x): return sin(PI / 2 - x)
def exp(x):
    s = D(1); t = D(1); k = 0
    while True:
        k += 1; t *= x / k
        if abs(t) < D(10) ** -88: return s
        s += t
def ln(x): return x.ln()
def atan(x):  # |x|<=1
    if abs(x) > D("0.5"):
        return 2 * atan(x / (1 + (1 + x * x).sqrt()))
    s = x; t = x; k = 1
    while True:
        t *= -x * x; k += 2; d = t / k
        if abs(d) < D(10) ** -88: return s
        s += d
def asin(x): return atan(x / (1 - x * x).sqrt())
def acos(x): return PI / 2 - asin(x)

def digitos(x, n):
    """(sinal, string de dígitos truncada a n significativos sem zeros à direita, e=nº de dígitos inteiros)"""
    neg = x < 0; x = abs(x)
    if x == 0: return neg, "0", 1
    t = x.as_tuple(); s = "".join(map(str, t.digits)).lstrip("0")
    e = len(t.digits) + t.exponent - (len("".join(map(str, t.digits))) - len(s))
    s = s[:n].rstrip("0") or "0"
    return neg, s, e

def visor(x, P=32, fe=False):
    neg, ds, e = digitos(D(x), P + 2)
    if ds == "0":
        return "0,e+0" if fe else "0"
    cd = len(ds); i21 = min(cd, P)
    rnd = (P <= cd) or (P < i21 - e and e > -3)
    modo = 1 if fe else 0
    pos = P
    if modo == 0 and P < e: modo = 1
    if modo == 0:
        if (P < i21 - e) or (P + 3 < e):
            if e < -2: modo = 1
            else: pos = P + e
    if rnd and cd > pos:
        n = int(ds[:pos]) + (1 if int(ds[pos]) >= 5 else 0)
        novo = D(n).scaleb(e - pos)
        return visor(-novo if neg else novo, P, fe)
    ds = ds[:pos]
    sinal = "-" if neg else ""
    if modo == 1:
        txt = ds[0] + "," + ds[1:] + "e" + ("+" if e - 1 >= 0 else "-") + str(abs(e - 1))
        return sinal + txt
    if e <= 0:
        txt = "0," + "0" * (-e) + ds
    else:
        ip = (ds[:e] + "0" * max(0, e - len(ds)))
        fr = ds[e:]
        g = ""
        while len(ip) > 3: g = "." + ip[-3:] + g; ip = ip[:-3]
        txt = ip + g + ("," + fr if fr else "")
    return sinal + txt

def margem(x, P=32):
    """dígitos 33..42 do valor verdadeiro (para ver a distância à fronteira de arredondamento)"""
    neg, ds, e = digitos(D(x), 60)
    ds = ds.ljust(60, "0")
    return ds[P:P + 10]

RAD = lambda g: D(g) * PI / 180
GRAD = lambda g: D(g) * PI / 200
CASOS_B = [
    ("sen 30° (DEG)", sin(RAD(30))),
    ("cos 60° (DEG)", cos(RAD(60))),
    ("sen 45° (DEG)", sin(RAD(45))),
    ("tan 45° (DEG)", sin(RAD(45)) / cos(RAD(45))),
    ("sen 90° (DEG)", sin(RAD(90))),
    ("sen 1 (RAD)", sin(D(1))),
    ("cos 1 (GRAD)", cos(GRAD(1))),
    ("tan 1 (RAD)", sin(D(1)) / cos(D(1))),
    ("sen -280° (DEG; = sen(-1e100 mod 360))", sin(RAD(-280))),
    ("asen 0,5 (DEG)", asin(D("0.5")) * 180 / PI),
    ("acos 0,5 (RAD)", acos(D("0.5"))),
    ("atan 1 (GRAD)", atan(D(1)) * 200 / PI),
    ("pi", PI),
    ("pi F-E", PI),
    ("e (Euler)", exp(D(1))),
    ("e^1", exp(D(1))),
    ("e^-10", exp(D(-10))),
    ("ln 10", ln(D(10))),
    ("log 2", ln(D(2)) / ln(D(10))),
    ("log 1000", ln(D(1000)) / ln(D(10))),
    ("10^0,5", D(10).sqrt()),
    ("2^0,5", D(2).sqrt()),
    ("27 yroot 3", D(3)),
    ("-8 yroot 3", D(-2)),
    ("8 logy 2", ln(D(8)) / ln(D(2))),
    ("0,5!", PI.sqrt() / 2),
]
if __name__ == "__main__":
    for nome, v in CASOS_B:
        print(f"{nome:42s} {visor(v, fe=nome.endswith('F-E')):45s} dígitos 33-42: {margem(v)}")
    print("--- exatos (bloco A) ---")
    for nome, v in [("1/3", D(1) / 3), ("2/3", D(2) / 3), ("2/30", D(2) / 30), ("1/300", D(1) / 300),
                    ("1/3000", D(1) / 3000), ("10^31", D(10) ** 31), ("10^32", D(10) ** 32),
                    ("20!", D(2432902008176640000)), ("25!", D(15511210043330985984000000)),
                    ("2000", D(2000)), ("1e-4", D("0.0001")), ("123 F-E", D(123)), ("1024", D(1024)),
                    ("1e100", D(10) ** 100), ("-1e100", -D(10) ** 100), ("0,5", D("0.5")), ("1,5", D("1.5"))]:
        print(f"{nome:42s} {visor(v, fe=nome.endswith('F-E'))}")
