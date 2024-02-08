cd /d %~dp0
cd js
call npm install

cd /d %~dp0
cd python
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

pause