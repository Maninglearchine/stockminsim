@echo off
cd /d %~dp0
echo Stock Mood AI 서버를 시작합니다...
echo http://localhost:8000 에서 접속하세요
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
