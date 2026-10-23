"""CLI da reimplementação.

    python -m calculadora                         # interativo, modo Padrão
    python -m calculadora -m cientifico           # interativo, Científico
    python -m calculadora 2 + 3 '*' 4 =           # executa as teclas e mostra o estado final
    python -m calculadora -m programador -- R:HEX '#FF' NOT

Teclas: a notação dos casos de teste (`rodar-casos.ps1`) mais apelidos (÷ × − √ x² 1/x …); número com vários
dígitos = um botão por dígito; `#1A3` aceita A–F. Comandos começando com `:` (veja `:ajuda`).
"""
import argparse
import sys

from .motor import NaoReimplementado
from .teclas import TeclaDesconhecida, pressionar
from .viewmodel import ANGULOS, TAMANHOS, Calculadora

AJUDA = """\
Teclas (separadas por espaço):
  dígitos  123  #1A3 (A–F no Programador)     ,  DEC (separador decimal)
  + - * /  (ou × ÷ −)   =   C   CE   BS (⌫)   NEG (±)   %   SQRT (√)   SQR (x²)   INV (1/x)
  memória  MS  MR  M+  M-  MC        histórico  LH (limpar)
  modos    ALT1 (Padrão)  ALT2 (Científico)  ALT4 (Programador)
  Científico  SIN COS TAN ASIN ACOS ATAN SINH… SEC… PI E EXP FE ANG ANG:RAD FACT MOD POW P10 LOG LN EX
              YROOT LOGY ABS FLOOR CEIL CUBE CBRT 2^X ( )
  Programador R:HEX R:DEC R:OCT R:BIN  W:BYTE (ou TAM = um clique no botão de tamanho)  BITn
              AND OR XOR NAND NOR NOT LSH RSH ROL ROR ROLC RORC  % (Mod)  DESL:ARIT|LOG|CIRC|CARRY
Comandos:  :hist  :mem  :estado  :modo <padrao|cientifico|programador>  :ajuda  :sair"""


def estado(vm):
    linhas = [f'  {vm.texto_expressao}' if vm.tokens else '  ', f'  {vm.visor}']
    if vm.modo == 'cientifico':
        linhas.append(f"  [{ANGULOS[vm.angulo]}{' F-E' if vm.fe else ''}{' INV' if vm.motor.inv else ''}"
                      f"{f' ({vm.n_parenteses} parênteses)' if vm.n_parenteses else ''}]")
    if vm.modo == 'programador':
        lin = vm.linhas()
        linhas += [f'  {k} {lin[k]}' for k in 'HDOB']
        linhas.append(f'  [{TAMANHOS[vm.tamanho]}, deslocamento {vm.deslocamento}]')
    return '\n'.join(linhas)


def lista(titulo, itens):
    if not itens:
        return f'{titulo}: (vazia)'
    return '\n'.join([f'{titulo}:'] + [f'  {i}' for i in itens])


def executar_linha(vm, linha, saida=print):
    for tok in linha.split():
        try:
            if not pressionar(vm, tok):
                saida(f'(botão {tok} desabilitado)')
        except TeclaDesconhecida:
            saida(f'tecla desconhecida: {tok}  (:ajuda)')
            return
        except NaoReimplementado as e:
            saida(f'não reimplementado (semântica não documentada no relatorio/): {e}')
            return
    while vm.anuncios:
        saida(f'(anúncio: {vm.anuncios.pop(0)})')


def repl(vm):
    print(f'Calculadora (reimplementação, modo {vm.modo}). :ajuda para as teclas, :sair para sair.')
    print(estado(vm))
    while True:
        try:
            linha = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not linha:
            continue
        if linha.startswith(':'):
            cmd, *arg = linha[1:].split()
            if cmd in ('sair', 'q'):
                return
            if cmd == 'ajuda':
                print(AJUDA)
            elif cmd == 'hist':
                print(lista('histórico', [f'{e} | {r}' for e, r in vm.historico]))
            elif cmd == 'mem':
                print(lista('memória', vm.memoria))
            elif cmd == 'modo' and arg:
                vm.definir_modo(arg[0])
            elif cmd != 'estado':
                print('comando desconhecido (:ajuda)')
                continue
        else:
            executar_linha(vm, linha)
        print(estado(vm))


def main(argv=None):
    p = argparse.ArgumentParser(prog='calculadora', description='Reimplementação da Calculadora do Windows '
                                '(modos Padrão, Científico e Programador).')
    p.add_argument('-m', '--modo', default='padrao', choices=['padrao', 'cientifico', 'programador'])
    p.add_argument('--idioma', default='pt-BR', help='pt-BR (padrão) ou en-US: só as mensagens de erro mudam')
    p.add_argument('teclas', nargs='*', help='teclas a executar (sem elas, abre o modo interativo)')
    a = p.parse_args(argv)
    vm = Calculadora(a.modo, a.idioma)
    if not a.teclas:
        repl(vm)
        return 0
    executar_linha(vm, ' '.join(a.teclas))
    print(estado(vm))
    if vm.historico:
        print(lista('histórico', [f'{e} | {r}' for e, r in vm.historico]))
    if vm.memoria:
        print(lista('memória', vm.memoria))
    return 0


if __name__ == '__main__':
    sys.exit(main())
