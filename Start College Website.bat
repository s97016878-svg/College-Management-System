@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
  echo Python Launcher was not found. Install Python and enable the py launcher, then try again.
  pause
  exit /b 1
)

py -c "import django" >nul 2>&1
if errorlevel 1 (
  echo Installing backend dependencies...
  py -m pip install -r "%~dp0backend\requirements.txt"
  if errorlevel 1 goto failed
)

pushd "%~dp0backend"
py manage.py migrate
if errorlevel 1 goto failed_backend

py manage.py shell -c "from django.contrib.auth import get_user_model; raise SystemExit(0 if get_user_model().objects.filter(is_staff=True).exists() else 1)" >nul 2>&1
if errorlevel 1 (
  echo Create a staff account to sign in to the dashboard.
  py manage.py createsuperuser
  if errorlevel 1 goto failed_backend
)

powershell -NoProfile -Command "try { $page = Invoke-WebRequest -Uri 'http://127.0.0.1:8000' -UseBasicParsing -TimeoutSec 2; if ($page.Content.Contains('CampusPro')) { exit 0 } } catch {}; exit 1" >nul 2>&1
if not errorlevel 1 (
  echo CampusPro is already running. Opening the existing app...
  start "" "http://127.0.0.1:8000"
  popd
  goto success
)

for /f %%P in ('powershell -NoProfile -Command "$ports = 8000..8020; foreach ($candidate in $ports) { if (-not (Get-NetTCPConnection -LocalPort $candidate -State Listen -ErrorAction SilentlyContinue)) { Write-Output $candidate; exit 0 } }; exit 1"') do set "PORT=%%P"
if not defined PORT (
  echo Could not find an available port between 8000 and 8020.
  goto failed_backend
)

echo Starting CampusPro at http://127.0.0.1:%PORT% ...
start "CampusPro Backend" /D "%~dp0backend" py manage.py runserver 127.0.0.1:%PORT%
powershell -NoProfile -Command "$url = 'http://127.0.0.1:%PORT%'; $deadline = (Get-Date).AddSeconds(45); do { try { $page = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2; if ($page.StatusCode -eq 200 -and $page.Content.Contains('CampusPro')) { Start-Process $url; exit 0 } } catch {}; Start-Sleep -Milliseconds 400 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
  echo The backend did not become ready. Check the CampusPro Backend window for errors.
  goto failed_backend
)
popd
goto success

:failed_backend
popd
:failed
echo Startup failed. Review the message above and try again.
pause
exit /b 1

:success
echo CampusPro is open in your browser. Keep the backend window open while using it.
pause
exit /b 0