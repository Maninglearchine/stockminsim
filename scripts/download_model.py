"""
Docker build 단계에서 HuggingFace 모델을 /app/models/KR-FinBert-SC 로 다운로드.
Railway 런타임 콜드스타트에서 모델 다운로드가 발생하지 않도록 이미지에 포함시킨다.
"""
import sys
from pathlib import Path

MODEL_DIR = Path("/app/models/KR-FinBert-SC")

if MODEL_DIR.exists() and any(MODEL_DIR.iterdir()):
    print(f"[model] 이미 존재: {MODEL_DIR}")
    sys.exit(0)

MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("[model] KR-FinBert-SC 다운로드 시작 (snunlp/KR-FinBert-SC)...")

try:
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id="snunlp/KR-FinBert-SC",
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )
    print(f"[model] 다운로드 완료 → {MODEL_DIR}")
except Exception as e:
    print(f"[model] 다운로드 실패: {e}")
    print("[model] 런타임에서 HuggingFace 직접 로드로 fallback됩니다.")
    sys.exit(0)
