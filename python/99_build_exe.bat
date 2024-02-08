cd /d %~dp0

call .venv\Script\activate.bat

pyinstaller main.py --onefile --add-data "..\js\dist:dist" --distpath exe

pause