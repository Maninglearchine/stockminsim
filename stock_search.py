import requests
import pandas as pd
from bs4 import BeautifulSoup

_df_krx: pd.DataFrame | None = None


def load_krx() -> pd.DataFrame:
    global _df_krx
    if _df_krx is None:
        resp = requests.get(
            "https://kind.krx.co.kr/corpgeneral/corpList.do",
            params={"method": "download", "searchType": "13"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table tr")
        data = []
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[0].get_text(strip=True)
                code = str(cols[1].get_text(strip=True)).zfill(6)
                if name and code:
                    data.append({"Name": name, "Code": code})
        _df_krx = pd.DataFrame(data, columns=["Name", "Code"])
    return _df_krx


def search_stock(user_input: str) -> list[dict]:
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
