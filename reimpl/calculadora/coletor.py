"""Coletor de histórico/expressão do motor (motor+0xf70).

Base documental: 02a §3.3 e §6 (tokens), 02b §4.1–4.2 (gravação e texto do histórico), 02c §3.11–3.12
(parênteses e troca de operador).

Cada token guarda o texto e, para operandos, o valor (usado só para refazer a expressão numa base nova,
FUN_180110180, 02d §1). O texto bruto é a junção das peças por um espaço (FUN_180128000); um binário são três
peças `" "`, `op`, `" "`, o que dá `7   +   5 =` (confirmado pelo UIA na 3b).
"""


class Token:
    __slots__ = ('tipo', 'texto', 'valor')

    def __init__(self, tipo, texto, valor=None):
        self.tipo, self.texto, self.valor = tipo, texto, valor

    def pecas(self):
        return [' ', self.texto, ' '] if self.tipo == 'bin' else [self.texto]


class Coletor:
    def __init__(self):
        self.limpar()

    def limpar(self):
        self.tokens = []
        self.operando = None   # +0xf8c: índice do operando corrente (None = −1)
        self.parenteses = []   # índices dos `(` abertos

    def texto(self, tokens=None):
        pecas = [p for t in (self.tokens if tokens is None else tokens) for p in t.pecas()]
        return ' '.join(pecas)

    def copia(self):
        return list(self.tokens)

    # ------------------------------------------------------------ operandos
    def operando_novo(self, texto, valor=None):
        """FUN_18010eae0 / FUN_180110560: operando criado a partir do texto do visor."""
        self.operando = len(self.tokens)
        self.tokens.append(Token('opnd', texto, valor))

    def trocar_operando(self, texto, valor=None):
        if self.operando is not None:
            del self.tokens[self.operando:]
        self.operando_novo(texto, valor)

    def remover_operando(self):
        """FUN_18010ff50."""
        if self.operando is not None:
            del self.tokens[self.operando:]
        self.operando = None

    # ------------------------------------------------------------ operadores
    def binario(self, texto):
        """FUN_18010ec10: tokens " ", op, " "; zera o operando corrente."""
        self.tokens.append(Token('bin', texto))
        self.operando = None

    def trocar_binario(self, texto):
        for i in range(len(self.tokens) - 1, -1, -1):
            if self.tokens[i].tipo == 'bin':
                self.tokens[i] = Token('bin', texto)
                return

    def remover_binario(self):
        if self.tokens and self.tokens[-1].tipo == 'bin':
            self.tokens.pop()

    def envolver_tudo(self):
        """FUN_18010f090: `(` no início do trecho e `)` no fim (02c §3.11). [I] "trecho" = tokens depois do último
        `(` ainda aberto, ou a expressão inteira."""
        ini = self.parenteses[-1] + 1 if self.parenteses else 0
        self.tokens.insert(ini, Token('abre', '('))
        self.tokens.append(Token('fecha', ')'))

    def unario(self, prefixo):
        """FUN_18010f200 / FUN_1801107e0: `prefixo(` antes do operando e `)` depois; o operando passa a ser o
        conjunto (permite `sqr( sqr( 9 ) )`)."""
        i = self.operando
        self.tokens.insert(i, Token('un', prefixo + '('))
        self.tokens.append(Token('fecha', ')'))
        self.operando = i

    def abre(self):
        self.parenteses.append(len(self.tokens))
        self.tokens.append(Token('abre', '('))
        self.operando = None

    def fecha(self):
        ini = self.parenteses.pop() if self.parenteses else 0
        self.tokens.append(Token('fecha', ')'))
        self.operando = ini

    def igual(self, texto):
        self.tokens.append(Token('igual', texto))
