"""StandardCalculatorViewModel (C++/CX) + o pouco do ApplicationViewModel (C#) que os casos exercitam.

Base documental: 01 §6.3 (OnButtonPressed), 01 §6.5 (ICalcDisplay → VM), 02a §4.4 (VM em erro; botões
desabilitados em erro, observado na Fase 4), 02b §3.3–§4.4 e §8 D1 (memória, histórico, `ErrorLayout`),
02c §1 (ângulo, F-E), 02d §1, §3.1–§3.2 (troca de base em erro, painel HEX/DEC/OCT/BIN, preenchimento da linha BIN,
ciclo do botão de tamanho Q→D→W→B→Q observado em caixa-preta, L27).
"""
from .comandos import BINPOS, C, DIGITOS
from .formatacao import agrupar, inteiro_para_texto, preencher_binario
from .gerenciador import Gerenciador
from .textos import Textos
from .coletor import Coletor

MODOS = ('padrao', 'cientifico', 'programador')
BASES = ('HEX', 'DEC', 'OCT', 'BIN')
TAMANHOS = ('QWORD', 'DWORD', 'WORD', 'BYTE')
ANGULOS = ('DEG', 'RAD', 'GRAD')

# Botões do modo Padrão cujo estado foi observado (02a §4.4, 02b §8)
SEMPRE_HABILITADOS = ['Navegação', 'Histórico', 'CE', 'C', '⌫', '=', *'0123456789', 'Sobrepor']
DESABILITADOS_EM_ERRO = ['%', '1/x', 'x²', '√', '÷', '×', '−', '+', ',', '±']


# Científico e Programador: comandos cujos botões o VisualState `ErrorLayout` desabilita (setters IsEnabled=False em
# CalculatorScientificOperators.xbf / CalculatorProgrammerRadixOperators.xbf e `,` em NumberPad.xbf; 04-lacunas L19).
# Funções de submenu ficam inacessíveis porque trigButton/funcButton/bitwiseButton/bitShiftButton e 2nd são desabilitados.
# Ângulo e F-E ficam habilitados: o setter de FtoeButton existe, mas o botão estava habilitado em erro (dif-Ci-061/088).
_DESAB_ERRO_CIENTIFICO = {C.ADD, C.SUBTRACT, C.MULTIPLY, C.DIVIDE, C.MOD, C.POW, C.YROOT, C.LOGBASEY,
                          C.SQR, C.CUBE, C.SQRT, C.CUBEROOT, C.POW10, C.TWOPOWX, C.LOG, C.LN, C.EPOWX, C.ABS, C.FACT,
                          C.INVERT, C.SIN, C.COS, C.TAN, C.INVSIN, C.INVCOS, C.INVTAN, C.SINH, C.COSH, C.TANH,
                          C.INVSINH, C.INVCOSH, C.INVTANH, *range(C.SEC, C.INVCOTH + 1), C.FLOOR, C.CEIL, C.RAND,
                          C.DMS, C.DEGREES, C.PI, C.EULER, C.EXP, C.OPENP, C.CLOSEP, C.NEGATE, C.DECIMAL}
_DESAB_ERRO_PROGRAMADOR = {C.ADD, C.SUBTRACT, C.MULTIPLY, C.DIVIDE, C.MOD, C.AND, C.OR, C.XOR, C.NAND, C.NOR, C.NOT,
                           C.LSH, C.RSH, C.RSHL, C.ROL, C.ROR, C.ROLC, C.RORC, C.OPENP, C.CLOSEP, C.NEGATE, C.DECIMAL}


