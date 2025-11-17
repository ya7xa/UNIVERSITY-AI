Write-Host "Starting UTAS-AI Application..." -ForegroundColor Green
Write-Host ""
Write-Host "Make sure Ollama is running at http://localhost:11434" -ForegroundColor Yellow
Write-Host ""
cd app
..\venv\Scripts\python.exe main.py

