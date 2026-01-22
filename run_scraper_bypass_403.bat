@echo off
echo Starting Web Scraper (Bypass 403 Mode)...
echo.
echo This mode uses visible browser and delays to bypass 403 errors
echo.
REM Change the URL below to your desired website
python scraper.py https://example.com --no-headless --delay
echo.
echo Press any key to exit...
pause >nul