class Calculadora:
    def __init__(self, modo='padrao', idioma='pt-BR'):
        self.textos = Textos(idioma)
        self.visor = '0'                  # DisplayValue
        self.em_erro = False              # IsInError (VM+0x68)
        self.tokens = []                  # ExpressionTokens
        self.n_parenteses = 0             # OpenParenthesisCount
        self.memoria = []                 # MemorizedNumbers (textos, mais novo primeiro)
        self.anuncios = []                # anúncios ao Narrador (máximo de dígitos, `)` sem `(`…)
        self.fe = False                   # IsFToEChecked
        self.angulo = 0                   # VM+0x148
        self.tamanho = 0                  # ValueBitLength (0 = QWORD)
        self.deslocamento = 'Arit'        # opção do submenu Bit-shift (UI, L27)
        self.teclado_bits = False         # teclado de bits visível (UI)
        self.cm = Gerenciador(self, self.textos)
        self.definir_modo(modo)

    # ================================================================ ICalcDisplay (01 §6.5)
    def primario(self, texto, erro):      # slots 0/1: SetPrimaryDisplay 0x1800d35b0
        # FUN_1800d2ee0: no Programador em BIN (vslot 0x428 == BinBase) o texto passa por FUN_1800d98a0, também em
        # erro (02d §3.1, correção pós-diferencial)
        if self.cm.modo == 'programador' and self.motor.radix == 2:
            texto = preencher_binario(texto)
        self.visor, self.em_erro = texto, erro

    def expressao(self, tokens):          # slot 2
        self.tokens = list(tokens)

    def parenteses(self, n):              # slot 3
        self.n_parenteses = n

    def sem_parentese(self):              # slot 4
        self.anuncios.append('NoRightParenthesisAdded')

    def max_digitos(self):                # slot 5
        self.anuncios.append('MaxDigitsReached')

    def operador_binario(self):           # slot 6
        pass

    def historico_adicionado(self, item):  # slot 7 (HistoryViewModel.OnHistoryItemAdded)
        pass

    def numeros_memorizados(self, textos):  # slot 8 (SetMemorizedNumbers)
        self.memoria = list(textos)

    def memoria_item_alterado(self, i):   # slot 9
        pass

    def entrada_alterada(self):           # slot 10
        pass

    # ================================================================ leitura
    @property
    def modo(self):
        return self.cm.modo

    @property
    def motor(self):
        return self.cm.motor

    @property
    def texto_expressao(self):
        return Coletor().texto(self.tokens)

    @property
    def historico(self):
        """Lista do HistoryViewModel: (expressão, resultado), mais novo em cima (InsertAt(0), 02b §4.3)."""
        return [(i.expressao, i.resultado) for i in self.cm.historico_atual.mais_novo_primeiro()]

    def estado_botoes(self):
        """Modo Padrão. Em erro: `%`, `1/x`, `x²`, `√`, operadores, `,`, `±` desabilitados (02a §4.4) e os cinco
        botões de memória pelo VisualState `ErrorLayout` (02b §8 D1). Fora de erro: MC, MR e M▾ seguem
        IsMemoryEmpty (02b §3.4). M▾ depende só de haver memória."""
        e, tem = self.em_erro, bool(self.cm.memoria)
        estado = {b: True for b in SEMPRE_HABILITADOS}
        estado.update({b: not e for b in DESABILITADOS_EM_ERRO})
        estado.update({'MC': tem and not e, 'MR': tem and not e, 'M+': not e, 'M−': not e, 'MS': not e,
                       'M▾': tem})
        return estado

    def desabilitado_em_erro(self, cmd):
        """Científico/Programador: o botão do comando está desabilitado agora? (ErrorLayout, L19)."""
        if not self.em_erro:
            return False
        if self.modo == 'cientifico':
            return int(cmd) in _DESAB_ERRO_CIENTIFICO
        if self.modo == 'programador':
            return int(cmd) in _DESAB_ERRO_PROGRAMADOR
        return False

    def linhas(self):
        """Painel do Programador (FUN_1800d9b20 → FUN_180116e10 por base; linha BIN por FUN_1800d98a0).
        Em erro as quatro linhas ficam vazias: FUN_1800d9b20 só as calcula se o vslot 0x350 (IsInError) devolve 0
        e, senão, grava as strings vazias [O, consulta da Fase 5, L29]."""
        m = self.motor
        if not m.inteiro:
            return {}
        if self.em_erro:
            return {'H': '', 'D': '', 'O': '', 'B': ''}
        v, w = m._truncar(m.valor_corrente()), m.largura
        return {'H': agrupar(inteiro_para_texto(v, 16, w), 16),
                'D': agrupar(inteiro_para_texto(v, 10, w), 10),
                'O': agrupar(inteiro_para_texto(v, 8, w), 8),
                'B': preencher_binario(agrupar(inteiro_para_texto(v, 2, w), 2))}

    def bits(self):
        """BinaryDigits: bits ligados do texto binário sem agrupamento (02d §3.7). [I] Em erro, o texto binário é
        vazio (L29), logo nenhum bit."""
        m = self.motor
        if self.em_erro:
            return set()
        v = m._truncar(m.valor_corrente())
        return {i for i in range(m.largura) if (v >> i) & 1}

    # ================================================================ ações
    def botao(self, cmd):
        """OnButtonPressed 0x1800d5aa0 (01 §6.3)."""
        cmd = int(cmd)
        if self.em_erro:
            # em erro: ProcessCommand(motor, Clear) direto; só continuam dígitos, separador, A–F e BINPOS
            self.motor.processar(C.CLEAR)
            if not (cmd in DIGITOS or cmd == C.DECIMAL or cmd in BINPOS):
                return
        if cmd == int(C.INV):
            self.memorizar()                               # na UI, 146 = Memory (MS)
            return
        if cmd in (C.CLEAR, C.CLEARENTRY, C.STANDARD, C.PROGRAMMER) and self.fe:
            self.fe = False                                # só a propriedade; nada vai ao motor (L25)
        if cmd in (C.DEG, C.RAD, C.GRAD):
            self.angulo = cmd - C.DEG
        self.cm.enviar(cmd)

    def definir_modo(self, modo):
        """[I] Troca de modo pelo ApplicationViewModel (C#, L3): SendCommand(200/201/209) sem passar pelo teste de
        erro de OnButtonPressed; ReloadHistory(modo) é implícito (a lista lê o histórico atual do CM)."""
        if modo not in MODOS:
            raise ValueError(modo)
        if modo in ('padrao', 'programador'):
            self.fe = False
        self.cm.enviar({'padrao': C.STANDARD, 'cientifico': C.SCIENTIFIC, 'programador': C.PROGRAMMER}[modo])
        if modo == 'programador':
            self.tamanho = self.motor.tamanho

    # memória (02b §3.3)
    def memorizar(self):                  # MS: OnMemoryButtonPressed 0x1800d6bf0
        self.cm.memorizar()

    def recuperar(self, pos=0):           # MR: OnMemoryItemPressed 0x1800d7350
        if self.cm.memoria and not self.motor.erro:
            self.cm.carregar(pos)
            self.motor.processar(C.MR)
            self.entrada_alterada()

    def memoria_somar(self, pos=0):       # M+: OnMemoryAdd 0x1800d76b0
        self.cm.somar(pos)

    def memoria_subtrair(self, pos=0):    # M−: OnMemorySubtract 0x1800d78f0
        self.cm.subtrair(pos)

    def memoria_limpar(self):             # MC: 0x1800d6680
        self.cm.limpar_memoria()

    def memoria_limpar_item(self, pos):   # OnMemoryClear 0x1800d7ac0
        self.cm.limpar_item(pos)

    def limpar_historico(self):           # OnClearCommand 0x1800b65a0: só a lista; nada vai ao motor
        self.cm.historico_atual.limpar()

    # Científico
    def ciclar_angulo(self):              # botão DEG/RAD/GRAD
        self.botao(C.DEG + (self.angulo + 1) % 3)

    def definir_angulo(self, nome):
        while ANGULOS[self.angulo] != nome:
            self.ciclar_angulo()

    def alternar_fe(self):                # FtoEButtonToggled 0x1800d5520 → OnButtonPressed(119)
        self.fe = not self.fe
        self.botao(C.FTOE)

    # Programador
    def definir_base(self, nome):
        """SwitchProgrammerModeBase 0x1800d8a40: em erro (vslot 0x350, [I] L28) manda Clear antes."""
        if self.em_erro:
            self.motor.processar(C.CLEAR)
        self.cm.enviar(C.HEX + BASES.index(nome))

    def ciclar_tamanho(self):
        """Botão de tamanho: Q→D→W→B→Q (observado, L27); set_ValueBitLength dispara o comando 317–320 (vslot 0x470,
        [I] L28)."""
        self.tamanho = (self.tamanho + 1) % 4
        self.cm.enviar(C.QWORD + self.tamanho)

    def definir_tamanho(self, nome):
        while TAMANHOS[self.tamanho] != nome:
            self.ciclar_tamanho()

    def bit(self, n):
        self.botao(C.BINPOS0 + n)
