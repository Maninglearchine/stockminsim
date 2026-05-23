@echo off
cd /d %~dp0
echo 네이버 종토방 민심 검색 봇 서버를 시작합니다...

rem 서버 기동 후 브라우저 자동 오픈 (별도 프로세스로 5초 대기)
start /b "" cmd /c "timeout /t 5 /nobreak > nul && start http://localhost:8000"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
