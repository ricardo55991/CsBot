import json, os, collections, itertools

ROOT = r"c:/Users/ricar/OneDrive/Documentos/Dev/CsBot"
STUDY = os.path.join(ROOT, "training_runs/intermediate_domain_study")
def load(f): return json.loads(open(os.path.join(STUDY, f), "rb").read().decode("utf-8"))

print("#"*90); print("CHECK E — CATALOGO 53 SPOTS E CLASSIFICACAO SEMANTICA (fonte primaria)"); print("#"*90)
cat = json.loads(open(os.path.join(ROOT, "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json"), "rb").read().decode("utf-8"))
print("catalog top keys:", list(cat.keys())[:20])
print("total_spots_field =", cat.get("total_spots"))
spots_arr = cat.get("spots")
print("len(spots) =", len(spots_arr))
cat_ids = [s["id"] for s in spots_arr]
print("duplicatas no catalogo:", [k for k, v in collections.Counter(cat_ids).items() if v > 1])
print("catalog_version =", cat.get("catalog_version"))

sem = json.loads(open(os.path.join(ROOT, "datasets/mirage_v2/contracts/spot_semantic_classification.json"), "rb").read().decode("utf-8"))
print("\nsemantic tipo raiz:", type(sem).__name__, "len =", len(sem))
sem_arr = sem
sem_ids, sem_types = [], []
for e in sem_arr:
    sid = e.get("spot_id") or e.get("id")
    st = e.get("spot_type") or e.get("type") or e.get("semantic_type")
    sem_ids.append(sid); sem_types.append(st)
print("len(sem) =", len(sem_ids), "| ids unicos =", len(set(sem_ids)))
print("distribuicao spot_type:", dict(collections.Counter(sem_types)))
print("soma =", sum(collections.Counter(sem_types).values()))
print("\ncatalog_ids == sem_ids (conjuntos)?", set(cat_ids) == set(sem_ids))
print("so no catalogo:", sorted(set(cat_ids) - set(sem_ids)))
print("so na semantica:", sorted(set(sem_ids) - set(cat_ids)))

print("\n" + "#"*90); print("CHECK F — COBERTURA 53 NO spot_domain_coverage.json"); print("#"*90)
cov = load("spot_domain_coverage.json")
cov_ids = [s["spot_id"] for s in cov["spots"]]
print("len =", len(cov_ids), "| unicos =", len(set(cov_ids)))
print("duplicatas:", [k for k, v in collections.Counter(cov_ids).items() if v > 1])
print("igual ao catalogo (conjunto)?", set(cov_ids) == set(cat_ids))
print("faltando:", sorted(set(cat_ids) - set(cov_ids)))
print("extra:", sorted(set(cov_ids) - set(cat_ids)))

print("\ndistribuicao spot_type no artefato:", dict(collections.Counter(s["spot_type"] for s in cov["spots"])))
print("sum =", sum(collections.Counter(s["spot_type"] for s in cov["spots"]).values()))
# checar tipo por spot contra a fonte primaria
sem_map = dict(zip(sem_ids, sem_types))
mismatch = [(s["spot_id"], s["spot_type"], sem_map.get(s["spot_id"])) for s in cov["spots"] if sem_map.get(s["spot_id"]) != s["spot_type"]]
print("divergencias tipo artefato vs spot_semantic_classification:", len(mismatch), mismatch[:10])

print("\nsector/bombsite no artefato:", dict(collections.Counter((s["sector"], s["bombsite"]) for s in cov["spots"])))
print("side no artefato:", dict(collections.Counter(s["side"] for s in cov["spots"])))

print("\n" + "#"*90); print("CHECK G — CLASSIFICACOES ATRIBUIDAS AOS 53 SPOTS"); print("#"*90)
cls = collections.Counter(s["classification"] for s in cov["spots"])
print("distribuicao:", dict(cls), "| soma =", sum(cls.values()))
FORBIDDEN = ["CROSS_DOMAIN_CONFIRMED", "INTERMEDIATE_CONFIRMED", "DOMAIN_SPECIFIC_INTERMEDIATE"]
print("categorias proibidas presentes:", {k: cls.get(k, 0) for k in FORBIDDEN})
print("soma proibidas = (%d/%d)" % (sum(cls.get(k, 0) for k in FORBIDDEN), 53))
print("PROFESSIONAL_CONFIRMED =", cls.get("PROFESSIONAL_CONFIRMED", 0), " INSUFFICIENT_SUPPORT =", cls.get("INSUFFICIENT_SUPPORT", 0))
print("HUMAN_VALIDATED_ONLY atribuido?", cls.get("HUMAN_VALIDATED_ONLY", 0), "| DOMAIN_SPECIFIC_PRO =", cls.get("DOMAIN_SPECIFIC_PRO", 0))
# coerencia: classification vs support
print("\ncoerencia classification x professional.support_sequences.total:")
bad = []
for s in cov["spots"]:
    tot = s["professional"]["support_sequences"]["total"]
    cl = s["classification"]
    if (tot == 0 and cl != "INSUFFICIENT_SUPPORT") or (tot > 0 and cl != "PROFESSIONAL_CONFIRMED"):
        bad.append((s["spot_id"], tot, cl))
