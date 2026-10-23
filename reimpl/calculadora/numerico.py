"""Aritmética do motor: racionais exatos e funções transcendentais.

Base documental:
- 02a §2: o motor guarda cada valor como racional de precisão arbitrária (numerador/denominador). Aqui isso é
  `fractions.Fraction`, exato.
- 02a §3.3/§3.5, 02c §3, 02d §3: regras de cada operação, domínios e códigos de erro.
- L26 (04-lacunas): o algoritmo numérico do motor (π de 41 dígitos por asin(1/2)·6, séries de Taylor até ~10⁻¹²⁸,
  corte de precisão FUN_1801265d0, Γ de FUN_18013b1b0) **não foi emulado**. As funções transcendentais usam a
  biblioteca de alta precisão `mpmath` com TRABALHO_DPS dígitos e o resultado volta a racional exato do valor mpmath.
  Só as regras de domínio, de corte (|y| ≤ 10⁻ᴾ → 0) e de redução de ângulo seguem o que foi lido no binário.
"""
from fractions import Fraction
import math

import mpmath

TRABALHO_DPS = 120  # dígitos decimais de trabalho do mpmath (o visor usa no máximo 32 + 2)
LIMITE_DIGITOS_EXATOS = 50_000  # [I] acima disso a potência deixa de ser exata (guarda de memória)

# Códigos de erro do motor (02a §4.2): o texto é CEngineStrings[(código & 0xFFFF) + 99]
DIVISAO_POR_ZERO = 0      # 0x80000000
ENTRADA_INVALIDA = 1      # 0x80000001
INDEFINIDO = 2            # 0x80000002
SEM_MEMORIA = 7           # 0x80000007 (chave 106 ausente do PRI → texto vazio)
ESTOURO = 8               # 0x80000008
NAO_DEFINIDO = 9          # 0x80000009


class ErroMotor(Exception):
    """Equivalente ao `_CxxThrowException(&código)` das rotinas aritméticas (02a §4.1)."""

    def __init__(self, codigo):
        super().__init__(codigo)
        self.codigo = codigo


def _ctx():
    ctx = mpmath.mp.clone()
    ctx.dps = TRABALHO_DPS
    return ctx


MP = _ctx()


def para_mp(x):
    return MP.mpf(x.numerator) / x.denominator


def de_mp(v):
    """Racional exato do valor binário do mpmath."""
    v = MP.mpf(v)
    if not MP.isfinite(v):
        raise ErroMotor(ESTOURO)
    sinal, man, exp, bc = v._mpf_
    if man == 0:
        return Fraction(0)
    if abs(exp + bc) > 140_000:  # [I] |v| fora de 10^±42000: o DisplayNum daria Estouro (expoente de 5 dígitos)
        raise ErroMotor(ESTOURO)
    if sinal:
        man = -man
    return Fraction(man * (1 << exp)) if exp >= 0 else Fraction(man, 1 << -exp)


PI = de_mp(MP.pi)
DOIS_PI = 2 * PI
E = de_mp(MP.e)
LN10 = de_mp(MP.log(10))
LIMITE_TRIG = Fraction(10) ** 100  # motor+0x98 (02c §2)


def log10_abs(x):
    """Estimativa de log10|x| para x ≠ 0 (só para guardas de estouro)."""
    return (math.log10(abs(x.numerator)) if abs(x.numerator) < 10 ** 300 else x.numerator.bit_length() * 0.30103) - \
        (math.log10(x.denominator) if x.denominator < 10 ** 300 else x.denominator.bit_length() * 0.30103)


def trunc(x):
    """intrat: subtrai a parte fracionária, ou seja, trunca em direção a zero (02d §3.1)."""
    return Fraction(int(x))


# ---------------------------------------------------------------- operações básicas (02a §3.3)

def dividir(a, b):
    """divrat: x ÷ 0 → 0x80000000; 0 ÷ 0 → 0x80000002 (02a §4.2)."""
    if b == 0:
        raise ErroMotor(INDEFINIDO if a == 0 else DIVISAO_POR_ZERO)
    return a / b


