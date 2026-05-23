import FinanceDataReader as fdr
import pandas as pd

_df_krx: pd.DataFrame | None = None


def load_krx() -> pd.DataFrame:
    global _df_krx
    if _df_krx is None:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        df["Code"] = df["Code"].astype(str).str.zfill(6)
        df["Name"] = df["Name"].astype(str).str.strip()
        _df_krx = df
    return _df_krx


def search_stock(user_input: str) -> list[dict]:
    """
    종목명 또는 종목코드로 KRX 종목 검색.
    Returns list of {"code": "005930", "name": "삼성전자"}
    """
    df = load_krx()
    value = str(user_input).strip()

    if not value:
        return []

    if value.isdigit():
        code_val = value.zfill(6)
        result = df[df["Code"] == code_val]
        if result.empty:
            result = df[df["Code"].str.startswith(value)]
    else:
        val_lower = value.lower()
        exact    = df[df["Name"] == value]
        starts   = df[df["Name"].str.lower().str.startswith(val_lower, na=False)]
        contains = df[df["Name"].str.contains(value, case=False, na=False, regex=False)]
        result = pd.concat([exact, starts, contains]).drop_duplicates(subset=["Code"])

    if result.empty:
        return []

    return [
        {"code": row["Code"], "name": row["Name"]}
        for _, row in result.head(10).iterrows()
    ]


def get_stock_name(code: str) -> str | None:
    df = load_krx()
    code = str(code).zfill(6)
    row = df[df["Code"] == code]
    if row.empty:
        return None
    return row.iloc[0]["Name"]
