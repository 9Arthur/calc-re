"""Teste diferencial fora da amostra: gera 100 sequências aleatórias de teclas por modo (Padrão, Científico,
Programador) com semente fixa e grava relatorio/03-diferencial-casos.json.

Regras (pedido do usuário, 2026-10-23):
- 3 a 15 teclas por sequência, pelo menos um operador binário, a última tecla é `=`;
- só teclas de features da reimplementação; excluídos DMS, Degrees, Rand, conversão de unidades e o que está em L31
  (sec/csc/cot, sech/csch/coth, hiperbólicas inversas; ⌫ no expoente; 0⁰). As demais decisões de L31 dependem do
  valor (arredondamento com e > 0, limite dos racionais) e não têm filtro sintático: são marcadas na comparação.

Uma tecla = um clique lógico (um dígito, um operador, uma função mesmo que a automação abra um submenu, R:<base>,
TAM). A notação é a de reimpl/calculadora/teclas.py e de trabalho/automacao/rodar-casos.ps1 (Etapa Diferencial).

Uso: python3 -I trabalho/diferencial/gerar_casos.py [--semente N] [--saida relatorio/X.json] [--prefixo dif]
"""
import argparse
import hashlib
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / 'relatorio' / '03-diferencial-casos.json'
SEMENTE = 20261023
N_POR_MODO = 100

DIGITOS10 = [str(d) for d in range(10)]
DIG_BASE = {'HEX': '0123456789ABCDEF', 'DEC': '0123456789', 'OCT': '01234567', 'BIN': '01'}

# (tecla, peso). Os dígitos entram como grupo com peso total.
PADRAO = {
    'digito': 40,
    'binario': [('+', 4), ('-', 4), ('*', 4), ('/', 4)],
    'outras': [('DEC', 3), ('NEG', 3), ('BS', 3), ('CE', 2), ('C', 1),
               ('%', 3), ('SQRT', 3), ('SQR', 3), ('INV', 3), ('=', 3),
               ('MS', 2), ('MR', 2), ('M+', 2), ('M-', 2), ('MC', 1)],
}
_UN_CI = ['SQR', 'SQRT', 'INV', 'ABS', 'FACT', 'P10', 'LOG', 'LN', 'EX', 'SIN', 'COS', 'TAN', 'ASIN', 'ACOS',
          'ATAN', 'SINH', 'COSH', 'TANH', 'CUBE', 'CBRT', '2^X', 'FLOOR', 'CEIL']
CIENTIFICO = {
    'digito': 36,
    'binario': [('+', 3), ('-', 3), ('*', 3), ('/', 3), ('POW', 2), ('MOD', 2), ('YROOT', 1), ('LOGY', 1)],
    'outras': [('DEC', 3), ('NEG', 3), ('BS', 2), ('C', 1), ('PI', 1.5), ('E', 1.5), ('EXP', 2), ('(', 3), (')', 3),
               ('FE', 1), ('=', 2), ('MS', 1), ('MR', 1), ('M+', 1), ('M-', 1), ('MC', 1)]
              + [(u, 0.8) for u in _UN_CI],
}
PROG_BIN = [('+', 3), ('-', 3), ('*', 3), ('/', 3), ('%', 2), ('AND', 1.5), ('OR', 1.5), ('XOR', 1.5),
            ('NAND', 1.5), ('NOR', 1.5)]
PROG_DESL = {'Arit': [('LSH', 2), ('RSH', 2)], 'Log': [('LSH', 2), ('RSH', 2)],
             'Circ': [('ROL', 2), ('ROR', 2)], 'Carry': [('ROLC', 2), ('RORC', 2)]}
PROG_OUTRAS = [('NOT', 2), ('NEG', 3), ('BS', 3), ('C', 1), ('(', 2), (')', 2), ('=', 2), ('R:', 3), ('TAM', 2)]
BINARIOS = {'+', '-', '*', '/', '%', 'POW', 'MOD', 'YROOT', 'LOGY', 'AND', 'OR', 'XOR', 'NAND', 'NOR', 'LSH', 'RSH'}


def escolher(rng, pares):
    total = sum(p for _, p in pares)
    x = rng.random() * total
    for t, p in pares:
        x -= p
        if x < 0:
            return t
    return pares[-1][0]


def gerar_sequencia(rng, modo, preparo):
    n = rng.randint(3, 15)
    base = preparo.get('base')
    passos = []
    for _ in range(n - 1):
        if modo == 'programador':
            pares = [('digito', 40)] + PROG_BIN + PROG_DESL[preparo['deslocamento']] + PROG_OUTRAS
        else:
            tab = PADRAO if modo == 'padrao' else CIENTIFICO
            pares = [('digito', tab['digito'])] + tab['binario'] + tab['outras']
        t = escolher(rng, pares)
        if t == 'digito':
            t = '#' + rng.choice(DIG_BASE[base]) if modo == 'programador' else rng.choice(DIGITOS10)
        elif t == 'R:':
            base = rng.choice([b for b in DIG_BASE if b != base])
            t = 'R:' + base
        passos.append(t)
    passos.append('=')
    return passos


def _corrida_de_zeros_antes(passos, i):
    """True se a entrada imediatamente antes de passos[i] é um número só de zeros (0, 00, 0,0 …)."""
    j, viu = i - 1, False
    while j >= 0 and passos[j] in DIGITOS10 + ['DEC']:
        if passos[j] in DIGITOS10:
            if passos[j] != '0':
                return False
            viu = True
        j -= 1
    return viu


