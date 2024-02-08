# このコードのベース
# Python + FlaskでWebSocketを使う サンプルコード
#  https://wonderhorn.net/programming/flaskwebsocket.html

# このドキュメントをベースに進化させる。
# Flask-SocketIO
#  https://flask-socketio.readthedocs.io/en/latest/index.html

# pyinstllerでエラーが出る対応
#Invalid async_mode specified
# https://github.com/miguelgrinberg/python-socketio/issues/35#issuecomment-1885028967
#add to the hidden imports in spec file
#
#hiddenimports=[ 'flask_socketio','engineio'], # なくても動いた！！
#add his line into your server
#
#from engineio.async_drivers import threading
#and i update the socket to :
#
#socket = SocketIO(app, cors_allowed_origins="*",async_mode="threading")
#

# ViteビルドのHTMLファイルをFlaskで読み込む
#  [Flask/API/Application Object](https://flask.palletsprojects.com/en/3.0.x/api/#application-object)
#  Flask()のコンストラクタ引数
#    static_url_pathに""を、
#    static_folderに"dist"を指定することで、
#    Viteのbuild結果を参照するようになる。
#
#    static_url_path (Optional[str])
#      can be used to specify a different path for the static files on the web.
#      Defaults to the name of the static_folder folder.
#    static_folder (Optional[Union[str, os.PathLike]])
#      The folder with static files that is served at static_url_path.
#      Relative to the application root_path or an absolute path. Defaults to 'static'.
#  参考:[ViteビルドのHTMLファイルをFlaskで読み込む](https://qiita.com/kiyuka/items/6b7b70b4265728b1a6c3)

import time
import sys
import os
import mimetypes
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, send, emit
from engineio.async_drivers import threading # pyinstaller対策

# 起動時の警告メッセージ除去する方法のはずだが、、、
# https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356 
### ここから
#from flask import Flask
#import sys
#cli = sys.modules['flask.cli']
#cli.show_server_banner = lambda *x: None
### ここまで

# https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356?permalink_comment_id=3693485#gistcomment-3693485
### ここから
#import os
#os.environ["WERKZEUG_RUN_MAIN"] = "true"
### ここまで

# https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356?permalink_comment_id=3588517#gistcomment-3588517
### ここから
#from flask import cli
#cli.show_server_banner = lambda *_: None
### ここまで

# exeで走ってる時と、scriptで走ってる時を識別してstatic_folder設定値を変える
#  Pyinstaller/Run-time Information
#   https://pyinstaller.org/en/stable/runtime-information.html?highlight=_MEIPASS#run-time-information

static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "js","dist"))
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    static_folder = os.path.abspath(os.path.join(sys._MEIPASS,"dist"))

print(static_folder)
#app = Flask(__name__)
app = Flask(
    __name__,
    static_folder=static_folder, # Viteのbuild結果をstaticにサービスするための設定
    static_url_path=""    # Viteのbuild結果をstaticにサービスするための設定
)

print(app.static_folder)

# MIME type of "text/plain" 対応。
mimetypes.add_type("application/javascript", ".js")

#sio = SocketIO(app)  # socketを初期化
sio = SocketIO(
    app,
#    cors_allowed_origins="*",
    async_mode="threading"  # pyinstaller対策
)

@sio.on("ping")  # pingイベントが届いたら呼ばれるコールバック
def ping(data):
    print(data)
    print(time.time())
    emit("pong", str(time.time()))
 
# Viteのbuild結果をstaticにサービスするための設定
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/assets/<path:path>")
def send_js(path):
    return send_from_directory(app.static_folder, "assets/"+path)

if __name__ =="__main__":
    try:
        sio.run(app, host="0.0.0.0", port=5001)
    except Exception as e:
        print(e)
    print("Hit enter to exit")
    input()