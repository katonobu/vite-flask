# 開発メモ

## 最初
[Python + FlaskでWebSocketを使う サンプルコード](https://wonderhorn.net/programming/flaskwebsocket.html)をベースに疎通確認

## exe化
### [pyinstaller](https://pyinstaller.org/en/stable/)でexeにして動かす。
- python実行では問題ないが、exeにすると実行時エラー
    - [Invalid async_mode specified](https://github.com/miguelgrinberg/python-socketio/issues/35#issue-167239547)記載と同じ症状。
    - [srbhgjr commented on Nov 10, 2023](https://github.com/miguelgrinberg/python-socketio/issues/35#issuecomment-1805781817)で解決した。

## viteで開発したweb-appをflaskでサーブ
### vite側
- `npm create vite@latest {ProjectName} -- --template react-ts` で生成。
    - 特に修正せずそのまま。

### flask側
- [ViteビルドのHTMLファイルをFlaskで読み込む](https://qiita.com/kiyuka/items/6b7b70b4265728b1a6c3)を参考に実装。
- Flask()のコンストラクタ引数に下記を設定することで、"/"にアクセスすると、Viteのbuild結果が見えるようになる。
    - static_url_pathに""(クライアントから見て"/"が対応付けられる)
    - static_folderにViteのビルド結果が格納されているdistディレクトリを指定する
- [Flask/API/Application Object](https://flask.palletsprojects.com/en/3.0.x/api/#application-object)
    ```
    static_url_path (Optional[str])
      can be used to specify a different path for the static files on the web.
      Defaults to the name of the static_folder folder.
    static_folder (Optional[Union[str, os.PathLike]])
      The folder with static files that is served at static_url_path.
      Relative to the application root_path or an absolute path. Defaults to 'static'.
    ```
## vite側とflask側のディレクトリ分離
- ごちゃつくのが嫌なので、js,pythonディレクトリに分離。
- 設定すべきstaticディレクトリは下記のとおり。
  - 実行時は直下の"dist"ディレクトリ。
  - python時は"js/dist"ディレクトリ。

- pythonスクリプトの修正
    - exeで走ってる時と、scriptで走ってる時の識別
        - [Pyinstaller/Run-time Information](https://pyinstaller.org/en/stable/runtime-information.html?highlight=_MEIPASS#run-time-information)
- pyinstaller起動時オプション
    - pyinstallerで"js/dist"ディレクトリを、実行時の直下の"dist"として見えるように組み込む。
        - [What To Bundle, Where To Search --add-data SOURCE:DEST](https://pyinstaller.org/en/stable/usage.html#cmdoption-add-data)
    - pyinstallerで出力結果が"dist"ディレクトリに生成されるので混乱する対策。
        - exeディレクトリに生成させるようにする。
        - [Options --distpath DIR](https://pyinstaller.org/en/stable/usage.html#cmdoption-distpath)

## 起動時にブラウザを立ち上げる
- [webbrowser --- 便利なウェブブラウザコントローラー](https://docs.python.org/ja/3/library/webbrowser.html)
    - webbrowserのopen()でブラウザを開く。
    - socket.run()の引数のhost,portと整合させるために変数追加

## BluePrintによるモジュール分割
- [はじめてのFlask導入〜Blueprint適用](https://qiita.com/shimajiri/items/fb7d1d58de0b0d171c88)


# 未解決
## 起動時のメッセージ削除
`WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.`
がうっとぉしい。
- [Prevent_flask_production_environment_warning.py](https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356)
- 下記のいずれも効果なし。
    - 最初に記載されている対策
        ```
        from flask import Flask
        import sys
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None
        ``` 
    - [fagci commented on Jan 10, 2021](https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356?permalink_comment_id=3588517#gistcomment-3588517)
        ```
        from flask import cli
        cli.show_server_banner = lambda *_: None
        ```
    - [bw2 commented on Apr 5, 2021](https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356?permalink_comment_id=3693485#gistcomment-3693485)
        ```
        import os
        os.environ["WERKZEUG_RUN_MAIN"] = "true"
        ```