def motivo_rejeicao(passos):
    if not any(t in BINARIOS for t in passos[:-1]):
        return 'sem operador binário'
    if 'EXP' in passos and 'BS' in passos[passos.index('EXP'):]:
        return 'L31: ⌫ depois de Exp'
    for i, t in enumerate(passos):
        if t == 'POW' and _corrida_de_zeros_antes(passos, i):
            return 'L31: base 0 em xʸ (0⁰)'
    return None


def gerar(semente, prefixo='dif'):
    rng = random.Random(semente)
    casos, rejeitadas = [], {}
    for modo, sigla in (('padrao', 'Pd'), ('cientifico', 'Ci'), ('programador', 'Pr')):
        k = 0
        while k < N_POR_MODO:
            if modo == 'cientifico':
                preparo = {'angulo': rng.choice(['DEG', 'RAD', 'GRAD'])}
            elif modo == 'programador':
                preparo = {'base': rng.choice(list(DIG_BASE)), 'tamanho': rng.choice(['QWORD', 'DWORD', 'WORD', 'BYTE']),
                           'deslocamento': rng.choice(list(PROG_DESL))}
            else:
                preparo = {}
            passos = gerar_sequencia(rng, modo, preparo)
            m = motivo_rejeicao(passos)
            if m:
                rejeitadas[f'{modo}: {m}'] = rejeitadas.get(f'{modo}: {m}', 0) + 1
                continue
            k += 1
            casos.append({'id': f'{prefixo}-{sigla}-{k:03d}', 'modo': modo, 'preparo': preparo, 'passos': passos,
                          'n_teclas': len(passos)})
    return casos, rejeitadas


def sha256_arvore(pasta):
    h = hashlib.sha256()
    for p in sorted(pasta.rglob('*.py')):
        if '__pycache__' in p.parts:
            continue
        h.update(f'{p.relative_to(pasta).as_posix()}\0{hashlib.sha256(p.read_bytes()).hexdigest()}\n'.encode())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--semente', type=int, default=SEMENTE)
    ap.add_argument('--saida', default=str(SAIDA.relative_to(RAIZ)))
    ap.add_argument('--prefixo', default='dif')
    a = ap.parse_args()
    casos, rejeitadas = gerar(a.semente, a.prefixo)
    dif = Path(__file__).resolve().parent
    doc = {
        'descricao': 'Teste diferencial fora da amostra: Calculadora real (UIA) × reimplementação (reimpl/)',
        'gerado_em': datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'),
        'semente': a.semente,
        'gerador': {'arquivo': 'trabalho/diferencial/gerar_casos.py',
                    'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'python': platform.python_version(), 'rng': 'random.Random(semente), Mersenne Twister'},
        'reimplementacao_congelada': {
            'pasta': 'reimpl/calculadora',
            'sha256_arvore': sha256_arvore(RAIZ / 'reimpl' / 'calculadora'),
            'regra_do_hash': 'sha256 de "caminho\\0sha256(arquivo)\\n" para cada *.py em ordem, sem __pycache__'},
        'ferramentas_de_comparacao': {
            p: hashlib.sha256((dif / p).read_bytes()).hexdigest() for p in ('rodar_reimpl.py', 'comparar.py')},
        'alfabeto': {'padrao': PADRAO, 'cientifico': CIENTIFICO,
                     'programador': {'digito': 'dígitos válidos na base corrente, peso 40', 'binario': PROG_BIN,
                                     'deslocamento_por_opcao': PROG_DESL, 'outras': PROG_OUTRAS}},
        'exclusoes': ['DMS, Degrees, Rand (não reimplementados)', 'conversão de unidades (L30)',
                      'sec/csc/cot, sech/csch/coth e hiperbólicas inversas (L31)', '⌫ depois de Exp (L31)',
                      'xʸ com base digitada só de zeros (L31: 0⁰)', 'histórico (clique em item, L22), teclado de bits',
                      'CE no Científico e no Programador (divide a posição com C)',
                      'memória no Programador (sem MR no painel)'],
        'rejeitadas_por_motivo': rejeitadas,
        'criterio': {
            'leitura_real': 'só UIA: visor = NormalOutput (RawView); erro = plusButton.IsEnabled == False; sem capturas '
                            'nem transcrição',
            'leitura_reimpl': 'visor = Calculadora.visor; erro = Calculadora.em_erro',
            'acerto': 'visor idêntico (texto exato) E estado de erro igual',
            'preparo': 'calculadora limpa no modo do caso (C, memória vazia, F-E/2nd/hyp desligados) com o ângulo, a '
                       'base, o tamanho e a opção de deslocamento do caso',
            'tecla_desabilitada': 'a automação não pressiona botão desabilitado e registra; a reimplementação faz o '
                                  'que teclas.pressionar faz',
            'classes_de_divergencia': ['bug da reimplementação', 'lacuna de documentação', 'desvio do motor numérico (3f)',
                                       'problema da automação'],
            'taxa': 'primeira passada, por modo, sobre os 100 casos; casos com falha da automação também à parte'},
        'casos': casos,
    }
    saida = RAIZ / a.saida
    saida.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{len(casos)} casos -> {saida}; rejeitadas: {rejeitadas}')


if __name__ == '__main__':
    sys.exit(main())