print("incoerencias:", len(bad), bad[:5])

print("\n" + "#"*90); print("CHECK H — SOMA DE SUPORTE POR SPOT POR SPLIT vs eligible_sequences"); print("#"*90)
sums = collections.Counter()
zero_ct = collections.Counter()
for s in cov["spots"]:
    ps = s["professional"]["support_sequences"]["per_split"]
    for k in ("train", "validation", "test"):
        sums[k] += ps[k]
        if ps[k] == 0:
            zero_ct[k] += 1
print("soma por split (recalculada):", dict(sums))
print("total recalculado:", sum(sums.values()))
declared = cov["professional_support_summary"]["sum_support_sequences_by_split"]
print("declarado no artefato:", declared, "| total declarado:", cov["professional_support_summary"]["sum_support_sequences_total"])
print("igual ao recalculado?", dict(sums) == declared, sum(sums.values()) == cov["professional_support_summary"]["sum_support_sequences_total"])
idx = json.loads(open(os.path.join(ROOT, "training_runs/positioning_v2_real_temporal/full_index_spot_ranking_coverage.json"), "rb").read().decode("utf-8"))
print("eligible_sequences (indice):", idx["eligible_sequences"], "| igual?", idx["eligible_sequences"] == sum(sums.values()))
print("total_sequences:", idx["total_sequences"], "| masked:", idx["masked_sequences_transit_or_unmapped"],
      "| soma=total?", idx["eligible_sequences"] + idx["masked_sequences_transit_or_unmapped"] == idx["total_sequences"])
print("spots com support=0 por split:", dict(zero_ct))
print("spots com total=0:", sum(1 for s in cov["spots"] if s["professional"]["support_sequences"]["total"] == 0))
print("spots com total>0:", sum(1 for s in cov["spots"] if s["professional"]["support_sequences"]["total"] > 0))

print("\n" + "#"*90); print("CHECK I — BLOCO intermediate DE TODOS OS 53 SPOTS: EXISTE ALGUM NUMERO?"); print("#"*90)
FIELDS = ["support_sequences","support_episodes","unique_demos","unique_matches","unique_players",
          "unique_teams_stacks","median_dwell","position_variance","approach_direction","exit_direction",
          "primary_aim_distribution","state_distribution","role_distribution","side","bombsite"]
problems = []
nums = []
for s in cov["spots"]:
    inter = s["intermediate"]
    keys = set(inter.keys())
    if keys != set(FIELDS):
        problems.append((s["spot_id"], "KEYS", sorted(keys ^ set(FIELDS))))
    for f in FIELDS:
        blk = inter.get(f)
        if not isinstance(blk, dict):
            problems.append((s["spot_id"], f, "NOT_DICT", blk)); continue
        if blk.get("value") != "N/A":
            problems.append((s["spot_id"], f, "VALUE_NOT_NA", blk.get("value")))
        for kk in ("numerator", "denominator"):
            if blk.get(kk) != 0:
                problems.append((s["spot_id"], f, kk, blk.get(kk)))
        # qualquer chave cujo valor seja int/float (exceto num/den == 0)
        for kk, vv in blk.items():
            if isinstance(vv, (int, float)) and not isinstance(vv, bool):
                if kk not in ("numerator", "denominator") or vv != 0:
                    nums.append((s["spot_id"], f, kk, vv))
print("spots inspecionados: %d | campos por spot: %d | blocos intermediate: %d" % (len(cov["spots"]), len(FIELDS), len(cov["spots"])*len(FIELDS)))
print("problemas estruturais/valor:", len(problems), problems[:10])
print("valores numericos inesperados no bloco intermediate:", len(nums), nums[:10])
