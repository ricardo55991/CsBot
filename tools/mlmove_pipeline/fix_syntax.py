from pathlib import Path
import re
import py_compile

p = Path("tools/mlmove_pipeline/train_and_export_onnx.py")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

pattern = r'flush=True\s*\):\s*\{acc_h0:\.2f\}%.*?\n\s*\)'
text = re.sub(pattern, 'flush=True\n        )', text)

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

py_compile.compile(str(p), doraise=True)
print("train_and_export_onnx.py compiled successfully!")
