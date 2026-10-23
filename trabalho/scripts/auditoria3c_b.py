#!/usr/bin/env python3
"""Auditoria do bloco B da 3c (2026-10-23): para cada caso, de onde veio o número congelado e se o caso discrimina o motor.
Reusa visor3c.py (o mesmo código que gerou as previsões). Compara:
  exato_arred = valor exato arredondado corretamente (ROUND_HALF_EVEN) na mesma posição que a regra do visor usa;
  regra       = visor3c.visor() (trunca para 34 dígitos e arredonda meia unidade para cima, emulando NumberToString);
  margem      = distância dos dígitos 33+ do valor exato até a fronteira de arredondamento, em unidades da 32ª posição.
Um erro do motor só pode mudar o visor se for maior que a margem. Uso: python3 -I auditoria3c_b.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import visor3c as v
from decimal import Decimal as D

IDS = ['3c-50', '3c-51', '3c-52', '3c-53', '3c-54', '3c-55', '3c-56', '3c-57', '3c-58', '3c-59', '3c-60', '3c-61',
       '3c-62', '3c-63', '3c-64', '3c-65', '3c-66', '3c-67', '3c-68', '3c-69', '3c-70', '3c-71', '3c-72', '3c-73',
       '3c-74', '3c-75']
# CASOS_B de visor3c.py tem sen 90° (não usado no 03c) e não tem 3c-54 (-sen 30°) nem 3c-58 (sen 100 grad):
# remonta a lista na ordem dos IDs com as mesmas expressões.
B = dict(v.CASOS_B)
VAL = {'3c-50': B['sen 30° (DEG)'], '3c-51': B['cos 60° (DEG)'], '3c-52': B['sen 45° (DEG)'], '3c-53': B['tan 45° (DEG)'],
       '3c-54': -B['sen 30° (DEG)'], '3c-55': B['sen 1 (RAD)'], '3c-56': B['tan 1 (RAD)'], '3c-57': B['cos 1 (GRAD)'],
       '3c-58': v.sin(v.GRAD(100)), '3c-59': B['asen 0,5 (DEG)'], '3c-60': B['acos 0,5 (RAD)'], '3c-61': B['atan 1 (GRAD)'],
       '3c-62': B['sen -280° (DEG; = sen(-1e100 mod 360))'], '3c-63': B['pi'], '3c-64': B['e (Euler)'], '3c-65': B['e^1'],
       '3c-66': B['e^-10'], '3c-67': B['ln 10'], '3c-68': B['log 2'], '3c-69': B['log 1000'], '3c-70': B['10^0,5'],
       '3c-71': B['2^0,5'], '3c-72': B['27 yroot 3'], '3c-73': B['-8 yroot 3'], '3c-74': B['8 logy 2'], '3c-75': B['0,5!']}

def margem(x):
    neg, ds, e = v.digitos(abs(D(x)), 80)
    if ds == '0': return D('0.5')
    pos = 32 if e > 0 or e < -2 else 32 + e     # mesma posição de corte que visor() usa (fração longa com -2<=e<=0)
    resto = D('0.' + ds[pos:].ljust(40, '0')[:40])  # fração da unidade da última posição exibida
    return min(abs(resto - D('0.5')), D('0.5'))

def exato_arred(x):
    neg, ds, e = v.digitos(abs(D(x)), 80)
    if ds == '0': return v.visor(D(0))
    pos = 32 if e > 0 or e < -2 else 32 + e
    q = D(1).scaleb(e - pos)
    r = (abs(D(x))).quantize(q, rounding='ROUND_HALF_EVEN')
    return v.visor(-r if x < 0 else r)

if __name__ == '__main__':
    for i in IDS:
        x = VAL[i]
        a, b = v.visor(x), exato_arred(x)
        print(f"{i}\t{a}\t{'igual' if a == b else 'DIFERE: ' + b}\t{float(margem(x)):.3f}")
