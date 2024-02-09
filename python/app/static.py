import os
import sys
from flask import Blueprint, send_from_directory
# Blueprintのオブジェクトを生成する

static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "js","dist"))
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # pyinstaller option --add-data "..\js\dist:dist" is assumed.
    static_folder = os.path.abspath(os.path.join(sys._MEIPASS,"dist"))


app = Blueprint(
    'static',
    __name__,
    static_folder=static_folder, # static_folder is js/dist or dist
    static_url_path=""           # assing url "/" to static folder
)

# static setting for Vite
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/assets/<path:path>")
def send_js(path):
    return send_from_directory(app.static_folder, "assets/"+path)
