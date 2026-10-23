"""Objeto de entrada do motor (motor+0x28…): o número em digitação.

Base documental: 02a §3.1 (dígito, separador, ⌫, ±, limite de dígitos), 02c §3.8 (Exp e texto do expoente),
02d §3.3 (limites no modo inteiro).
"""
from fractions import Fraction

from .formatacao import DIGITOS, agrupar


class Entrada:
    def __init__(self):
        self.limpar()

    def limpar(self):
        self.mantissa = ''     # dígitos e '.', sem sinal
        self.negativo = False  # +0x88 (sinal do texto)
        self.no_expoente = False
        self.expoente = ''
        self.exp_negativo = False

    @property
    def vazia(self):
        return self.mantissa == ''

    # ------------------------------------------------------------ edição
    def digito(self, d, limites):
        """FUN_180121670. Devolve False quando o limite foi atingido (o motor anuncia "máximo de dígitos")."""
        ch = DIGITOS[d]
        if self.no_expoente:
            if len(self.expoente) >= 4:            # expoente: no máximo 4 dígitos (02a §3.1)
                return False
            if self.expoente or ch != '0':     # [I] zero à esquerda do expoente não entra (como na mantissa)
                self.expoente += ch
            return True
        if self.mantissa == '' and ch == '0':      # zero à esquerda não entra
            return True
        novo = self.mantissa + ch
        if not limites(novo, self.negativo):
            return False
        self.mantissa = novo
        return True

    def separador(self):
        """0x180121900: ignorado se já há separador ou no expoente; com o buffer vazio grava `0` antes."""
        if '.' in self.mantissa or self.no_expoente:
            return
        if self.mantissa == '':
            self.mantissa = '0'
        self.mantissa += '.'

    def apagar(self):
        """0x1801219b0: remove o último caractere; se sobra "0", remove também.
        [I] No expoente: apaga o último dígito do expoente; sem dígitos, sai do modo expoente."""
        if self.no_expoente:
            if self.expoente:
                self.expoente = self.expoente[:-1]
            else:
                self.no_expoente = False
            return
        self.mantissa = self.mantissa[:-1]
        if self.mantissa == '0':
            self.mantissa = ''

    def trocar_sinal(self):
        """± digitando em base 10: troca o sinal do texto, ou do expoente se estiver nele; com o buffer vazio só
        zera o sinal (02a §3.1, 02c §3.8)."""
        if self.no_expoente:
            self.exp_negativo = not self.exp_negativo
        elif self.mantissa == '':
            self.negativo = False
        else:
            self.negativo = not self.negativo

    def iniciar_expoente(self):
        """Exp (02c §3.8): chama o separador decimal e liga o modo expoente."""
        self.separador()
        self.no_expoente = True

    # ------------------------------------------------------------ leitura
    def valor(self, base):
        m = self.mantissa.rstrip('.') or '0'
        if base == 10:
            v = Fraction(m)
            if self.expoente:
                k = int(self.expoente)
                v *= Fraction(10) ** (-k if self.exp_negativo else k)
        else:
            v = Fraction(int(m, base))
        return -v if self.negativo else v

    def texto(self, base, sep_decimal=',', sep_milhar='.'):
        """Texto mostrado durante a digitação: mantissa agrupada, separador local e, no modo expoente,
        `e` + sinal + expoente (ou `0`), como em `2,e+0` (FUN_180121ad0)."""
        m = self.mantissa or '0'
        inteira, tem_sep, frac = m.partition('.')
        t = agrupar(inteira, base, sep_milhar)
        if tem_sep:
            t += sep_decimal + frac
        if self.negativo and self.mantissa:
            t = '-' + t
        if self.no_expoente:
            t += 'e' + ('-' if self.exp_negativo else '+') + (self.expoente or '0')
        return t
