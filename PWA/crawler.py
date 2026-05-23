import requests
import time
import random
import re
import html
from bs4 import BeautifulSoup, UnicodeDammit
import pandas as pd


def _extract_int(text) -> int | None:
    if text is None:
        return None
    value = re.sub(r"[^0-9]", "", str(text))
    return int(value) if value else None


def _clean_text(text) -> str:
    if text is None:
        return ""
    text = html.unescape(str(text))
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _decode_html(response) -> tuple[str, str]:
    raw = response.content
    dammit = UnicodeDammit(raw, known_definite_encodings=["utf-8", "cp949", "euc-kr"])
    return dammit.unicode_markup, dammit.original_encoding


def crawl_naver_board(stock_code: str, start_page: int = 1, end_page: int = 10) -> pd.DataFrame:
    stock_code = str(stock_code).zfill(6)
    base_url = "https://finance.naver.com/item/board.naver"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": f"https://finance.naver.com/item/main.naver?code={stock_code}",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    session = requests.Session()
    records = []

    for page in range(start_page, end_page + 1):
        try:
            resp = session.get(
                base_url,
                params={"code": stock_code, "page": page},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()

            html_text, _ = _decode_html(resp)
            soup = BeautifulSoup(html_text, "html.parser")

            for row in soup.select("table.type2 tr"):
                title_td = row.select_one("td.title")
                if title_td is None:
                    continue
                a_tag = title_td.select_one("a")
                if a_tag is None:
                    continue

                title = _clean_text(a_tag.get("title", "") or a_tag.get_text(" ", strip=True))
                if not title:
                    continue

                rec_tag = row.select_one("strong.tah.p10.red01")
                if rec_tag is not None:
                    recommend = _extract_int(rec_tag.get_text(strip=True))
                else:
                    tds = row.find_all("td", recursive=False)
                    recommend = _extract_int(tds[-2].get_text(strip=True)) if len(tds) >= 6 else None

                records.append({"Title": title, "Recommend_Count": recommend})

            time.sleep(random.uniform(0.5, 1.2))

        except Exception as e:
            print(f"[crawler] page {page} error: {e}")
            continue

    df = pd.DataFrame(records)
    if not df.empty:
        df = df[["Title", "Recommend_Count"]]
        df["Recommend_Count"] = df["Recommend_Count"].fillna(0).astype(int)
    return df
