"""Formatação do visor: NumberToString (0x1801300f0), versão inteira (0x180116f90) e agrupamento (0x18012c350).

Base documental: 02a §5, 02c §3.13, 02d §3.1, 02a §4.1 (teste de estouro do DisplayNum).
"""
import re

DIGITOS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # tabela 0x18018c410 (maiúsculas), 02d §3.1


def _digitos_truncados(x, n):
    """|x| = 0,d₁d₂…dₙ… × 10^e, d₁ ≠ 0. Devolve (n dígitos truncados, e). Só aritmética inteira, para aceitar
    números com dezenas de milhares de dígitos (3a-26 chega a 10^16383)."""
    p, q = abs(x.numerator), x.denominator

    def pelo_menos(k):  # |x| ≥ 10^k
        return p >= q * 10 ** k if k >= 0 else p * 10 ** -k >= q

    e = int((p.bit_length() - q.bit_length()) * 0.30102999566398120)
    while pelo_menos(e):
        e += 1
    while not pelo_menos(e - 1):
        e -= 1
    k = n - e
    m = p * 10 ** k // q if k >= 0 else p // (q * 10 ** -k)
    return str(m), e


def _arredondar(s, e, n):
    """Mantém n dígitos somando meia unidade na última casa (FUN_1801393b0); o vai-um pode aumentar e."""
    if len(s) <= n:
        return s, e
    if s[n] >= '5':
        m = str(int(s[:n]) + 1)
        if len(m) > n:
            e += 1
        s = m
    else:
        s = s[:n]
    return s.rstrip('0') or '0', e


def numero_para_texto(x, precisao, cientifico=False, sep=','):
    """NumberToString em base 10 (02c §3.13; 02a §5).

    1. trunca para P + 2 dígitos significativos e apaga zeros à direita (FUN_180130060);
    2. e = nº de dígitos inteiros; e > P → científica; casas fracionárias > P: com e < −2 científica, com
       −2 ≤ e ≤ 0 arredonda na casa P depois da vírgula;
    3. arredonda somando meia unidade e reformata se o vai-um mudou o número;
    4. científica: `d,` + resto + `e` + sinal + expoente; o separador fica mesmo sem resto (`1,e+16`).
    [I] Para e > 0, o arredondamento é para P dígitos significativos (o texto do documento só detalha e ≤ 0)."""
    if x == 0:
        return '0' + sep + 'e+0' if cientifico else '0'
    s, e = _digitos_truncados(x, precisao + 2)
    s = s.rstrip('0')
    return ('-' if x < 0 else '') + _montar(s, e, precisao, cientifico, sep)


def _montar(s, e, P, cientifico, sep):
    if not cientifico and e <= P:
        manter = P + min(e, 0)
        if len(s) > manter:
            if e < -2:
                cientifico = True
            else:
                s2, e2 = _arredondar(s, e, manter)
                return _montar(s2, e2, P, False, sep)
        else:
            if e <= 0:
                return '0' + sep + '0' * -e + s
            if len(s) <= e:
                return s + '0' * (e - len(s))
            return s[:e] + sep + s[e:]
    s, e = _arredondar(s, e, P)
    exp = e - 1
    return s[0] + sep + s[1:] + 'e' + ('+' if exp >= 0 else '-') + str(abs(exp))


def estourou(texto):
    """DisplayNum (02a §4.1): expoente com 5 ou mais dígitos → Overflow."""
    m = re.search(r'e[+-](\d+)$', texto)
    return bool(m and len(m.group(1)) >= 5)


def inteiro_para_texto(x, base, largura):
    """NumberToString no modo inteiro (0x180116f90): em base 10, bit w−1 ligado → −(2^w − x); nas outras bases,
    os bits sem sinal (02d §3.1). x já está truncado em [0, 2^w)."""
    if base == 10 and (x >> (largura - 1)) & 1:
        return '-' + str((1 << largura) - x)
    if x == 0:
        return '0'
    out = []
    while x:
        x, r = divmod(x, base)
        out.append(DIGITOS[r])
    return ''.join(reversed(out))


def agrupar(texto, base, sep_milhar='.', sep_decimal=','):
    """Agrupamento (0x18012c350, 02d §3.1): base 2 e 16 em grupos de 4, base 8 em grupos de 3, separador espaço
    (DAT_18017cb14 = U+0020); base 10 com o separador de milhar do idioma, grupos de 3 (pt-BR: `.`), só na parte
    inteira e fora da notação científica (02a §5)."""
    if 'e' in texto and base == 10:
        return texto
    neg = texto.startswith('-')
    corpo = texto[1:] if neg else texto
    if base == 10:
        inteira, sep, resto = corpo.partition(sep_decimal)
        tam, sepg = 3, sep_milhar
    else:
        inteira, sep, resto = corpo, '', ''
        tam, sepg = (3 if base == 8 else 4), ' '
    grupos = []
    while len(inteira) > tam:
        grupos.insert(0, inteira[-tam:])
        inteira = inteira[:-tam]
    grupos.insert(0, inteira)
    return ('-' if neg else '') + sepg.join(grupos) + sep + resto


def preencher_binario(texto):
    """FUN_1800d98a0 (02d §3.1): conta os caracteres ≠ espaço e acrescenta (4 − n mod 4) mod 4 zeros à esquerda do
    texto como está; `0` fica como está. Usada na linha BIN do painel e, desde a correção pós-diferencial, no visor
    em BIN (SetPrimaryDisplay → FUN_1800d2ee0), sem teste de erro: `0Resultado indefinido`."""
    if texto == '0':
        return texto
    n = len(texto) - texto.count(' ')
    return '0' * ((4 - n % 4) % 4) + texto
