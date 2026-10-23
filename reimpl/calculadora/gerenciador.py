"""CalculatorManager (VM+0x178) e CalculatorHistory.

Base documental: 01 §6.4 (SendCommand), 01 §6.6 (engines por modo, precisões, troca de modo), 02b §2–§4
(memória em CM+0x40, históricos de 20 itens por modo, MemorizeNumber/Load/Changed/Subtract/Clear).
"""
from .comandos import C, INVERSAS
from .motor import Motor

LIMITE_HISTORICO = 20   # CalculatorHistory+0x20 = 0x14 (02b §2)
LIMITE_MEMORIA = 100    # FUN_18010dd40 (02b §3.2)

# modo: (precedência, inteiro, precisão) — construtor da engine 0x180111bd0(eng, a, b, …) (01 §6.6)
MODOS = {'padrao': (False, False, 16), 'cientifico': (True, False, 32), 'programador': (True, True, 64)}
COMANDO_MODO = {C.STANDARD: 'padrao', C.SCIENTIFIC: 'cientifico', C.PROGRAMMER: 'programador'}


class ItemHistorico:
    """HISTORYITEM (0x60 bytes): tokens, comandos, expressão (+0x20) e resultado (+0x40)."""

    def __init__(self, expressao, resultado, tokens):
        self.expressao, self.resultado, self.tokens = expressao, resultado, tokens

    def __repr__(self):
        return f'[{self.expressao} | {self.resultado}]'


class Historico:
    """CalculatorHistory: AddToHistory com size ≥ 20 remove o mais antigo e faz push_back (02b §4.3)."""

    def __init__(self, limite=LIMITE_HISTORICO):
        self.limite = limite
        self.itens = []

    def adicionar(self, expressao, resultado, tokens):
        if len(self.itens) >= self.limite:
            self.itens.pop(0)
        item = ItemHistorico(expressao, resultado, tokens)
        self.itens.append(item)
        return item

    def limpar(self):
        self.itens.clear()

    def mais_novo_primeiro(self):
        return list(reversed(self.itens))


class Gerenciador:
    def __init__(self, saida, textos, sep_decimal=',', sep_milhar='.'):
        self.saida = saida
        self.textos = textos
        self.seps = (sep_decimal, sep_milhar)
        self.motores = {}
        self.motor = None
        self.modo = None
        self.memoria = []                                  # CM+0x40: racionais, mais novo primeiro
        self.historicos = {'padrao': Historico(), 'cientifico': Historico()}   # CM+0xa0 / CM+0xb0
        self.historico_atual = self.historicos['padrao']   # CM+0xc0
        self.fe = False                                    # CM+0x98
        self.angulo = 0                                    # CM+0x9c

    # ------------------------------------------------------------ SendCommand 0x18010d3d0
    def enviar(self, cmd):
        cmd = int(cmd)
        if cmd in COMANDO_MODO:
            self._trocar_modo(COMANDO_MODO[cmd])
        elif cmd in (C.DEG, C.RAD, C.GRAD):
            self.angulo = cmd - C.DEG
            self.motor.processar(cmd)
        elif cmd == C.FTOE:
            self.fe = not self.fe
            self.motor.processar(cmd)
        elif cmd in INVERSAS:                              # inversa = INV (146) + função direta
            self.motor.processar(C.INV)
            self.motor.processar(INVERSAS[cmd])
        else:
            self.motor.processar(cmd)
        self.saida.entrada_alterada()                      # slot 10

    def _trocar_modo(self, modo):
        """SetStandardMode/SetScientificMode/SetProgrammerMode: engine criada sob demanda; DecButton e Clear;
        precisão do modo; histórico atual = o do modo (o Programador não muda CM+0xc0)."""
        prec, inteiro, precisao = MODOS[modo]
        if modo not in self.motores:
            self.motores[modo] = Motor(prec, inteiro, self.textos, self.saida, self.historicos.get(modo), *self.seps)
        m = self.motores[modo]
        self.motor, self.modo = m, modo
        if modo in self.historicos:
            self.historico_atual = self.historicos[modo]
        m.precisao = precisao
        m._ajustar_max_digitos()
        m.processar(C.DEC)
        m.processar(C.CLEAR)

    # ------------------------------------------------------------ memória (02b §3.2)
    def memorizar(self):
        """MemorizeNumber 0x18010d760 (MS)."""
        m = self.motor
        if m.erro:
            return
        m.processar(C.MS)
        valor, m.registro = m.registro, None
        self.memoria.insert(0, valor)
        del self.memoria[LIMITE_MEMORIA:]
        self._enviar_memoria()

    def carregar(self, i):
        """MemorizedNumberLoad 0x18010d9b0."""
        if self.motor.erro:
            return
        if i >= len(self.memoria):
            raise IndexError(i)
        self.motor.registro = self.memoria[i]

    def alterado(self, i):
        """MemorizedNumberChanged 0x18010dab0."""
        if self.motor.erro:
            return
        self.memoria[i], self.motor.registro = self.motor.registro, None

    def subtrair(self, i):
        """MemorizedNumberSubtract 0x18010d8c0: com a memória vazia, MS e duas subtrações de si mesma (→ −x)."""
        if self.motor.erro:
            return
        if not self.memoria:
            self.memorizar()
            self.subtrair(0)
            self.subtrair(0)
        else:
            self.carregar(i)
            self.motor.processar(C.MMINUS)
            self.alterado(i)
            self._enviar_memoria()
        self.saida.memoria_item_alterado(i)                # slot 9

    def somar(self, i):
        """OnMemoryAdd do VM 0x1800d76b0 sobre a API do CM."""
        if self.motor.erro:
            return
        if not self.memoria:
            self.memorizar()
        else:
            self.carregar(i)
            self.motor.processar(C.MPLUS)
            self.alterado(i)
            self._enviar_memoria()
        self.saida.memoria_item_alterado(i)

    def limpar_item(self, i):
        """MemorizedNumberClear 0x18010d810 (não testa erro)."""
        del self.memoria[i]
        self._enviar_memoria()

    def limpar_memoria(self):
        """MemorizedNumberClearAll 0x18010d940."""
        self.memoria.clear()
        self.motor.processar(C.MC)
        self._enviar_memoria()

    def _enviar_memoria(self):
        """SetMemorizedNumbersString 0x18010dbe0: mesma conversão do visor na base atual + agrupamento; slot 8."""
        m = self.motor
        self.saida.numeros_memorizados([m.agrupar(m._formatar(v)) for v in self.memoria])
