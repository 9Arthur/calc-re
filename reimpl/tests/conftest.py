import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def pytest_terminal_summary(terminalreporter):
    """Taxa de casos passando por subfase."""
    por = {}
    for estado in ('passed', 'failed'):
        for rep in terminalreporter.stats.get(estado, []):
            if '::test_caso[' in rep.nodeid and rep.when == 'call':
                fase = rep.nodeid.split('[')[1][:2]
                t = por.setdefault(fase, [0, 0, []])
                t[1] += 1
                if estado == 'passed':
                    t[0] += 1
                else:
                    t[2].append(rep.nodeid.split('[')[1].rstrip(']'))
    if not por:
        return
    terminalreporter.section('taxa por subfase')
    for fase in sorted(por):
        ok, n, falhas = por[fase]
        terminalreporter.write_line(f'{fase}: {ok}/{n} ({100 * ok / n:.1f}%)' + (f'  falhas: {", ".join(falhas)}' if falhas else ''))
    ok = sum(v[0] for v in por.values()); n = sum(v[1] for v in por.values())
    terminalreporter.write_line(f'total: {ok}/{n} ({100 * ok / n:.1f}%)')
