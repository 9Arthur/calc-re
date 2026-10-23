"""Textos do motor (`CEngineStrings`) e a regra de escolha do texto por comando.

Fonte dos valores: tabela `trabalho/pri/CEngineStrings.tsv` (EN-US) e `trabalho/ptbr/CEngineStrings.tsv` (PT-BR),
citadas em 01 §7.1–7.2 como a extração do `resources.pri`. Regras: 02a §7 (consulta por nome da chave, chave
ausente → ""; texto de erro = chave (código & 0xFFFF) + 99), 02a §7.3 (mapa de exceções), 02d §3.4 (Mod = `%` no
modo inteiro) e L17 (no Windows pt-BR só as 9 mensagens de erro são traduzidas; os símbolos ficam em EN-US).
"""
from .comandos import C

EN_US = {
    '2': 'CE', '4': '.', '6': 'AND', '7': 'OR', '8': 'XOR', '9': 'Lsh', '10': 'Rsh', '11': '÷', '12': '×',
    '13': '+', '14': '-', '15': 'Mod', '16': 'yroot', '17': '^', '18': 'Int', '19': 'RoL', '20': 'RoR',
    '21': 'NOT', '22': 'sin', '23': 'cis', '24': 'tan', '25': 'sinh', '26': 'cosh', '27': 'tanh', '28': 'ln',
    '29': 'log', '30': '√', '35': 'dms', '37': '10^', '38': '%', '40': 'Pi', '41': '=', '47': 'Exp', '48': '(',
    '49': ')', '66': 'frac', '67': 'sin₀', '68': 'cos₀', '69': 'tan₀', '70': 'sin₀⁻¹', '71': 'cos₀⁻¹',
    '72': 'tan₀⁻¹', '73': 'sinᵣ', '74': 'cosᵣ', '75': 'tanᵣ', '76': 'sinᵣ⁻¹', '77': 'cosᵣ⁻¹', '78': 'tanᵣ⁻¹',
    '79': 'sin₉', '80': 'cos₉', '81': 'tan₉', '82': 'sin₉⁻¹', '83': 'cos₉⁻¹', '84': 'tan₉⁻¹', '85': 'sinh⁻¹',
    '86': 'cosh⁻¹', '87': 'tanh⁻¹', '88': 'e^', '89': '10^', '90': '√', '91': 'sqr', '92': 'cube', '94': 'fact',
    '95': '1/', '96': 'degrees', '97': 'negate',
    '99': 'Cannot divide by zero', '100': 'Invalid input', '101': 'Result is undefined', '105': 'Not enough memory',
    '107': 'Overflow', '108': 'Result not defined', '118': 'Result not defined', '119': 'Overflow',
    '120': 'Overflow',
    'Abs': 'abs', 'Ceil': 'ceil', 'Floor': 'floor', 'CubeRoot': 'cuberoot', 'TwoPowX': '2^', 'LogBaseY': 'log base',
    'Nand': 'NAND', 'Nor': 'NOR', 'ProgrammerMod': '%',
    'SecDeg': 'sec₀', 'SecRad': 'secᵣ', 'SecGrad': 'sec₉', 'InverseSecDeg': 'sec₀⁻¹', 'InverseSecRad': 'secᵣ⁻¹',
    'InverseSecGrad': 'sec₉⁻¹', 'CscDeg': 'csc₀', 'CscRad': 'cscᵣ', 'CscGrad': 'csc₉', 'InverseCscDeg': 'csc₀⁻¹',
    'InverseCscRad': 'cscᵣ⁻¹', 'InverseCscGrad': 'csc₉⁻¹', 'CotDeg': 'cot₀', 'CotRad': 'cotᵣ', 'CotGrad': 'cot₉',
    'InverseCotDeg': 'cot₀⁻¹', 'InverseCotRad': 'cotᵣ⁻¹', 'InverseCotGrad': 'cot₉⁻¹',
    'Sech': 'sech', 'InverseSech': 'sech⁻¹', 'Csch': 'csch', 'InverseCsch': 'csch⁻¹', 'Coth': 'coth',
    'InverseCoth': 'coth⁻¹',
}

ERROS_PT_BR = {'99': 'Não é possível dividir por zero', '100': 'Entrada inválida', '101': 'Resultado indefinido',
               '105': 'Memória insuficiente', '107': 'Estouro', '108': 'Resultado não definido',
               '118': 'Resultado não definido', '119': 'Estouro', '120': 'Estouro'}

# Mapa de exceções dos unários (02a §7.3): (normal, inversa) ou, se depende do ângulo,
# ((DEG normal, DEG inv), (RAD normal, RAD inv), (GRAD normal, GRAD inv)).
_TRIG = {C.SIN: (67, 70, 73, 76, 79, 82), C.COS: (68, 71, 74, 77, 80, 83), C.TAN: (69, 72, 75, 78, 81, 84)}
_RECIP = {C.SEC: 'Sec', C.CSC: 'Csc', C.COT: 'Cot'}
_UNARIOS = {
    C.INT: (None, '66'), C.SINH: (None, '85'), C.COSH: (None, '86'), C.TANH: (None, '87'), C.LN: (None, '88'),
    C.SQR: ('91', None), C.CUBE: ('92', None), C.FACT: ('94', None), C.INVERT: ('95', None),
    C.DMS: (None, '96'), C.DEGREES: ('96', '96'), C.NEGATE: ('97', None),
    C.SECH: ('Sech', 'InverseSech'), C.CSCH: ('Csch', 'InverseCsch'), C.COTH: ('Coth', 'InverseCoth'),
    C.TWOPOWX: ('TwoPowX', None), C.ABS: ('Abs', None), C.FLOOR: ('Floor', None), C.CEIL: ('Ceil', None),
    C.ROLC: ('19', None), C.RORC: ('20', None), C.CUBEROOT: ('CubeRoot', None),
}
_BINARIOS = {C.NAND: 'Nand', C.NOR: 'Nor', C.RSHL: '10', C.LOGBASEY: 'LogBaseY'}


class Textos:
    """`unordered_map<wstring, wstring>` global do motor, carregado só com chaves de texto não vazio (02a §7.1)."""

    def __init__(self, idioma='pt-BR'):
        self.mapa = dict(EN_US)
        if idioma.lower() == 'pt-br':
            self.mapa.update(ERROS_PT_BR)

    def __getitem__(self, chave):
        return self.mapa.get(str(chave), '')  # chave ausente → "" (02a §7.1)

    def erro(self, codigo):
        return self[(codigo & 0xFFFF) + 99]

    def binario(self, cmd, inteiro=False):
        """FUN_180116bf0: mapa de exceções; senão to_wstring(código − 80). Mod no modo inteiro = ProgrammerMod."""
        if cmd == C.MOD and inteiro:
            return self['ProgrammerMod']
        return self[_BINARIOS.get(cmd, cmd - 80)]

    def unario(self, cmd, inv, angulo):
        """FUN_1801168e0: variantes normal/inversa e DEG/RAD/GRAD; entrada vazia → to_wstring(código − 80)."""
        if cmd in _TRIG:
            chave = _TRIG[cmd][2 * angulo + (1 if inv else 0)]
        elif cmd in _RECIP:
            nome = _RECIP[cmd] + ('Deg', 'Rad', 'Grad')[angulo]
            chave = ('Inverse' + nome) if inv else nome
        elif cmd in _UNARIOS:
            normal, inversa = _UNARIOS[cmd]
            chave = inversa if inv else normal
        else:
            chave = None
        texto = self[chave] if chave else ''
        return texto or self[cmd - 80]
