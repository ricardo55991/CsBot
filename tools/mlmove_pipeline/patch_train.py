from pathlib import Path
import re

p = Path("tools/mlmove_pipeline/train_and_export_onnx.py")
with open(p, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Resilient imports
old_imp = """from contract_spec import (
    ACTION_SPACE_SIZE,
    CHECKPOINTS_DIR_D,
    DEFAULT_BASE_DIR,
    EXTRACTED_TENSORS_DIR_D,
    FEATURE_DIM,
    HORIZONS_COUNT,
    MAX_PLAYERS,
    ONNX_INPUT_NAME,
    ONNX_OUTPUT_NAME,
    SERVER_MODELS_DIR_H,
)
from model_mlmove import MLMoveTransformer, count_parameters"""

new_imp = """try:
    from contract_spec import (
        ACTION_SPACE_SIZE,
        CHECKPOINTS_DIR_D,
        DEFAULT_BASE_DIR,
        EXTRACTED_TENSORS_DIR_D,
        FEATURE_DIM,
        HORIZONS_COUNT,
        MAX_PLAYERS,
        ONNX_INPUT_NAME,
        ONNX_OUTPUT_NAME,
        SERVER_MODELS_DIR_H,
    )
    from model_mlmove import MLMoveTransformer, count_parameters
except ImportError:
    from tools.mlmove_pipeline.contract_spec import (
        ACTION_SPACE_SIZE,
        CHECKPOINTS_DIR_D,
        DEFAULT_BASE_DIR,
        EXTRACTED_TENSORS_DIR_D,
        FEATURE_DIM,
        HORIZONS_COUNT,
        MAX_PLAYERS,
        ONNX_INPUT_NAME,
        ONNX_OUTPUT_NAME,
        SERVER_MODELS_DIR_H,
    )
    from tools.mlmove_pipeline.model_mlmove import MLMoveTransformer, count_parameters"""

code = code.replace(old_imp, new_imp)

# 2. P99 latency in export_to_server_onnx
old_lat = """    avg_ms = float(np.mean(latencies))
    p50_ms = float(np.median(latencies))
    print(
        f"[train_and_export_onnx] Validação ONNX Runtime CPU -> Output shape: {out.shape} | Latência mediana: {p50_ms:.3f} ms (média: {avg_ms:.3f} ms)"
    )"""

new_lat = """    avg_ms = float(np.mean(latencies))
    p50_ms = float(np.median(latencies))
    p99_ms = float(np.percentile(latencies, 99))
    print(
        f"[train_and_export_onnx] Validação ONNX Runtime CPU -> Output shape: {out.shape} | Latência mediana: {p50_ms:.3f} ms (média: {avg_ms:.3f} ms, p99: {p99_ms:.3f} ms)",
        flush=True
    )"""

code = code.replace(old_lat, new_lat)

# 3. Epoch loop tracking L0, L125, L250, Top-1, Top-3
epoch_loop_pattern = r"    for epoch in range\(1, args\.epochs \+ 1\):.*?print\(\s*f\"\s*\[Época.*?\)"
epoch_loop_new = """    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        running_l0 = 0.0
        running_l1 = 0.0
        running_l2 = 0.0
        correct_h0 = 0
        correct_top3_h0 = 0
        total_tokens = 0
        t_ep = time.perf_counter()

        for bx, by in loader:
            bx = bx.to(device)
            by = by.to(device)

            optimizer.zero_grad()
            logits = model(bx)  # [B, 10, 3, 97]

            loss_0ms = criterion(logits[:, :, 0, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 0].reshape(-1))
            loss_125ms = criterion(logits[:, :, 1, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 1].reshape(-1))
            loss_250ms = criterion(logits[:, :, 2, :].reshape(-1, ACTION_SPACE_SIZE), by[:, :, 2].reshape(-1))
            loss = loss_0ms + loss_125ms + loss_250ms

            loss.backward()
            for p_param in model.parameters():
                if p_param.grad is not None:
                    p_param.grad.clamp_(-1.0, 1.0)
            optimizer.step()

            bsz = bx.size(0)
            running_loss += float(loss.item()) * bsz
            running_l0 += float(loss_0ms.item()) * bsz
            running_l1 += float(loss_125ms.item()) * bsz
            running_l2 += float(loss_250ms.item()) * bsz

            preds_h0 = logits[:, :, 0, :].argmax(dim=-1)
            correct_h0 += int((preds_h0 == by[:, :, 0]).sum().item())

            _, top3_preds = logits[:, :, 0, :].topk(3, dim=-1)
            correct_top3_h0 += int((top3_preds == by[:, :, 0].unsqueeze(-1)).any(dim=-1).sum().item())
            total_tokens += bsz * MAX_PLAYERS

        scheduler.step()
        epoch_loss = running_loss / len(dataset)
        ep_l0 = running_l0 / len(dataset)
        ep_l1 = running_l1 / len(dataset)
        ep_l2 = running_l2 / len(dataset)
        acc_top1 = (correct_h0 / max(1, total_tokens)) * 100.0
        acc_top3 = (correct_top3_h0 / max(1, total_tokens)) * 100.0
        dt = time.perf_counter() - t_ep
        print(
            f"  [Época {epoch:02d}/{args.epochs:02d}] Loss: {epoch_loss:.4f} (L0: {ep_l0:.3f}, L125: {ep_l1:.3f}, L250: {ep_l2:.3f}) | Top-1: {acc_top1:.2f}% | Top-3: {acc_top3:.2f}% | Tempo: {dt:.2f}s",
            flush=True
        )"""

code = re.sub(epoch_loop_pattern, epoch_loop_new, code, flags=re.DOTALL)

with open(p, "w", encoding="utf-8") as f:
    f.write(code)

print("train_and_export_onnx.py successfully enhanced with multi-horizon tracking and Top-1/Top-3.")
