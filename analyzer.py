import numpy as np
import torch
import pandas as pd
from transformers import pipeline

_pipe = None
_model_path: str = ""


def load_model(local_model_path: str = "./models/KR-FinBert-SC") -> None:
    global _pipe, _model_path
    if _pipe is None or _model_path != local_model_path:
        device = 0 if torch.cuda.is_available() else -1
        _pipe = pipeline(
            task="text-classification",
            model=local_model_path,
            tokenizer=local_model_path,
            device=device,
        )
        _model_path = local_model_path


def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Title"] = df["Title"].astype(str).str.strip()
    df["Recommend_Count"] = df["Recommend_Count"].fillna(0).astype(int)
    df = df[df["Title"].str.len() >= 3]
    df = df.drop_duplicates(subset=["Title"])
    df = df.reset_index(drop=True)
    return df


def _signal_strength(confidence: float) -> str:
    if confidence > 0.3:
        return "강함"
    if confidence > 0.15:
        return "보통"
    return "약함"


def analyze(
    df_board: pd.DataFrame,
    local_model_path: str = "./models/KR-FinBert-SC",
    batch_size: int = 32,
    top_n: int = 5,
    max_length: int = 64,
) -> dict:
    load_model(local_model_path)

    df = _preprocess(df_board)
    if df.empty:
        raise ValueError("분석할 게시글 제목이 없습니다.")

    df["Weight"] = np.log1p(df["Recommend_Count"]) + 1

    outputs = _pipe(
        df["Title"].tolist(),
        batch_size=batch_size,
        truncation=True,
        max_length=max_length,
        top_k=None,
    )

    pos_probs, neg_probs = [], []
    for result in outputs:
        scores = {item["label"].lower(): item["score"] for item in result}
        pos_probs.append(scores.get("positive", 0.0))
        neg_probs.append(scores.get("negative", 0.0))

    df["Prob_Positive"] = pos_probs
    df["Prob_Negative"] = neg_probs
    df["Buy_Score"] = df["Weight"] * df["Prob_Positive"]
    df["Sell_Score"] = df["Weight"] * df["Prob_Negative"]

    total_buy = float(df["Buy_Score"].sum())
    total_sell = float(df["Sell_Score"].sum())

    signal = "매수" if total_buy >= total_sell else "매도"
    score_sum = total_buy + total_sell
    confidence = abs(total_buy - total_sell) / score_sum if score_sum > 0 else 0.0
    strength = _signal_strength(confidence)

    if signal == "매수":
        df_ev = df[df["Buy_Score"] >= df["Sell_Score"]].copy()
        sort_col = "Buy_Score"
    else:
        df_ev = df[df["Sell_Score"] > df["Buy_Score"]].copy()
        sort_col = "Sell_Score"

    if df_ev.empty:
        df_ev = df.copy()

    evidence = (
        df_ev.sort_values(sort_col, ascending=False)
        .head(top_n)["Title"]
        .tolist()
    )

    return {
        "signal": signal,
        "strength": strength,
        "confidence": round(confidence, 4),
        "buy_score": round(total_buy, 4),
        "sell_score": round(total_sell, 4),
        "evidence": evidence,
        "analyzed_count": len(df),
    }
