@echo off
title Laptop Price Scraper & Master Compiler
color 0A
cd /d "%~dp0"
python scrape_and_compile.py
set "scrape_result=%ERRORLEVEL%"
pause
exit /b %scrape_result%
