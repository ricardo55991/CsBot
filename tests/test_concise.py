import urllib.request
import json
import time

prompt = """Voce e o Capitao e Estrategista (IGL) no CS2 (Counter-Terrorist).
Contexto:
- Mapa: de_mirage | Lado: Counter-Terrorist | Round: 5 | Economia: FullBuy ($4500)
- Escolha a melhor tatica entre:
  1. 'Defesa Padrao 2-1-2 Equilibrada' (Score: 91)
  2. 'Stack A & Retake B Preparado (3-1-1)' (Score: 80)

Responda APENAS um JSON valido no formato:
{
  "tactic_name": "Defesa Padrao 2-1-2 Equilibrada",
  "tactic_summary": "Resumo da estrategia",
  "round_tempo": "SLOW_DEFAULT",
  "staging_duration_seconds": 15,
  "bot_orders": {
    "bot_awper": {"target_area": "Mid Window", "stance": "PASSIVE_HOLD"},
    "bot_entry": {"target_area": "Bombsite A", "stance": "AGGRESSIVE_POKE"},
    "bot_rotator": {"target_area": "Connector", "stance": "JIGGLE_INFO"},
    "bot_anchor": {"target_area": "Bombsite B", "stance": "PASSIVE_HOLD"}
  }
}"""

req_body = {
    "model": "qwen2.5:3b",
    "prompt": prompt,
    "stream": False,
    "format": "json",
    "keep_alive": -1,
    "options": {
        "temperature": 0.2,
        "num_predict": 180
    }
}
data = json.dumps(req_body).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})

t0 = time.time()
with urllib.request.urlopen(req, timeout=15) as r:
    res = json.loads(r.read())
dt = time.time() - t0
print(f"Concise call took: {dt:.2f}s, eval_count={res.get('eval_count')}, eval_duration={res.get('eval_duration',0)/1e6:.1f}ms")
print("Response:", res.get("response"))
