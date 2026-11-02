import urllib.request
import json
import time
import concurrent.futures

def test_diag():
    print("=== TESTE DE DIAGNÓSTICO OLLAMA IGL ===")
    
    # a) GET de disponibilidade / listagem de modelos
    print("\n--- a) Verificando disponibilidade e modelos ---")
    t0 = time.time()
    req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
    with urllib.request.urlopen(req, timeout=5) as r:
        tags = json.loads(r.read())
    t_tags = time.time() - t0
    models = [m['name'] for m in tags.get('models', [])]
    print(f"Status: OK ({t_tags*1000:.1f}ms). Modelos disponíveis: {models}")
    assert "qwen2.5:3b" in models, "Modelo qwen2.5:3b não encontrado!"

    # b) Chamada mínima ao modelo (ping)
    print("\n--- b) Chamada mínima ao modelo ---")
    t0 = time.time()
    req_body = {
        "model": "qwen2.5:3b",
        "prompt": "ping",
        "stream": False,
        "keep_alive": -1
    }
    data = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    t_min = time.time() - t0
    print(f"Status: OK ({t_min*1000:.1f}ms). Resposta: {resp.get('response', '').strip()[:60]}")

    # c) Chamada usando o mesmo payload do IGL
    print("\n--- c) Chamada completa com payload do IGL (JSON schema) ---")
    igl_prompt = """Você é o Capitão e Estrategista (IGL) no CS2 (CounterTerrorist).
Contexto do Round:
- Mapa: de_mirage | Lado: CounterTerrorist | Round: 5
- Economia: FullBuy (Média: $4500, LossStreak: 0)
- Histórico Recente: Vitória anterior
- Candidatas Táticas Avaliadas para este Round:
1. Defesa Padrão 2-1-2 Equilibrada (Pontuação: 91.0)
2. Stack A & Retake B Preparado (3-1-1) (Pontuação: 80.0)
- Diretriz de Diversidade: Nenhuma
- Pacing: SLOW_DEFAULT
- Instrução do Humano: Estruture o plano detalhado para 'Defesa Padrão 2-1-2 Equilibrada'.

Responda APENAS um JSON válido seguindo esta estrutura:
{
  "decisionId": "DEC-TEST",
  "side": "CT",
  "round": 5,
  "tacticName": "Defesa Padrão 2-1-2 Equilibrada",
  "tacticSummary": "Defesa padrão 2-1-2",
  "tempo": "SLOW_DEFAULT",
  "stagingDuration": 15,
  "botOrders": {
    "bot_awper": { "target_area": "Mid Window", "role_action": "Hold window", "staging_spot_id": "ct_mid_window_deep_awp", "execute_spot_id": "ct_mid_window_crouch", "stance": "PASSIVE_HOLD", "fallback_spot_id": "ct_spawn_safe" },
    "bot_entry": { "target_area": "Bombsite A", "role_action": "Hold A", "staging_spot_id": "ct_a_palace_close_poke", "execute_spot_id": "ct_a_stairs_cross", "stance": "AGGRESSIVE_POKE", "fallback_spot_id": "ct_spawn_safe" },
    "bot_rotator": { "target_area": "Connector", "role_action": "Hold connector", "staging_spot_id": "ct_mid_connector_headshot", "execute_spot_id": "ct_a_stairs_cross", "stance": "JIGGLE_INFO", "fallback_spot_id": "ct_spawn_safe" },
    "bot_anchor": { "target_area": "Bombsite B", "role_action": "Anchor B", "staging_spot_id": "ct_b_van_peek", "execute_spot_id": "ct_b_site_default_crouch", "stance": "JIGGLE_INFO", "fallback_spot_id": "ct_spawn_safe" }
  }
}"""

    req_body_igl = {
        "model": "qwen2.5:3b",
        "prompt": igl_prompt,
        "stream": False,
        "format": "json",
        "keep_alive": -1,
        "options": {
            "temperature": 0.35,
            "num_predict": 480
        }
    }
    t0 = time.time()
    data = json.dumps(req_body_igl).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp_igl = json.loads(r.read())
    t_igl = time.time() - t0
    raw_json_c = resp_igl.get("response", "")
    print(f"Status: OK ({t_igl*1000:.1f}ms). Tokens retornados: {resp_igl.get('eval_count')}. eval_duration: {resp_igl.get('eval_duration',0)/1e6:.1f}ms")
    print(f"JSON gerado (primeiros 150 chars): {raw_json_c[:150]}...")

    # d) Duas chamadas concorrentes (CT e TR simultâneas)
    print("\n--- d) Duas chamadas concorrentes (CT e TR simuladas) ---")
    def call_ollama(team_name):
        start = time.time()
        body = dict(req_body_igl)
        body["prompt"] = igl_prompt.replace("CounterTerrorist", team_name)
        d = json.dumps(body).encode("utf-8")
        rq = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=d, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(rq, timeout=30) as resp_obj:
            res = json.loads(resp_obj.read())
            dur = time.time() - start
            return team_name, dur, res

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_ct = executor.submit(call_ollama, "CounterTerrorist")
        f_tr = executor.submit(call_ollama, "Terrorist")
        r_ct = f_ct.result()
        r_tr = f_tr.result()
    t_concurrent = time.time() - t0
    print(f"CT finalizado em {r_ct[1]*1000:.1f}ms (eval_count={r_ct[2].get('eval_count')})")
    print(f"TR finalizado em {r_tr[1]*1000:.1f}ms (eval_count={r_tr[2].get('eval_count')})")
    print(f"Tempo total concorrente: {t_concurrent*1000:.1f}ms")

    # e) Validação da resposta com o parser real
    print("\n--- e) Validação com o parser real ---")
    parsed_json = json.loads(raw_json_c)
    assert "tacticName" in parsed_json, "Falta tacticName"
    assert "botOrders" in parsed_json, "Falta botOrders"
    print(f"Parse JSON OK! tacticName='{parsed_json.get('tacticName')}', botOrders={list(parsed_json.get('botOrders', {}).keys())}")
    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    test_diag()