def _raiz_exata(n, q):
    """Raiz q-ésima inteira de n ≥ 0 se for exata, senão None (Newton inteiro)."""
    if n < 2:
        return n
    if q > n.bit_length():                 # raiz inteira ≥ 2 exige q ≤ nº de bits de n
        return None
    x = 1 << -(-n.bit_length() // q)
    while True:
        y = ((q - 1) * x + n // x ** (q - 1)) // q
        if y >= x:
            break
        x = y
    return x if x ** q == n else None


def potencia(x, y):
    """powrat (02c §3.4, §3.11): potência inteira exata pelo numerador do expoente e raiz pelo denominador.

    [O] base negativa só com denominador ímpar do expoente; 0 elevado a negativo → Entrada inválida.
    [I] x⁰ = 1 e 0^y (y > 0) = 0: o documento só diz que base 0 e expoente 0 vão "para o caminho geral".
    [I] Guarda de estouro: |y·log10|x|| ≥ 10⁵ dá Estouro (o DisplayNum daria Estouro com expoente de 5 dígitos)."""
    if y == 0:
        return Fraction(1)
    if x == 0:
        if y < 0:
            raise ErroMotor(ENTRADA_INVALIDA)
        return Fraction(0)
    p, q = y.numerator, y.denominator
    if x < 0 and q % 2 == 0:
        raise ErroMotor(ENTRADA_INVALIDA)
    sinal = -1 if (x < 0 and p % 2 == 1) else 1
    if abs(x) == 1:
        return Fraction(sinal)
    try:
        estimativa = abs(log10_abs(x) * float(y))
    except OverflowError:
        estimativa = math.inf
    if estimativa >= 1e5:
        raise ErroMotor(ESTOURO)
    a = abs(x)
    bits = abs(p) * (a.numerator.bit_length() + a.denominator.bit_length())
    if bits > LIMITE_DIGITOS_EXATOS * 3.33:
        # [I] guarda de memória: o motor real limita os racionais à precisão (regra não documentada para as
        # operações básicas); aqui, acima do limite, a potência sai do mpmath em vez de exata
        return sinal * de_mp(MP.power(para_mp(a), MP.mpf(p) / q))
    if q == 1:
        r = a ** p if p > 0 else 1 / (a ** -p)
        return sinal * r
    rn, rd = _raiz_exata(a.numerator, q), _raiz_exata(a.denominator, q)
    if rn is not None and rd is not None:
        base = Fraction(rn, rd)
        return sinal * (base ** p if p > 0 else 1 / (base ** -p))
    return sinal * de_mp(MP.power(para_mp(a), MP.mpf(p) / q))


def resto_cientifico(x, y):
    """mod no Científico (02c §3.6): y = 0 → x; resto com o sinal do divisor (confirmado em 3c-16/17)."""
    if y == 0:
        return x
    return x - y * math.floor(x / y)


# ---------------------------------------------------------------- funções do modo científico (02c §3)

def ln(x):
    """lnrat: x ≤ 0 → Entrada inválida (02c §3.3)."""
    if x <= 0:
        raise ErroMotor(ENTRADA_INVALIDA)
    if x == 1:
        return Fraction(0)
    return de_mp(MP.log(para_mp(x)))


def log10(x):
    """log = ln(x) ÷ ln 10 (02c §3.3)."""
    return dividir(ln(x), LN10)


def exp(x):
    """eˣ (INV + ln). [I] Estouro quando o resultado passaria do expoente de 5 dígitos."""
    if abs(x) > 23000:
        raise ErroMotor(ESTOURO)
    return de_mp(MP.exp(para_mp(x)))


def log_base(x, y):
    """logᵧx = ln x ÷ ln y (02c §3.4)."""
    return dividir(ln(x), ln(y))


def fatorial(x):
    """02c §3.5: > 3249 ou < −1000 → Estouro; inteiro negativo → Entrada inválida; não inteiro → Γ(x + 1)."""
    if x > 3249 or x < -1000:
        raise ErroMotor(ESTOURO)
    if x.denominator == 1:
        if x < 0:
            raise ErroMotor(ENTRADA_INVALIDA)
        return Fraction(math.factorial(int(x)))
    return de_mp(MP.gamma(para_mp(x) + 1))


def _para_radianos(x, angulo):
    """Redução e conversão (02c §3.1): DEG mod 360 (truncado) e > 180 → −360; GRAD mod 400 e > 200 → −400;
    RAD mod 2π. A redução em DEG/GRAD é feita em racional exato."""
    if angulo == 0:
        r = x - 360 * trunc(x / 360)
        if r > 180:
            r -= 360
        return para_mp(r) * MP.pi / 180
    if angulo == 2:
        r = x - 400 * trunc(x / 400)
        if r > 200:
            r -= 400
        return para_mp(r) * MP.pi / 200
    v = para_mp(x)
    return MP.fmod(v, 2 * MP.pi)


def _corte(y, precisao):
    """Depois da série: limita a [−1, 1] e |y| ≤ 10⁻ᴾ vira 0 exato (02c §3.1, passo 3)."""
    if y > 1:
        y = MP.mpf(1)
    elif y < -1:
        y = MP.mpf(-1)
    if abs(y) <= MP.mpf(10) ** (-precisao):
        return Fraction(0)
    return de_mp(y)


def seno(x, angulo, precisao):
    return _corte(MP.sin(_para_radianos(x, angulo)), precisao)


def cosseno(x, angulo, precisao):
    return _corte(MP.cos(_para_radianos(x, angulo)), precisao)


def tangente(x, angulo, precisao):
    """tan = sen/cos, ambos com o corte; cosseno zero → Entrada inválida (02c §3.1, passo 4)."""
    s, c = seno(x, angulo, precisao), cosseno(x, angulo, precisao)
    if c == 0:
        raise ErroMotor(ENTRADA_INVALIDA)
    return s / c


def _de_radianos(v, angulo):
    """Inversas: resultado em radianos e, em DEG, ÷ 2π × 360; em GRAD, ÷ 2π × 400 (02c §3.2)."""
    if angulo == 0:
        v = v / (2 * MP.pi) * 360
    elif angulo == 2:
        v = v / (2 * MP.pi) * 400
    return de_mp(v)


def arco_seno(x, angulo, precisao):
    """asinrat: ||x| − 1| ≤ 10⁻ᴾ → ±π/2 exato; |x| > 1 → Entrada inválida (02c §3.2)."""
    eps = Fraction(1, 10 ** precisao)
    if abs(abs(x) - 1) <= eps:
        return _de_radianos(MP.pi / 2 * (1 if x > 0 else -1), angulo)
    if abs(x) > 1:
        raise ErroMotor(ENTRADA_INVALIDA)
    return _de_radianos(MP.asin(para_mp(x)), angulo)


def arco_cosseno(x, angulo, precisao):
    """[I] Mesmo domínio do asen (só o asen foi lido em detalhe)."""
    eps = Fraction(1, 10 ** precisao)
    if abs(abs(x) - 1) <= eps:
        return Fraction(0) if x > 0 else _de_radianos(MP.pi, angulo)
    if abs(x) > 1:
        raise ErroMotor(ENTRADA_INVALIDA)
    return _de_radianos(MP.acos(para_mp(x)), angulo)


def arco_tangente(x, angulo, precisao):
    return _de_radianos(MP.atan(para_mp(x)), angulo)


def hiperbolica(nome, x, inversa):
    """[I] sinh/cosh/tanh e inversas: o documento só lista os comandos e o domínio x < 10¹⁰⁰ (02c §3.1)."""
    v = para_mp(x)
    try:
        if not inversa:
            r = {'sinh': MP.sinh, 'cosh': MP.cosh, 'tanh': MP.tanh}[nome](v)
        else:
            if nome == 'cosh' and v < 1 or nome == 'tanh' and abs(v) >= 1:
                raise ErroMotor(ENTRADA_INVALIDA)
            r = {'sinh': MP.asinh, 'cosh': MP.acosh, 'tanh': MP.atanh}[nome](v)
    except OverflowError:
        raise ErroMotor(ESTOURO)
    return de_mp(r)
