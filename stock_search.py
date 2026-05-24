import requests
import pandas as pd
from bs4 import BeautifulSoup

_df_krx: pd.DataFrame | None = None


def load_krx() -> pd.DataFrame:
    global _df_krx
    if _df_krx is None:
        try:
            resp = requests.get(
                "https://kind.krx.co.kr/corpgeneral/corpList.do",
                params={"method": "download", "searchType": "13"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            resp.encoding = "euc-kr"
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("table tr")

            # 헤더에서 종목코드 컬럼 위치 동적 탐지 (기본값 cols[2])
            code_idx = 2
            if rows:
                hdrs = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
                for i, h in enumerate(hdrs):
                    if "종목코드" in h:
                        code_idx = i
                        break

            data = []
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) > code_idx:
                    name = cols[0].get_text(strip=True)
                    code = cols[code_idx].get_text(strip=True).strip()
                    if name and code:
                        data.append({"Name": name, "Code": code.zfill(6)})

            _df_krx = pd.DataFrame(data, columns=["Name", "Code"])
            print(f"[KRX] {len(_df_krx)}개 종목 로딩 완료 (종목코드 col={code_idx})")
        except Exception as e:
            print(f"[KRX] 로딩 실패: {e}")
            _df_krx = pd.DataFrame(columns=["Name", "Code"])
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
        for _, row in result.head(50).iterrows()
    ]


def get_stock_name(code: str) -> str | None:
    df = load_krx()
    code = str(code).zfill(6)
    row = df[df["Code"] == code]
    if row.empty:
        return None
    return row.iloc[0]["Name"]
