@echo off
cd /d %~dp0
echo 네이버 종토방 민심 검색 봇 서버를 시작합니다...
echo http://localhost:8000 에서 접속하세요
uvicorn main:app --host 0.0.0.0 --port 8000
pause
