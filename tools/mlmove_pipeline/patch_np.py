from pathlib import Path

p = Path("tools/mlmove_pipeline/train_and_export_onnx.py")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

target = """        x = np.array(data["X"][local_idx], dtype=np.float32, copy=False)
        y = np.array(data["Y"][local_idx], dtype=np.int64, copy=False)"""

replacement = """        x = np.asarray(data["X"][local_idx], dtype=np.float32)
        y = np.asarray(data["Y"][local_idx], dtype=np.int64)"""

text = text.replace(target, replacement)

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

import py_compile
py_compile.compile(str(p), doraise=True)
print("train_and_export_onnx.py updated and verified.")
