## セットアップ

このプロジェクトは **PySide6** を用いた Qt アプリケーションです。初回は次のコマンドで依存関係をインストールしてください。

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> **補足**: 旧来の PyQt 依存は取り除かれているため、既存の仮想環境を流用する場合は `pip uninstall PyQt5 PyQt6 -y` で競合を除去してください。

## 実装ルール

ルートディレクトリに、各機能のディレクトリを作成し、`QtWidgets.QWidget` を継承したウィジェットを実装してください。
全体で用いるようなシステム機能(サウンド再生等)や、小さいツール(ポートスキャン等)を除き、オブジェクト指向プログラミングの原則に従い、クラスを適切に分割し、再利用性を高めるよう心掛けてください。

※自分の担当機能以外は基本的に触らない。

※キャラクターの制御はmainで生成されるAsyncUnityControllerのインスタンス、「controller」を用いて制御すること。
個別にコントローラーを生成しないこと。

コントローラーのメソッド呼び出し例:
```python
class sample:
    def __init__(self, controller):
        self.ctrl = controller
        self.smile_time = 1000
    
    def smile(self):
        self.ctrl.smile(self.smile_time)
```


- コメントアウトがなくてもコードの意図が明確になるレベルに、変数名や関数名は分かりやすくすること。(ただし、適宜コメントアウトも行うこと。)

## ライセンス

プロジェクト本体は [MIT License](LICENSE) の下で提供されます。

サードパーティライブラリのライセンス一覧と原文は [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) および `licenses/` ディレクトリを参照してください。LGPL ライブラリをバンドルする際は、再リンク可能な形での提供などライセンス要件を満たすようにしてください。