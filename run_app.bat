@echo off
echo Starting UTAS-AI Application...
echo.
echo Make sure Ollama is running at http://localhost:11434
echo.
cd app
..\venv\Scripts\python.exe main.py
pause

