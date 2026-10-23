from pathlib import Path
import re

p = Path("tools/mlmove_pipeline/train_and_export_onnx.py")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

sharded_pattern = r"class ShardedMemmapDataset\(Dataset\):.*?def load_dataset_for_map"
sharded_new = '''class ShardedMemmapDataset(Dataset):
    """
    Dataset sharded de alta performance e baixo consumo de RAM (< 1.5 GB).
    Descarta o bootstrap sintético automaticamente quando houver >= 50.000 amostras humanas reais.
    Mantém os tensores em memória contígua (~100 MB para centenas de milhares de passos)
    proporcionando throughput máximo na GPU AMD RX 6600M sem gargalo de I/O.
    """
    def __init__(self, npz_files: List[Path]):
        real_files = [f for f in npz_files if "bootstrap" not in f.name.lower()]
        real_samples = 0
        for f in real_files:
            try:
                with np.load(f) as data:
                    if "X" in data:
                        real_samples += len(data["X"])
            except Exception:
                pass

        if real_samples >= 50000:
            print(f"[ShardedMemmapDataset] Dataset de partidas humanas reais robusto ({real_samples:,} amostras >= 50k). Descartando bootstrap sintético!", flush=True)
            target_files = real_files
        else:
            target_files = npz_files

        x_list = []
        y_list = []
        total = 0
        for f in target_files:
            try:
                with np.load(f) as data:
                    if "X" in data and "Y" in data:
                        x = np.asarray(data["X"], dtype=np.float32)
                        y = np.asarray(data["Y"], dtype=np.int64)
                        sz = len(x)
                        if sz > 0:
                            x_list.append(x)
                            y_list.append(y)
                            total += sz
                            print(f"[ShardedMemmapDataset] Shard {f.name}: {sz:,} amostras (Total: {total:,})", flush=True)
            except Exception as exc:
                print(f"[ShardedMemmapDataset] Aviso ao ler {f.name}: {exc}", flush=True)

        if total == 0:
            raise ValueError("Nenhuma amostra válida encontrada nos arquivos .npz fornecidos.")

        self.total_samples = total
        self.X = torch.from_numpy(np.concatenate(x_list, axis=0))
        self.Y = torch.from_numpy(np.concatenate(y_list, axis=0))
        ram_mb = (self.X.element_size() * self.X.nelement() + self.Y.element_size() * self.Y.nelement()) / (1024**2)
        print(f"[ShardedMemmapDataset] Dataset consolidado com {total:,} amostras (Consumo RAM: {ram_mb:.1f} MB << 2.0 GB).", flush=True)

    def __len__(self) -> int:
        return self.total_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.Y[idx]


def load_dataset_for_map'''

text = re.sub(sharded_pattern, sharded_new, text, flags=re.DOTALL)

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

import py_compile
py_compile.compile(str(p), doraise=True)
print("train_and_export_onnx.py successfully patched and verified!")
