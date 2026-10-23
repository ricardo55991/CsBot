from pathlib import Path

p = Path("tools/mlmove_pipeline/overnight_massive_worker.py")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("dt_ext = time.perf_counter() - t_ext", "dt_ext = time.perf_counter() - t0_ext")

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

import py_compile
py_compile.compile(str(p), doraise=True)
print("overnight_massive_worker.py fixed and verified!")
