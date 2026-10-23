"""Engine do CalcManager: `ProcessCommand` (0x180112db0) e as rotinas que ele chama.

Base documental: 02a §2–§6 (estado, entrada, CE/C, binários, `=`, unárias, erros, limpeza da expressão),
02b §3.1 e §4.1 (memória da engine, gravação de histórico H1–H4), 02c §1–§4 (INV, ângulo, unárias científicas,
precedência, parênteses, F-E, Exp, π/e), 02d §1–§3 (modo inteiro: truncamento, base, tamanho, bits, deslocamentos,
÷/Mod). Os comentários citam a seção; "[I]" marca o que a reimplementação teve de decidir sem documento.

Uma engine por modo, criada pelo CalculatorManager com `precedencia` (+0x00) e `inteiro` (+0x01) (01 §6.6).
A saída é um objeto com a interface ICalcDisplay (01 §6.5), aqui com nomes em português.
"""
from fractions import Fraction

from .coletor import Coletor
from .comandos import (BINARIOS, BINPOS, C, DIGITOS, INVERSAS, PRECEDENCIA, UNARIOS, UNARIOS_H3)
from .entrada import Entrada
from .formatacao import agrupar, estourou, inteiro_para_texto, numero_para_texto
from . import numerico as N
from .numerico import ErroMotor

MARCA = None  # marcador 0 que `(` empilha na pilha de precedência (02c §2)
LIMITE_PILHA = 25

# Comandos que não finalizam o número em digitação (02a §3.1, 02b §3.1, 02c §3.8, 02d §1)
_MANTEM_DIGITACAO = DIGITOS | {C.DECIMAL, C.BACKSPACE, C.EXP, C.CLEAR, C.CLEARENTRY, C.INV}
_DOMINIO_TRIG = set(range(102, 108)) | set(range(400, 412))           # x < 10¹⁰⁰ (02c §3.1, passo 5)
_DESLIGA_INV = {98, 115, 324} | set(range(102, 109)) | set(range(400, 412))  # 02c §1
_UNARIOS_INTEIRO = {C.NOT, C.ROL, C.ROR, C.ROLC, C.RORC, C.NEGATE}
# `(` depois destes comandos executa × antes (ProcessCommand l. 2024, 02c §3.12): dígitos 0x82–0x91, unárias
# 0x62–0x76 e 400–417, separador 0x54, `)` 0x81. Sem ± (0x50) e sem Degrees (0x144).
_ANTES_DE_PARENTESE = DIGITOS | set(range(0x62, 0x77)) | set(range(400, 418)) | {C.DECIMAL, C.CLOSEP}
_UNARIOS_REAIS = {C.NEGATE, C.SQRT, C.SQR, C.CUBE, C.CUBEROOT, C.INVERT, C.FACT, C.POW10, C.TWOPOWX, C.LN,
                  C.LOG, C.SIN, C.COS, C.TAN, C.SINH, C.COSH, C.TANH, C.SEC, C.CSC, C.COT, C.SECH, C.CSCH,
                  C.COTH, C.ABS, C.FLOOR, C.CEIL, C.INT}


class NaoReimplementado(Exception):
    """Comando cuja semântica não está documentada no relatorio/ (ex.: DMS, Degrees, Rand)."""


