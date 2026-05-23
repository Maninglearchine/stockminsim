from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import stock_search
import crawler
import analyzer

_executor = ThreadPoolExecutor(max_workers=4)

BASE_DIR = Path(__file__).parent

_cache: dict[str, tuple[dict, datetime]] = {}
_CACHE_TTL_SECONDS = 300


def _get_cache(code: str) -> dict | None:
    entry = _cache.get(code)
    if entry:
        data, expires_at = entry
        if datetime.now() < expires_at:
            return data
        del _cache[code]
    return None


def _set_cache(code: str, data: dict, ttl: int = _CACHE_TTL_SECONDS) -> None:
    _cache[code] = (data, datetime.now() + timedelta(seconds=ttl))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] KRX 종목 데이터 로딩 중...")
    stock_search.load_krx()
    print("[startup] 감정분석 모델 로딩 중...")
    analyzer.load_model(str(BASE_DIR / "models" / "KR-FinBert-SC"))
    print("[startup] 준비 완료")
    yield


app = FastAPI(title="Stock Mood AI", lifespan=lifespan)
app.mount("/image", StaticFiles(directory=BASE_DIR / "image"), name="image")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ── 페이지 라우트 ────────────────────────────────────────────

@app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse(request, "main.html")


@app.get("/result")
async def result_page(request: Request):
    return templates.TemplateResponse(request, "result.html")


# ── API 라우트 ───────────────────────────────────────────────

@app.get("/api/search")
async def search(q: str) -> JSONResponse:
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="검색어를 입력하세요.")
    results = stock_search.search_stock(q.strip())
    if not results:
        raise HTTPException(status_code=404, detail="검색 결과가 없습니다.")
    return JSONResponse({"results": results})


@app.get("/api/analyze")
async def analyze_stock(code: str) -> JSONResponse:
    code = str(code).strip().zfill(6)
    name = stock_search.get_stock_name(code)
    if name is None:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

    cached = _get_cache(code)
    if cached:
        return JSONResponse({**cached, "cached": True})

    loop = asyncio.get_event_loop()
    try:
        df_board = await loop.run_in_executor(
            _executor,
            lambda: crawler.crawl_naver_board(code, start_page=1, end_page=10),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"데이터 수집 실패: {e}")

    if df_board.empty:
        raise HTTPException(status_code=502, detail="수집된 게시글이 없습니다.")

    model_path = str(BASE_DIR / "models" / "KR-FinBert-SC")
    try:
        result = await loop.run_in_executor(
            _executor,
            lambda: analyzer.analyze(df_board, local_model_path=model_path),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"감정분석 실패: {e}")

    payload = {
        "code": code,
        "name": name,
        "signal": result["signal"],
        "strength": result["strength"],
        "confidence": result["confidence"],
        "evidence": result["evidence"],
        "analyzed_count": result["analyzed_count"],
        "updated_at": datetime.now().strftime("%H:%M"),
        "cached": False,
    }
    _set_cache(code, payload)
    return JSONResponse(payload)
