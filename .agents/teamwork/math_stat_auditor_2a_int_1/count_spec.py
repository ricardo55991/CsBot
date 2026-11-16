import io, os, re

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
P = os.path.join(ROOT, ".agents/teamwork/ORIGINAL_REQUEST.md")
lines = io.open(P, encoding="utf-8").read().splitlines()
print("total_linhas =", len(lines))

REGIONS = [
 ("§12 CT metrics",            1497, 1513),
 ("§12 (regra 2-1-2)",         1515, 1515),
 ("§13 TR metrics",            1527, 1541),
 ("§13 distincoes",            1545, 1550),
 ("§14 grupos",                1560, 1562),
 ("§14 metricas",              1566, 1580),
 ("§14 estatistica",           1584, 1588),
 ("§15 estatisticas por spot", 1601, 1615),
 ("§15 classificacoes",        1619, 1625),
 ("§16 criterios piloto",      1641, 1646),
 ("§16 classificacoes",        1650, 1656),
 ("§17 criterios de hipotese", 1666, 1673),
 ("§17 problemas",             1679, 1686),
 ("§18 estrategias",           1696, 1716),
 ("§18 avaliacao por estrategia", 1720, 1727),
 ("§20 testes",                1766, 1785),
 ("§19 leakeage a evitar",     1739, 1743),
 ("§19 artefatos de split",    1753, 1756),
 ("Gate A",                    1854, 1859),
 ("Gate B",                    1863, 1869),
 ("Gate C",                    1873, 1877),
]

for name, a, b in REGIONS:
    items = []
    for i in range(a - 1, b):
        raw = lines[i]
        s = raw.strip()
        if not s:
            continue
        if re.match(r"^\d+\.\s", s):          # lista numerada
            items.append(s)
        elif raw.startswith("    ") and not raw.startswith("        "):
            items.append(s)
    print("-" * 90)
    print("%-32s linhas %d-%d  -> N = %d" % (name, a, b, len(items)))
    for k, it in enumerate(items, 1):
        print("    %2d. %s" % (k, it))
