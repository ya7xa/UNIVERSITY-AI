@echo off
echo Installing smallest Ollama models for UTAS-AI...
echo.
echo This will download the following models:
echo - tinyllama (chat model, ~637MB)
echo - nomic-embed-text (embedding model, ~137MB)
echo - llava:7b (vision model, ~4.7GB)
echo.
echo Press any key to continue or CTRL+C to cancel...
pause
echo.
echo Pulling chat model (tinyllama)...
ollama pull tinyllama
echo.
echo Pulling embedding model (nomic-embed-text)...
ollama pull nomic-embed-text
echo.
echo Pulling vision model (llava:7b)...
ollama pull llava:7b
echo.
echo Done! All models installed.
pause

