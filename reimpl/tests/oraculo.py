"""Oráculo: resultados reais das execuções caixa-preta das fases 3a–3d.

- Visor, histórico, memória, estado dos botões, linhas do painel e bits: `relatorio/resultados-reais*.txt`
  (lidos do UIA, sem transcrição).
- Expressão: 3a — o campo do próprio `resultados-reais.txt` (já com a transcrição das capturas aplicada); 3b–3d —
  `trabalho/automacao/transcricao-capturas-3{b,c,d}.tsv` (o OCR bruto dos resultados não é usado). Leituras sem
  transcrição ficam sem expressão a comparar, como nos scripts `comparar-3*.py`.
- Casos (passos): `tests/casos.json`, extraído de `rodar-casos.ps1` por `ferramentas/extrair_casos.py`.
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
REL = RAIZ / 'relatorio'
AUTO = RAIZ / 'trabalho' / 'automacao'

ARQ_RESULTADOS = {'3a': 'resultados-reais.txt', '3b': 'resultados-reais-3b.txt', '3c': 'resultados-reais-3c.txt',
                  '3d': 'resultados-reais-3d.txt'}
ARQ_CONGELADO = {'3a': '03-casos-de-teste.md', '3b': '03b-casos-de-teste.md', '3c': '03c-casos-de-teste.md',
                 '3d': '03d-casos-de-teste.md'}
_CAB = re.compile(r'^(3[a-d]-\d+c?)(?: →(\d+) \[(?:[^\[\]]|\[[^\]]*\])*\])?: (.*)$')


def casos(fase=None):
    dados = json.loads((Path(__file__).parent / 'casos.json').read_text(encoding='utf-8'))['casos']
    return [c for c in dados if fase is None or c['fase'] == fase]


def _transcricoes(fase):
    arq = AUTO / f'transcricao-capturas-{fase}.tsv'
    out = {}
    for ln in arq.read_text(encoding='utf-8').splitlines():
        if not ln.strip() or ln.startswith('#') or ln.startswith('captura\t'):
            continue
        cap, origem, texto = ln.split('\t')
        out[cap] = (texto, origem)
    return out


def _vazia(s):
    return '' if s.startswith('(vazia') else s


def _botoes_3a(obs):
    m = re.search(r'desabilitados: (.*?) ; habilitados: (.*)$', obs)
    if not m:
        return None
    est = {b: False for b in m.group(1).split()}
    est.update({b: True for b in m.group(2).split()})
    return est


def _hist(s):
    if s.startswith('(vazia'):
        return []
    return [(e, r) for e, r in re.findall(r'\[(.*?) \| (.*?)\](?:; |$)', s)]


def leituras(fase):
    """id → lista de leituras na ordem (intermediárias e a final)."""
    trans = _transcricoes(fase) if fase != '3a' else {}
    out = {}
    linhas = (REL / ARQ_RESULTADOS[fase]).read_text(encoding='utf-8').splitlines()
    for ln in linhas:
        if ln.startswith('# Checagem cruzada'):
            break
        m = _CAB.match(ln)
        if not m:
            continue
        cid, n, corpo = m.groups()
        cap = f'{cid}-{n}' if n else f'{cid}-final'
        lei = {'captura': cap, 'expr': None, 'origem_expr': None}
        if fase == '3a':
            corpo, _, obs = corpo.partition(' -- ')
            visor, _, expr = corpo.partition(' | ')
            lei.update(visor=visor, expr=_vazia(expr), origem_expr='transcrição (resultados-reais.txt)',
                       botoes=_botoes_3a(obs))
        elif fase == '3b':
            r = re.match(r'^(.*?) \| (.*?) \| hist\(\d+\): (.*) \| mem: (.*?) \| (MC=\S+ MR=\S+ M\+=\S+ M−=\S+ '
                         r'MS=\S+ M▾=\S+)(?: -- .*)?$', corpo)
            visor, _ocr, hist, mem, bot = r.groups()
            lei.update(visor=visor, historico=_hist(hist),
                       memoria=[] if mem.startswith('(vazia') else mem.split('; '),
                       botoes={k: v == 'hab' for k, v in (p.split('=') for p in bot.split())})
        elif fase == '3c':
            lei['visor'] = corpo.split(' | ')[0]
        else:
            partes = corpo.split(' -- ')[0].split(' | ')
            lei['visor'] = partes[0]
            lei['linhas'] = dict(re.findall(r"([HDOB])='([^']*)'", partes[2]))
            b = re.search(r'bits=\{([^}]*)\}', partes[3])
            lei['bits'] = None if not b else {int(x) for x in b.group(1).split(',') if x.strip()}
        if fase != '3a' and cap in trans:
            texto, origem = trans[cap]
            lei['expr'], lei['origem_expr'] = _vazia(texto), origem
        out.setdefault(cid, []).append(lei)
    return out


def estado_base_3a():
    """Linha `BASE (Padrao, apos C)` do resultados-reais.txt."""
    for ln in (REL / ARQ_RESULTADOS['3a']).read_text(encoding='utf-8').splitlines():
        if ln.startswith('BASE '):
            return _botoes_3a(ln)
    return None
