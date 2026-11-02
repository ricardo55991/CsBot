import urllib.request
import json
import time
import concurrent.futures

prompt_template = """Voce e o Capitao e Estrategista (IGL) no CS2 ({team}).
Contexto:
- Mapa: de_mirage | Lado: {team} | Round: 5 | Economia: FullBuy ($4500)
- Escolha a melhor tatica entre:
  1. '{t1}' (Score: 91)
  2. '{t2}' (Score: 80)

Responda APENAS um JSON valido no formato:
{{
  "tactic_name": "{t1}",
  "tactic_summary": "Resumo objetivo",
  "round_tempo": "SLOW_DEFAULT",
  "staging_duration_seconds": 15,
  "bot_orders": {{
    "bot_awper": {{"target_area": "Mid Window", "stance": "PASSIVE_HOLD"}},
    "bot_entry": {{"target_area": "Bombsite A", "stance": "AGGRESSIVE_POKE"}},
    "bot_rotator": {{"target_area": "Connector", "stance": "JIGGLE_INFO"}},
    "bot_anchor": {{"target_area": "Bombsite B", "stance": "PASSIVE_HOLD"}}
  }}
}}"""

def call(team, t1, t2):
    t0 = time.time()
    p = prompt_template.format(team=team, t1=t1, t2=t2)
    body = {
        "model": "qwen2.5:3b",
        "prompt": p,
        "stream": False,
        "format": "json",
        "keep_alive": -1,
        "options": {
            "temperature": 0.2,
            "num_predict": 220
        }
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read())
    dt = time.time() - t0
    return team, dt, res

print("Testando chamadas com num_predict=220:")
t_start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    f1 = ex.submit(call, "CounterTerrorist", "Defesa Padrao 2-1-2 Equilibrada", "Stack A & Retake B Preparado")
    f2 = ex.submit(call, "Terrorist", "Execucao B (Tapete Rapido)", "Split A (Top Mid + Conector)")
    r1 = f1.result()
    r2 = f2.result()

print(f"R1 ({r1[0]}): {r1[1]:.2f}s, tokens={r1[2].get('eval_count')}")
print(f"R2 ({r2[0]}): {r2[1]:.2f}s, tokens={r2[2].get('eval_count')}")
print(f"Total concurrent time: {time.time() - t_start:.2f}s")
print("R1 JSON:", r1[2].get("response"))
print("R2 JSON:", r2[2].get("response"))