class Motor:
    def __init__(self, precedencia, inteiro, textos, saida, historico=None, sep_decimal=',', sep_milhar='.'):
        self.precedencia = precedencia   # +0x00
        self.inteiro = inteiro           # +0x01
        self.textos = textos
        self.saida = saida
        self.historico = historico       # CalculatorHistory do modo (None no Programador)
        self.sep_decimal, self.sep_milhar = sep_decimal, sep_milhar
        self.radix = 10                  # +0xe24
        self.precisao = 32               # +0xe28
        self.tamanho = 0                 # +0xf50 (0 = QWORD)
        self.largura = 64                # +0xf54
        self.cientifico = False          # +0x90 (F-E)
        self.angulo = 0                  # +0xf4c: 0 DEG, 1 RAD, 2 GRAD
        self.inv = False                 # +0xe21
        self.erro = False                # +0xe20
        self.registro = None             # +0xd8: registrador de memória da engine
        self.flag_mr = False             # +0x22 [I] o documento não diz quem o liga; fica sempre 0
        self.carry = 0                   # +0xf68
        self.entrada = Entrada()         # +0x28
        self.coletor = Coletor()         # +0xf70
        self.atual = Fraction(0)         # +0x120
        self.acumulador = Fraction(0)    # +0x160
        self.ultimo_rhs = Fraction(0)    # +0xe0
        self.texto = '0'                 # +0xe48 (texto do visor, sem agrupamento)
        self.max_digitos = 32            # +0xe2c
        self._limpar()

    # ================================================================ utilidades
    @property
    def mascara(self):
        return (1 << self.largura) - 1

    def _truncar(self, v):
        """FUN_18012b790: parte inteira; negativo → complemento de dois; AND máscara (02d §3.1)."""
        return int(v) & self.mascara

    def _formatar(self, v):
        if self.inteiro:
            return inteiro_para_texto(self._truncar(v), self.radix, self.largura)
        return numero_para_texto(v, self.precisao, self.cientifico, self.sep_decimal)

    def agrupar(self, texto):
        return agrupar(texto, self.radix, self.sep_milhar, self.sep_decimal)

    def valor_corrente(self):
        """Valor que o painel do Programador mostra: o número digitado, se houver, senão o atual."""
        if self.digitando and not self.entrada.vazia:
            return self.entrada.valor(self.radix)
        return self.atual

    def _ajustar_max_digitos(self):
        """SetMaxDigits 0x18012d820 (02a §2, 02d §2)."""
        if not self.inteiro:
            self.max_digitos = self.precisao
        elif self.radix == 10:
            self.max_digitos = len(str(self.mascara >> 1)) - 1
        else:
            self.max_digitos = self.largura // {16: 4, 8: 3, 2: 1}[self.radix]

    def _cabe(self, texto, negativo):
        """Limite de digitação (FUN_180121670; 02a §3.1 e 02d §3.3)."""
        n = len(texto)
        if not self.inteiro:
            return n <= self.max_digitos + ('.' in texto) + texto.startswith('0')
        w = self.largura
        if self.radix == 16:
            return n <= w // 4
        if self.radix == 2:
            return n <= w
        if self.radix == 8:
            livre = w // 3
            return n <= livre or (n == livre + 1 and ((w % 3 == 1 and texto[0] == '1') or
                                                      (w % 3 == 2 and texto[0] < '4')))
        limite = self.mascara >> 1                       # texto-limite = int(máscara / 2) (02d §2)
        if n <= len(str(limite)) - 1:
            return True
        return n == len(str(limite)) and int(texto) <= limite + (1 if negativo else 0)

    def _mostrar_expressao(self):
        self.saida.expressao(self.coletor.copia())

    def _erro(self, codigo):
        """DisplayError 0x18012b640: texto = mapa[(código & 0xFFFF) + 99]; slots 0 e 1; motor+0xe20 = 1. A linha
        de expressão não é limpa (02a §4.1)."""
        self.erro = True
        self.saida.primario(self.textos.erro(codigo), True)

    def display_num(self):
        """DisplayNum 0x18012bb70: no modo inteiro trunca e grava de volta em +0x120 (02d §1); formata; em base 10
        testa o estouro (expoente de 5 dígitos, 02a §4.1); agrupa e manda ao visor."""
        if self.inteiro:
            self.atual = Fraction(self._truncar(self.atual))
        t = self._formatar(self.atual)
        if not self.inteiro and estourou(t):
            self._erro(N.ESTOURO)
            return False
        self.texto = t
        self.saida.primario(self.agrupar(t), False)
        return True

    def _mostrar_entrada(self):
        self.saida.primario(self.entrada.texto(self.radix, self.sep_decimal, self.sep_milhar), False)

    def _gravar_historico(self):
        """FUN_18010fb30: AddToHistory(tokens, texto do visor agrupado) sem filtro; depois esvazia o coletor
        (02b §4.1). Sem CalculatorHistory (Programador) só esvazia."""
        if self.historico is not None:
            item = self.historico.adicionar(self.coletor.texto(), self.agrupar(self.texto), self.coletor.copia())
            self.saida.historico_adicionado(item)
        self.coletor.limpar()

    # ================================================================ ProcessCommand
    def processar(self, cmd):
        cmd = int(cmd)
        if not self.operando_novo:                     # +0xe22 == 0 → FUN_180112c40 (02a §3.6)
            self.saida.expressao([])
        if self.erro:                                  # em erro só C passa; CE vira C (02a §4.4)
            if cmd == C.CLEARENTRY:
                cmd = C.CLEAR
            if cmd != C.CLEAR:
                return
        if self.digitando and cmd not in _MANTEM_DIGITACAO and not (cmd == C.NEGATE and self.radix == 10):
            self._finalizar()
        if cmd in DIGITOS:
            self._digito(cmd)
        elif cmd == C.DECIMAL:
            self._separador()
        elif cmd == C.BACKSPACE:
            if self.digitando:                         # fora da digitação ⌫ é ignorado (02a §3.1)
                self.entrada.apagar()
                self._mostrar_entrada()
        elif cmd == C.CLEARENTRY:
            self._ce()
        elif cmd == C.CLEAR:
            self._c()
        elif cmd == C.NEGATE and self.digitando and self.radix == 10:
            self.entrada.trocar_sinal()
            self._mostrar_entrada()
            self.ultimo = cmd
        elif cmd == C.EXP:
            if self.digitando and not self.inteiro:    # só digitando e fora do modo inteiro (02c §3.8)
                self.entrada.iniciar_expoente()
                self._mostrar_entrada()
        elif cmd == C.INV:
            self.inv = not self.inv
        elif cmd in (C.DEG, C.RAD, C.GRAD):
            self.angulo = cmd - C.DEG
            self.ultimo = cmd
        elif cmd == C.FTOE:
            self.cientifico = not self.cientifico
            self.display_num()
        elif cmd in (C.PI, C.EULER):
            self.atual = (N.DOIS_PI if self.inv else N.PI) if cmd == C.PI else N.E
            self.display_num()
            self.ultimo = cmd
        elif cmd in BINARIOS:
            self._binario(cmd)
        elif cmd == C.EQUALS:
            self._igual()
        elif cmd == C.OPENP:
            self._abre()
        elif cmd == C.CLOSEP:
            self._fecha()
        elif cmd in UNARIOS or cmd == C.NEGATE:
            self._unario(cmd)
        elif cmd in (C.MC, C.MR, C.MS, C.MPLUS, C.MMINUS):
            self._memoria(cmd)
        elif C.HEX <= cmd <= C.BIN:
            self._base_tamanho(base=cmd - C.HEX)
        elif C.QWORD <= cmd <= C.BYTE:
            self._base_tamanho(tamanho=cmd - C.QWORD)
        elif cmd in BINPOS:
            self._bit(cmd)
        else:
            raise NaoReimplementado(f'comando {cmd}')

    # ================================================================ entrada (02a §3.1)
    def _finalizar(self):
        """0x180121d50: texto → racional; vira o valor atual e passa pelo DisplayNum."""
        self.atual = self.entrada.valor(self.radix)
        self.digitando = False
        self.display_num()

    def _inicio_de_numero(self):
        """O que um dígito ou separador faz antes de começar um número novo."""
        if self.ultimo == C.CLOSEP:
            # número logo após `)`: × pendente com o resultado do parêntese como acumulador, sem empilhar nem
            # avaliar o pendente anterior; zera a pilha de precedência (02c §3.12)
            self.pendente, self.acumulador, self.ha_pendente = C.MULTIPLY, self.atual, True
            self.pilha = [x for x in self.pilha if x is MARCA]
            self.coletor.binario(self.textos.binario(C.MULTIPLY, self.inteiro))
            self._mostrar_expressao()
        elif self.coletor.operando is not None:
            if not self.ha_pendente and self.n_par == 0 and self.ultimo in UNARIOS_H3:
                self._gravar_historico()                 # H3 (02b §4.1): sem `=` e sem reexibir a linha
            else:
                self.coletor.remover_operando()
                self._mostrar_expressao()
        self.entrada.limpar()
        self.digitando = True

    def _digito(self, cmd):
        d = cmd - C.ZERO
        if d >= self.radix:                              # dígito só se d < base
            return
        if not self.digitando:
            self._inicio_de_numero()
        if not self.entrada.digito(d, self._cabe):
            self.saida.max_digitos()                     # ICalcDisplay slot 5; o visor não muda
            return
        self._mostrar_entrada()
        self.ultimo = cmd

    def _separador(self):
        if self.inteiro:
            return
        if not self.digitando:
            self._inicio_de_numero()
        self.entrada.separador()
        self._mostrar_entrada()
        self.ultimo = C.DECIMAL

    def _ce(self):
        """FUN_180112bc0: esvazia o buffer, liga "digitando", limpa o erro e mostra 0 (02a §3.2)."""
        self.entrada.limpar()
        self.digitando = True
        self.erro = False
        self.atual = Fraction(0)
        self.texto = '0'
        self.saida.primario('0', False)
        self.ultimo = C.CLEARENTRY

    def _limpar(self):
        self.pendente = 0          # +0x18
        self.anterior = 0          # +0x1c
        self.ha_pendente = False   # +0x20
        self.digitando = True      # +0x21
        self.operando_novo = True  # +0xe22
        self.ultimo = 0            # +0xf48
        self.pilha = []            # +0x7e0/+0xedc/+0xf40
        self.pilha_par = []        # +0x1a0/+0xe78
        self.n_par = 0             # +0xe70
        self.acumulador = Fraction(0)
        self.carry = 0             # o carry só é zerado pelo C (02d §2)
        self.coletor.limpar()

    def _c(self):
        """C (02a §3.2): zera acumulador, pendente, pilhas, parênteses (slot 3) e expressão; +0xe22 = 1; cai no CE."""
        self._limpar()
        self.saida.parenteses(0)
        self.saida.expressao([])
        self._ce()
        self.ultimo = C.CLEAR

    # ================================================================ binários (02a §3.3, 02c §3.11)
    def _operar(self, op, a, b):
        """DoOperation 0x180131140 com o try/catch interno: em erro chama DisplayError e devolve um operando."""
        try:
            return self._do(op, a, b)
        except ErroMotor as e:
            self._erro(e.codigo)
            return b

    def _do(self, op, a, b):
        if self.inteiro:
            return Fraction(self._do_inteiro(op, self._truncar(a), self._truncar(b)) & self.mascara)
        if op == C.ADD:
            return a + b
        if op == C.SUBTRACT:
            return a - b
        if op == C.MULTIPLY:
            return a * b
        if op == C.DIVIDE:
            return N.dividir(a, b)
        if op == C.MOD:
            return N.resto_cientifico(a, b)
        if op == C.POW:
            return N.potencia(a, b)
        if op == C.YROOT:
            return N.potencia(a, N.dividir(Fraction(1), b))   # x yroot y = x^(1/y)
        if op == C.LOGBASEY:
            return N.log_base(a, b)
        raise NaoReimplementado(f'binário {op} fora do modo inteiro')

    def _do_inteiro(self, op, x, y):
        """Ramos do modo inteiro de DoOperation (02d §3.4–3.6). [I] O resultado é truncado logo aqui; no binário
        a truncagem vem do DisplayNum seguinte, o que dá o mesmo valor nos caminhos documentados."""
        w, m = self.largura, self.mascara
        if op == C.ADD:
            return x + y
        if op == C.SUBTRACT:
            return x - y
        if op == C.MULTIPLY:
            return x * y
        if op in (C.DIVIDE, C.MOD):
            sx, sy = (x >> (w - 1)) & 1, (y >> (w - 1)) & 1
            mx = ((x ^ m) + 1) if sx else x
            my = ((y ^ m) + 1) if sy else y
            if op == C.DIVIDE:
                q = Fraction(N.dividir(Fraction(mx), Fraction(my)))
                return -int(q) if sx != sy else int(q)
            if my == 0:
                raise ErroMotor(N.INDEFINIDO)              # x Mod 0 → "Resultado indefinido"
            r = mx % my
            return -r if sx else r                         # sinal do dividendo
        if op == C.AND:
            return x & y
        if op == C.OR:
            return x | y
        if op == C.XOR:
            return x ^ y
        if op == C.NAND:
            return (x & y) ^ m
        if op == C.NOR:
            return (x | y) ^ m
        if op in (C.LSH, C.RSH, C.RSHL):
            if y >= w:
                raise ErroMotor(N.NAO_DEFINIDO)            # n ≥ largura → "Resultado não definido"
            if op == C.LSH:
                return x << y
            r = x >> y
            if op == C.RSH and (x >> (w - 1)) & 1:
                r |= (m >> y) ^ m                          # estende o sinal
            return r
        raise NaoReimplementado(f'binário {op} no modo inteiro')

    def _binario(self, op):
        if self.ultimo in BINARIOS:
            self._trocar_operador(op)
            return
        if self.coletor.operando is None:
            self.coletor.operando_novo(self.texto, self.atual)
        if self.ha_pendente:
            if self.precedencia and PRECEDENCIA[op] > PRECEDENCIA[self.pendente]:
                par = (self.acumulador, self.pendente)
                if len(self.pilha) < LIMITE_PILHA:
                    self.pilha.append(par)
                else:                                      # B19: o 25º nível é sobrescrito (02a §8)
                    self.pilha[-1] = par
            else:
                self.atual = self._operar(self.pendente, self.acumulador, self.atual)
                self.anterior = self.pendente
                while (not self.erro and self.precedencia and self.pilha and self.pilha[-1] is not MARCA
                       and PRECEDENCIA[op] <= PRECEDENCIA[self.pilha[-1][1]]):
                    a, p = self.pilha.pop()
                    self.atual = self._operar(p, a, self.atual)
                    self.anterior = p
                if self.erro or not self.display_num():
                    return
                if not self.precedencia:
                    # `=` implícito do Padrão (02a §3.3 [Fase 4]; H2 em 02b §4.1)
                    self.coletor.igual(self.textos['41'])
                    self._mostrar_expressao()
                    self._gravar_historico()
                    self.coletor.operando_novo(self.texto, self.atual)
        self.saida.operador_binario()                      # slot 6
        self.acumulador = self.atual
        self.pendente = op
        self.ha_pendente = True
        self.operando_novo = True
        self.coletor.binario(self.textos.binario(op, self.inteiro))
        self._mostrar_expressao()
        self.ultimo = op

    def _trocar_operador(self, op):
        """Operador logo após operador: só troca o pendente e o token (02a §3.3). No Científico, se
        prec(substituído) ≤ prec(+0x1c) < prec(novo), põe `(`…`)` no trecho (L11, 02c §3.11)."""
        texto = self.textos.binario(op, self.inteiro)
        if (self.precedencia and self.anterior and
                PRECEDENCIA[self.pendente] <= PRECEDENCIA[self.anterior] < PRECEDENCIA[op]):
            self.anterior = 0
            self.coletor.remover_binario()
            self.coletor.envolver_tudo()
            self.coletor.binario(texto)
        else:
            self.coletor.trocar_binario(texto)
        self.pendente = op
        self._mostrar_expressao()
        self.ultimo = op

    # ================================================================ igual (02a §3.4)
    def _igual(self):
        while self.n_par > 0 and not self.erro:            # fecha todos os parênteses
            self._fecha()
        if self.erro:
            return
        repetido = not self.operando_novo                  # +0xe22 == 0
        if repetido:
            self.acumulador = self.atual
        if self.pendente:
            if repetido:
                # `=` repetido: atual = último rhs; a expressão é refeita como `visor op rhs =` (02a §3.6)
                if self.coletor.operando is None:
                    self.coletor.operando_novo(self.texto, self.atual)
                self.coletor.binario(self.textos.binario(self.pendente, self.inteiro))
                self.coletor.operando_novo(self._formatar(self.ultimo_rhs), self.ultimo_rhs)
                self.atual = self.ultimo_rhs
            else:
                self.ultimo_rhs = self.atual
                if self.coletor.operando is None:
                    self.coletor.operando_novo(self.texto, self.atual)
            self.atual = self._operar(self.pendente, self.acumulador, self.atual)
            while not self.erro and self.pilha:            # Científico: desempilha o que restou
                par = self.pilha.pop()
                if par is not MARCA:
                    self.atual = self._operar(par[1], par[0], self.atual)
            self.acumulador = self.atual
            self.operando_novo = False
            self.ha_pendente = False
        elif self.coletor.operando is None:                # sem pendente: só reexibe (e +0xe22 não muda)
            self.coletor.operando_novo(self.texto, self.atual)
        if self.erro or not self.display_num():
            return
        self.coletor.igual(self.textos['41'])
        self._mostrar_expressao()
        self._gravar_historico()                           # H1
        self.ultimo = C.EQUALS

    # ================================================================ parênteses (02c §3.12)
    def _abre(self):
        if self.n_par >= LIMITE_PILHA:
            return
        ultimo = self.ultimo
        if ultimo in _ANTES_DE_PARENTESE:                  # × real, com precedência (± não entra: 02c §3.12)
            self._binario(C.MULTIPLY)
            if self.erro:
                return
        # salva o operador só se há pendente (+0x20); senão 0, e o `)` restaura +0x20 = (op ≠ 0) (02c §3.12, B3)
        self.pilha_par.append((self.acumulador, self.pendente if self.ha_pendente else 0, self.ha_pendente))
        self.pilha.append(MARCA)
        self.acumulador, self.pendente, self.ha_pendente = Fraction(0), 0, False
        if ultimo in BINARIOS:                             # depois de operador binário, +0x120 = 0 (02c §3.12)
            self.atual = Fraction(0)
        self.n_par += 1
        self.coletor.abre()
        self._mostrar_expressao()
        self.saida.parenteses(self.n_par)
        self.ultimo = C.OPENP

    def _fecha(self):
        if self.n_par == 0:                                # `)` sem `(`: só o anúncio (slot 4)
            self.saida.sem_parentese()
            return
        if self.coletor.operando is None:
            self.coletor.operando_novo(self.texto, self.atual)
        if self.ha_pendente:
            self.atual = self._operar(self.pendente, self.acumulador, self.atual)
            self.anterior = self.pendente
        while not self.erro and self.pilha and self.pilha[-1] is not MARCA:
            a, p = self.pilha.pop()
            self.atual = self._operar(p, a, self.atual)
            self.anterior = p
        if self.erro:
            return
        if self.pilha:
            self.pilha.pop()                               # o marcador
        self.acumulador, self.pendente, self.ha_pendente = self.pilha_par.pop()
        self.n_par -= 1
        self.coletor.fecha()
        if not self.display_num():
            return
        self._mostrar_expressao()
        self.saida.parenteses(self.n_par)
        self.ultimo = C.CLOSEP

    # ================================================================ unárias (02a §3.5, 02c §3, 02d §3.4–3.5)
    def _unario(self, cmd):
        suportadas = _UNARIOS_INTEIRO if self.inteiro else _UNARIOS_REAIS
        if cmd != C.PERCENT and cmd not in suportadas:
            raise NaoReimplementado(f'unário {cmd}')
        if self.ultimo in BINARIOS:                        # `5 + √` usa o 5
            self.atual = self.acumulador
        if cmd == C.PERCENT:
            self._percentual()
            return
        inv = self.inv
        if self.coletor.operando is None:
            self.coletor.operando_novo(self.texto, self.atual)
        self.coletor.unario(self.textos.unario(cmd, inv, self.angulo))   # o token entra antes do cálculo
        self._mostrar_expressao()
        self.ultimo = cmd
        if cmd in _DOMINIO_TRIG and not self.atual < N.LIMITE_TRIG:     # comparação com sinal
            self.atual = Fraction(0)
            self.inv = False
            self._erro(N.ENTRADA_INVALIDA)
            return
        try:
            self.atual = self._funcao(cmd, self.atual, inv)
        except ErroMotor as e:                             # catch 0x180167c8d de SciCalcFunctions
            self._erro(e.codigo)
            return
        finally:
            if cmd in _DESLIGA_INV:
                self.inv = False
        self.display_num()

    def _percentual(self):
        """% (02a §3.5): com × ou ÷ pendente, x/100; senão x × (acumulador/100). Não gera token unário: o
        resultado entra como operando."""
        x = self.atual
        self.atual = x / 100 if self.pendente in (C.MULTIPLY, C.DIVIDE) else x * (self.acumulador / 100)
        if not self.display_num():
            return
        self.coletor.trocar_operando(self.texto, self.atual)
        self._mostrar_expressao()
        self.ultimo = C.PERCENT

    def _funcao(self, cmd, x, inv):
        """SciCalcFunctions 0x1801286f0."""
        if self.inteiro:
            w, m, v = self.largura, self.mascara, self._truncar(x)
            if cmd == C.NOT:
                return Fraction(v ^ m)                     # NOT = x XOR máscara
            if cmd == C.ROL:
                return Fraction(((v << 1) | ((v >> (w - 1)) & 1)) & m)
            if cmd == C.ROR:
                return Fraction(((v & 1) << (w - 1)) | (v >> 1))
            if cmd == C.ROLC:
                r = ((v << 1) | self.carry) & m
                self.carry = (v >> (w - 1)) & 1
                return Fraction(r)
            if cmd == C.RORC:
                r = (self.carry << (w - 1)) | (v >> 1)
                self.carry = v & 1
                return Fraction(r)
            if cmd == C.NEGATE:
                return -x
        P, ang = self.precisao, self.angulo
        if cmd == C.NEGATE:
            return -x
        if cmd == C.SQRT:
            return N.potencia(x, Fraction(1, 2))           # pow(x, 1/2)
        if cmd == C.SQR:
            return N.potencia(x, Fraction(2))
        if cmd == C.CUBE:
            return N.potencia(x, Fraction(3))
        if cmd == C.CUBEROOT:
            return N.potencia(x, Fraction(1, 3))
        if cmd == C.INVERT:
            return N.dividir(Fraction(1), x)               # 1 ÷ x
        if cmd == C.FACT:
            return N.fatorial(x)
        if cmd == C.POW10:
            return N.potencia(Fraction(10), x)
        if cmd == C.TWOPOWX:
            return N.potencia(Fraction(2), x)
        if cmd == C.LN:
            return N.exp(x) if inv else N.ln(x)
        if cmd == C.LOG:
            return N.log10(x)
        if cmd == C.SIN:
            return N.arco_seno(x, ang, P) if inv else N.seno(x, ang, P)
        if cmd == C.COS:
            return N.arco_cosseno(x, ang, P) if inv else N.cosseno(x, ang, P)
        if cmd == C.TAN:
            return N.arco_tangente(x, ang, P) if inv else N.tangente(x, ang, P)
        if cmd in (C.SINH, C.COSH, C.TANH):
            return N.hiperbolica({C.SINH: 'sinh', C.COSH: 'cosh', C.TANH: 'tanh'}[cmd], x, inv)
        if cmd in (C.SEC, C.CSC, C.COT):
            # [I] sec/csc/cot = 1/cos, 1/sen, 1/tan; inversas = arco da recíproca (não lidas)
            direta = {C.SEC: C.COS, C.CSC: C.SIN, C.COT: C.TAN}[cmd]
            if inv:
                return self._funcao(direta, N.dividir(Fraction(1), x), True)
            return N.dividir(Fraction(1), self._funcao(direta, x, False))
        if cmd in (C.SECH, C.CSCH, C.COTH):
            direta = {C.SECH: C.COSH, C.CSCH: C.SINH, C.COTH: C.TANH}[cmd]
            if inv:
                return self._funcao(direta, N.dividir(Fraction(1), x), True)
            return N.dividir(Fraction(1), self._funcao(direta, x, False))
        if cmd == C.ABS:
            return abs(x)                                  # case 0x19d (02c §3.7)
        if cmd == C.FLOOR:
            return Fraction(x.numerator // x.denominator)
        if cmd == C.CEIL:
            return Fraction(-((-x.numerator) // x.denominator))
        if cmd == C.INT:
            return x - N.trunc(x) if inv else N.trunc(x)
        raise NaoReimplementado(f'unário {cmd}')

    # ================================================================ memória da engine (02b §3.1)
    def _memoria(self, cmd):
        if cmd == C.MS:
            self.registro = Fraction(self._truncar(self.atual)) if self.inteiro else self.atual
        elif cmd == C.MC:
            self.registro = Fraction(0)
        elif cmd == C.MPLUS:
            r = (self.registro or 0) + self.atual
            self.registro = Fraction(self._truncar(r)) if self.inteiro else r
        elif cmd == C.MMINUS:
            r = (self.registro or 0) - self.atual
            self.registro = Fraction(self._truncar(r)) if self.inteiro else r
        elif cmd == C.MR:
            if self.coletor.operando is not None:
                if not self.ha_pendente and self.n_par == 0 and self.ultimo in UNARIOS_H3:
                    self._gravar_historico()               # H4: com o visor de antes do MR
                else:
                    self.coletor.remover_operando()
                    self._mostrar_expressao()
            if not self.flag_mr:
                self.atual = self.registro if self.registro is not None else Fraction(0)
            else:
                self.flag_mr = False
            self.display_num()
            self.ultimo = cmd

    # ================================================================ Programador (02d §3)
    def _bit(self, cmd):
        """FUN_18012d520: pos < largura → valor XOR 2^pos; logo depois de binário age sobre o acumulador."""
        if self.ultimo in BINARIOS:
            self.atual = self.acumulador
        pos = cmd - C.BINPOS0
        if pos < self.largura:
            self.atual = Fraction(self._truncar(self.atual) ^ (1 << pos))
        self.display_num()
        self.ultimo = cmd

    def _base_tamanho(self, base=None, tamanho=None):
        """FUN_18012d140 (02d §3.2): bit de sinal na largura antiga → valor negativo; grava base/tamanho;
        SetMaxDigits; DisplayNum (que trunca na largura nova). Na troca de base refaz a expressão (FUN_180110180)."""
        if self.inteiro:
            x = self._truncar(self.atual)
            self.atual = Fraction(-((x ^ self.mascara) + 1)) if (x >> (self.largura - 1)) & 1 else Fraction(x)
        if base is not None:
            self.radix = (16, 10, 8, 2)[base]
        if tamanho is not None:
            self.tamanho, self.largura = tamanho, (64, 32, 16, 8)[tamanho]
        self._ajustar_max_digitos()
        self.display_num()
        if base is not None and self.inteiro and self.coletor.tokens:
            for t in self.coletor.tokens:
                if t.tipo == 'opnd' and t.valor is not None:
                    t.texto = self._formatar(t.valor)
            self._mostrar_expressao()
