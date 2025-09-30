<p align="center">
    <img src="assets/logo/onesapo_logo.jpg" alt="OneSapo ロゴ" width="240"/>
</p>


# OneSapo - 作業集中支援アプリケーション

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.9.2-green.svg)

**OneSapo**は、作業集中支援アプリケーションです。東京電機大学 HackU参加チーム「不健全紳士」によって開発されました。

## ✨ 主な機能

### 🎯 タイマー機能
- 30分間の作業タイマー
- 視覚的なカウントダウン表示
- 作業完了時の音声フィードバック

### 😴 睡眠監視システム
- Webカメラを使用したリアルタイム睡眠検出
- 居眠り時の音声アラート機能
- 段階的な警告システム（3段階）

### 🎮 ゲーム監視機能
- バックグラウンドでのゲームプロセス検出
- 作業中のゲーム起動を自動検知
- 集中度評価への反映

### 📊 レベルシステム
- 作業時間に基づく経験値とレベル
- 連続作業日数の記録
- 作業集中度によるボーナス計算
- レベルアップ時の特別演出

### 🎵 BGMプレイヤー
- 作業用BGMの再生機能
- 音量調整とプレイリスト管理
- シンプルで直感的なUI

### 🎤 キャラクターボイス
- 作業進行に応じた音声フィードバック
- 複数キャラクターの音声データ対応

## 🚀 クイックスタート

### 必要環境
- **Python 3.12系での動作確認済み**
- **Webカメラ** (睡眠監視機能用)
- **Windows** 

### インストール

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/Ryuki0530/onesapo.git
   cd onesapo
   ```

2. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **アプリケーションの起動**
   ```bash
   python main.py
   ```

## 📁 プロジェクト構造

```
onesapo/
├── main.py                 # メインアプリケーション
├── requirements.txt        # 依存関係
├── LICENSE                # MITライセンス
├── THIRD_PARTY_LICENSES.md # サードパーティライセンス
├── data/
│   ├── config.json        # 設定データ
│   ├── save_data.json     # セーブデータ
│   └── game_words.txt     # ゲーム検出用キーワード
├── assets/                # リソースファイル
├── timer/                 # タイマー機能
├── sleep_checker/         # 睡眠監視機能
├── game_process_checker/  # ゲーム監視機能
├── level_counter/         # レベルシステム
├── music/                 # BGMプレイヤー
├── sound_effects/         # 音声システム
├── unity/                 # Unity統合機能
└── user_data_manager/     # データ管理
```

## ⚙️ 設定

### 主要設定項目

- **音量設定**: BGMとボイスの音量調整
- **応援頻度**: キャラクターの応援間隔（分単位）
- **睡眠検出感度**: カメラによる睡眠検出の精度調整
- **ゲーム監視間隔**: プロセス監視の頻度設定
- **外部レンダリングシステムのパス**:　Unity等の外部レンダリングシステムの実行ファイルパスを指定 

設定は `data/config.json` で管理され、UIから変更可能です。

## 🎮 使用方法

1. **作業開始**: タイマーウィジェットで作業時間を設定し、開始ボタンをクリック
2. **監視機能**: 睡眠監視とゲーム監視が自動的に開始
3. **BGM再生**: 音楽ウィジェットから作業用BGMを選択・再生
4. **レベル確認**: レベルカウンターで現在の進捗とレベルを確認
5. **設定調整**: 設定メニューから各種パラメータを調整

## 🛠️ 技術スタック

- **フレームワーク**: PySide6 (Qt for Python)
- **画像処理**: OpenCV, dlib
- **プロセス監視**: Windows API
- **音声処理**: pygame, simpleaudio, pydub
- **データ管理**: JSON ベース
- **外部統合**: Unity エンジン連携

## 📝 ライセンス

プロジェクト本体は [MIT License](LICENSE) の下で提供されます。

### サードパーティライセンス

本プロジェクトは以下のオープンソースライブラリを使用しています：

- **PySide6** (LGPL-3.0) - QtベースのGUIフレームワーク
- **OpenCV** (Apache-2.0) - コンピュータビジョン
- **dlib** (Boost-1.0) - 機械学習ライブラリ
- **NumPy** (BSD-3-Clause) - 数値計算
- **pygame** (LGPL-2.1) - マルチメディア処理

詳細は [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) および `licenses/` ディレクトリを参照してください。LGPL ライブラリをバンドルする際は、再リンク可能な形での提供などライセンス要件を満たすようにしてください。

## 👥 開発チーム

**東京電機大学 HackU参加チーム「不健全紳士」**

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

## 📞 サポート

バグ報告や機能要望は [Issues](https://github.com/Ryuki0530/onesapo/issues) にお寄せください。

---

*OneSapo で効率的な作業環境を実現しましょう！* 🚀