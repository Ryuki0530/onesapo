# Third-Party Licenses

このプロジェクトでは、下表に示すサードパーティ製ライブラリを使用しています。配布物を公開する場合は、各ライセンスの条件を遵守してください。特に **LGPL** 系ライブラリについては、動的リンクの許可・改変したライブラリの提供手段・利用者への再リンク手段の確保等が必要になります。

## 使用ライブラリ一覧

| パッケージ | バージョン | ライセンス | 主な義務/注意点 |
| --- | --- | --- | --- |
| PySide6 | 6.9.2 | LGPL-3.0-only | LGPL の条件で再配布。動的リンクと再リンク手段の提供。 |
| PySide6_Addons | 6.9.2 | LGPL-3.0-only | PySide6 と同様。 |
| PySide6_Essentials | 6.9.2 | LGPL-3.0-only | PySide6 と同様。 |
| shiboken6 | 6.9.2 | LGPL-3.0-only | PySide6 と同様。 |
| ffpyplayer | 4.5.3 | LGPL-3.0 | 動的リンクまたはソース公開など、LGPL v3 の条件に従う。 |
| pygame | 2.6.1 | LGPL-2.1-or-later | 動的リンクまたは差し替え可能な形で提供する。 |
| dlib | 20.0.0 | Boost Software License 1.0 | ライセンス表示の保持。 |
| numpy | 2.2.6 | BSD 3-Clause License | ライセンス表示と免責文の保持。 |
| opencv-python | 4.12.0.88 | Apache License 2.0 | NOTICE の維持、特許条項への同意。 |
| playsound | 1.3.0 | MIT License | 著作権表示とライセンス文の保持。 |
| pydub | 0.25.1 | MIT License | 同上。 |
| simpleaudio | 1.0.4 | MIT License | 同上。 |
| tinytag | 2.1.2 | MIT License | 同上。 |

> **PySide6/PySide6_Addons/PySide6_Essentials/shiboken6** は複数ライセンス (LGPL-3.0-only / GPL-2.0-only / GPL-3.0-only) で提供されています。本プロジェクトでは LGPL-3.0-only として利用します。

## ライセンス原文

以下のファイルに、各ライセンスの原文を同梱しています。配布物にも同梱するようにしてください。

- [GNU Lesser General Public License v3.0](licenses/LGPL-3.0.txt) — PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 / ffpyplayer
- [GNU Lesser General Public License v2.1](licenses/LGPL-2.1.txt) — pygame
- [Boost Software License 1.0](licenses/Boost-1.0.txt) — dlib
- [BSD 3-Clause License](licenses/BSD-3-Clause.txt) — numpy
- [Apache License 2.0](licenses/Apache-2.0.txt) — opencv-python
- [MIT License](licenses/MIT.txt) — playsound / pydub / simpleaudio / tinytag

バイナリ配布時は、これらのライセンスファイルを利用者が確認できる形で同梱し、LGPL ライブラリについては再リンクやソース入手手段を案内してください。
