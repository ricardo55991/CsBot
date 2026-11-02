import time
import json
import urllib.request
import concurrent.futures

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"
TIMEOUT = 12

print("==========================================================")
print("  DIAGNOSTICO ISOLADO DO OLLAMA - CSBOTMANAGER V4.2")
print(f"  Endpoint: {OLLAMA_URL} | Modelo: {MODEL} | Timeout: {TIMEOUT}s")
print("==========================================================\n")

def invoke_measurement(test_name, prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 120
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    
    start = time.perf_counter()
    res = {
        "test_name": test_name,
        "model": MODEL,
        "prompt_tokens": 0,
        "generated_tokens": 0,
        "load_duration_ms": 0.0,
        "prompt_eval_duration_ms": 0.0,
        "eval_duration_ms": 0.0,
        "total_duration_ms": 0.0,
        "tokens_per_second": 0.0,
        "response_size_bytes": 0,
        "parse_success": False,
        "timeout": False,
        "error": None
    }
    
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read().decode('utf-8')
            elapsed = (time.perf_counter() - start) * 1000.0
            res["total_duration_ms"] = round(elapsed, 1)
            parsed = json.loads(raw)
            res["prompt_tokens"] = parsed.get("prompt_eval_count", 0)
            res["generated_tokens"] = parsed.get("eval_count", 0)
            res["load_duration_ms"] = round(parsed.get("load_duration", 0) / 1e6, 1)
            res["prompt_eval_duration_ms"] = round(parsed.get("prompt_eval_duration", 0) / 1e6, 1)
            res["eval_duration_ms"] = round(parsed.get("eval_duration", 0) / 1e6, 1)
            
            resp_text = parsed.get("response", "")
            res["response_size_bytes"] = len(resp_text)
            
            eval_dur_s = parsed.get("eval_duration", 0) / 1e9
            if eval_dur_s > 0:
                res["tokens_per_second"] = round(res["generated_tokens"] / eval_dur_s, 2)
            
            res["parse_success"] = len(resp_text.strip()) > 0
            res["raw_sample"] = resp_text.strip()[:100]
    except Exception as ex:
        elapsed = (time.perf_counter() - start) * 1000.0
        res["total_duration_ms"] = round(elapsed, 1)
        if "timed out" in str(ex).lower():
            res["timeout"] = True
        res["error"] = str(ex)
        
    return res

prompt_ct = "You are CT IGL on de_mirage. Choose: A Default or B Rush. Return JSON."
prompt_tr = "You are TR IGL on de_mirage. Choose: Execute A or Execute B. Return JSON."

# 1. CT Fria
print("[1/4] Testando chamada CT (Fria)...")
r1 = invoke_measurement("CT_Cold", prompt_ct)
print(f" -> Total: {r1['total_duration_ms']}ms | GenTokens: {r1['generated_tokens']} | TPS: {r1['tokens_per_second']} | Timeout: {r1['timeout']} | Err: {r1['error']}")

# 2. TR
print("[2/4] Testando chamada TR...")
r2 = invoke_measurement("TR_Live", prompt_tr)
print(f" -> Total: {r2['total_duration_ms']}ms | GenTokens: {r2['generated_tokens']} | TPS: {r2['tokens_per_second']} | Timeout: {r2['timeout']} | Err: {r2['error']}")

# 3. CT pós-warmup
print("[3/4] Testando chamada CT pós-warmup...")
r3 = invoke_measurement("CT_PostWarmup", prompt_ct)
print(f" -> Total: {r3['total_duration_ms']}ms | GenTokens: {r3['generated_tokens']} | TPS: {r3['tokens_per_second']} | Timeout: {r3['timeout']} | Err: {r3['error']}")

# 4. Concorrência
print("[4/4] Testando CT e TR em concorrência...")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    f_ct = executor.submit(invoke_measurement, "Concurrent_CT", prompt_ct)
    f_tr = executor.submit(invoke_measurement, "Concurrent_TR", prompt_tr)
    r_ct = f_ct.result()
    r_tr = f_tr.result()

print(f" -> Concorrente CT: {r_ct['total_duration_ms']}ms | Tokens: {r_ct['generated_tokens']} | TPS: {r_ct['tokens_per_second']} | Timeout: {r_ct['timeout']}")
print(f" -> Concorrente TR: {r_tr['total_duration_ms']}ms | Tokens: {r_tr['generated_tokens']} | TPS: {r_tr['tokens_per_second']} | Timeout: {r_tr['timeout']}")

print("\n==========================================================")
print("  TABELA FINAL DE RESULTADOS (PARTE 10)")
print("==========================================================")
print(f"{'Teste':<16} | {'Total(ms)':<10} | {'Eval(ms)':<10} | {'Tokens':<8} | {'TPS':<8} | {'Parse':<6} | {'Timeout':<7}")
print("-" * 75)
for r in [r1, r2, r3, r_ct, r_tr]:
    print(f"{r['test_name']:<16} | {r['total_duration_ms']:<10} | {r['eval_duration_ms']:<10} | {r['generated_tokens']:<8} | {r['tokens_per_second']:<8} | {str(r['parse_success']):<6} | {str(r['timeout']):<7}")
