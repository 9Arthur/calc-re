"""Teclas: a notação dos passos de `trabalho/automacao/rodar-casos.ps1` (usada nos testes) e apelidos para a CLI.

Um número com vários dígitos é um botão por dígito; `#1A3` idem, aceitando A–F (Programador).
"""
from .comandos import C, digito

# token → comando de OnButtonPressed
BOTOES = {
    'C': C.CLEAR, 'CE': C.CLEARENTRY, 'BS': C.BACKSPACE, '⌫': C.BACKSPACE, 'NEG': C.NEGATE, '±': C.NEGATE,
    'DEC': C.DECIMAL, ',': C.DECIMAL, '.': C.DECIMAL,
    '/': C.DIVIDE, '÷': C.DIVIDE, '*': C.MULTIPLY, '×': C.MULTIPLY, 'X': C.MULTIPLY, '-': C.SUBTRACT,
    '−': C.SUBTRACT, '+': C.ADD, '=': C.EQUALS, '%': C.PERCENT,
    'SQRT': C.SQRT, '√': C.SQRT, 'SQR': C.SQR, 'X²': C.SQR, 'INV': C.INVERT, '1/X': C.INVERT,
    'SIN': C.SIN, 'COS': C.COS, 'TAN': C.TAN, 'ASIN': C.INVSIN, 'ACOS': C.INVCOS, 'ATAN': C.INVTAN,
    'SINH': C.SINH, 'COSH': C.COSH, 'TANH': C.TANH, 'ASINH': C.INVSINH, 'ACOSH': C.INVCOSH, 'ATANH': C.INVTANH,
    'SEC': C.SEC, 'CSC': C.CSC, 'COT': C.COT, 'ASEC': C.INVSEC, 'ACSC': C.INVCSC, 'ACOT': C.INVCOT,
    'PI': C.PI, 'Π': C.PI, 'E': C.EULER, 'EXP': C.EXP, 'FACT': C.FACT, 'N!': C.FACT, 'MOD': C.MOD,
    'POW': C.POW, '^': C.POW, 'P10': C.POW10, '10^X': C.POW10, 'LOG': C.LOG, 'LN': C.LN, 'ABS': C.ABS,
    '(': C.OPENP, ')': C.CLOSEP, 'EX': C.EPOWX, 'E^X': C.EPOWX, 'YROOT': C.YROOT, 'LOGY': C.LOGBASEY,
    'CUBE': C.CUBE, 'X³': C.CUBE, 'CBRT': C.CUBEROOT, '2^X': C.TWOPOWX, 'FLOOR': C.FLOOR, 'CEIL': C.CEIL,
    'AND': C.AND, 'OR': C.OR, 'XOR': C.XOR, 'NAND': C.NAND, 'NOR': C.NOR, 'NOT': C.NOT,
    'ROL': C.ROL, 'ROR': C.ROR, 'ROLC': C.ROLC, 'RORC': C.RORC,
    'DMS': C.DMS, 'DEGREES': C.DEGREES, 'RAND': C.RAND,     # não reimplementados (semântica não documentada)
}

# nome do botão do modo Padrão (para conferir se está habilitado, como a automação fazia)
NOME_PADRAO = {C.CLEAR: 'C', C.CLEARENTRY: 'CE', C.BACKSPACE: '⌫', C.NEGATE: '±', C.DECIMAL: ',',
               C.DIVIDE: '÷', C.MULTIPLY: '×', C.SUBTRACT: '−', C.ADD: '+', C.EQUALS: '=', C.PERCENT: '%',
               C.SQRT: '√', C.SQR: 'x²', C.INVERT: '1/x'}
NOME_MEMORIA = {'MS': 'MS', 'MR': 'MR', 'M+': 'M+', 'M-': 'M−', 'M−': 'M−', 'MC': 'MC'}


class TeclaDesconhecida(ValueError):
    pass


def _numero(tok):
    corpo = tok[1:] if tok.startswith('#') else tok
    if tok.startswith('#'):
        ok = corpo != '' and all(c in '0123456789ABCDEF' for c in corpo.upper())
    else:
        ok = corpo.isdigit()
    return corpo.upper() if ok else None


def desabilitado(vm, tok):
    """Na UI um botão desabilitado não pode ser clicado (3a-09: `+` em erro "desabilitada, não pressionada").
    Padrão: estado_botoes (02a §4.4, 02b §8). Científico e Programador: memória como no Padrão (Calculator.xbf) e,
    em erro, os botões do ErrorLayout de cada painel (L19, correção pós-diferencial)."""
    t = tok.upper()
    if vm.modo == 'padrao':
        nome = NOME_MEMORIA.get(t) or (NOME_PADRAO.get(BOTOES[t]) if t in BOTOES else None)
        return nome is not None and not vm.estado_botoes().get(nome, True)
    if t in NOME_MEMORIA:
        return not vm.estado_botoes().get(NOME_MEMORIA[t], True)
    if not vm.em_erro:
        return False
    if vm.modo == 'programador' and (t == 'TAM' or t.startswith('W:')):
        return True                                       # Qword/Dword/Word/Byte: ErrorLayout do DisplayPanel
    if vm.modo == 'programador' and t == '%':
        cmd = C.MOD
    else:
        cmd = {'LSH': C.LSH, 'RSH': C.RSH}.get(t, BOTOES.get(t))
    return cmd is not None and vm.desabilitado_em_erro(cmd)


def pressionar(vm, tok):
    """Executa uma tecla. Devolve False se o botão estava desabilitado e não foi pressionado."""
    num = _numero(tok)
    if num is not None:
        for ch in num:
            vm.botao(digito(int(ch, 16)))
        return True
    t = tok.upper()
    if desabilitado(vm, t):
        return False
    if t in ('ALT1', 'ALT2', 'ALT4'):
        vm.definir_modo({'ALT1': 'padrao', 'ALT2': 'cientifico', 'ALT4': 'programador'}[t])
    elif t == 'MS':
        vm.memorizar()
    elif t == 'MR':
        vm.recuperar()
    elif t == 'M+':
        vm.memoria_somar()
    elif t in ('M-', 'M−'):
        vm.memoria_subtrair()
    elif t == 'MC':
        vm.memoria_limpar()
    elif t == 'LH':
        vm.limpar_historico()
    elif t == 'ANG':
        vm.ciclar_angulo()
    elif t.startswith('ANG:'):
        vm.definir_angulo(t[4:])
    elif t == 'FE':
        vm.alternar_fe()
    elif t.startswith('R:'):
        vm.definir_base(t[2:])
    elif t.startswith('W:'):
        vm.definir_tamanho(t[2:])
    elif t == 'TAM':
        vm.ciclar_tamanho()
    elif t.startswith('KB:'):
        vm.teclado_bits = t == 'KB:BITS'
    elif t.startswith('BIT') and t[3:].isdigit():
        vm.bit(int(t[3:]))
    elif t.startswith('DESL:'):
        vm.deslocamento = {'ARIT': 'Arit', 'LOG': 'Log', 'CIRC': 'Circ', 'CARRY': 'Carry'}[t[5:]]
    elif t in ('LSH', 'RSH'):
        if t == 'RSH':
            vm.botao(C.RSHL if vm.deslocamento == 'Log' else C.RSH)
        else:
            vm.botao(C.LSH)
    elif t == '%' and vm.modo == 'programador':
        vm.botao(C.MOD)                                    # no Programador o botão `%` é o Mod (modButton)
    elif t in BOTOES:
        vm.botao(BOTOES[t])
    else:
        raise TeclaDesconhecida(tok)
    return True
