Write-Host "Installing smallest Ollama models for UTAS-AI..." -ForegroundColor Green
Write-Host ""
Write-Host "This will download the following models:" -ForegroundColor Yellow
Write-Host "- tinyllama (chat model, ~637MB)"
Write-Host "- nomic-embed-text (embedding model, ~137MB)"
Write-Host "- llava:7b (vision model, ~4.7GB)"
Write-Host ""
Write-Host "Press any key to continue or CTRL+C to cancel..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "Pulling chat model (tinyllama)..." -ForegroundColor Cyan
ollama pull tinyllama

Write-Host ""
Write-Host "Pulling embedding model (nomic-embed-text)..." -ForegroundColor Cyan
ollama pull nomic-embed-text

Write-Host ""
Write-Host "Pulling vision model (llava:7b)..." -ForegroundColor Cyan
ollama pull llava:7b

Write-Host ""
Write-Host "Done! All models installed." -ForegroundColor Green

