#!/usr/bin/env pwsh
Write-Host "Activating virtual environment and starting Flask app..."
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1
python app.py
