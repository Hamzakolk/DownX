@echo off
REM Build DownX.exe (single file, no console window).
REM Put ffmpeg.exe in this folder before building to bundle it with the app.

pip install -r requirements.txt pyinstaller
if exist ffmpeg.exe (
    pyinstaller --noconfirm --onefile --windowed --name DownX --collect-all customtkinter --add-binary "ffmpeg.exe;." main.py
) else (
    pyinstaller --noconfirm --onefile --windowed --name DownX --collect-all customtkinter main.py
)
echo.
echo Done. The app is in dist\DownX.exe
pause
