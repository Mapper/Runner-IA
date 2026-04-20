@echo off
cd /d %~dp0
python -m pip install --upgrade pip
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name RunnerIA runner_ia_gui.py
echo.
echo Executável gerado em dist\RunnerIA.exe
pause
