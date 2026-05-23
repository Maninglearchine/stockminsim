FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 (BeautifulSoup lxml 파서 등)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 빌드 단계에서 모델 다운로드 (런타임 콜드스타트 방지)
COPY scripts/download_model.py scripts/download_model.py
RUN python scripts/download_model.py

# 소스 복사
COPY . .

# Railway는 PORT 환경변수를 주입함
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
