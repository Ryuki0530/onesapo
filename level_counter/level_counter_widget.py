# timer_tool/timer_widget.py
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
QtKeep = QtCore.Qt.AspectRatioMode.KeepAspectRatio
QtIgnore = QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
QtSmooth = QtCore.Qt.TransformationMode.SmoothTransformation
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSlider
)

import datetime

from tools.event_bus import EventBus
from sound_effects import VoiceService
from user_data_manager.config_data import ConfigData
from user_data_manager.save_data import SaveData
from unity.async_unity_controller import AsyncUnityController

class LevelCounterWidget(QtWidgets.QWidget):

    def __init__(self, controller : AsyncUnityController, voice_service: VoiceService, event_bus: EventBus, config: ConfigData, save_data: SaveData, parent=None):
        super().__init__(parent)

        self.MAX_EXP : int = 1000  # 最大経験値
        self.MAX_LEVEL : int = 5  # 最大レベル
        self.ctrl = controller
        self.voice_service = voice_service
        self.event_bus = event_bus
        self.config = config
        self.save_data = save_data

        self.debug_mode = self.config.get("debug_mode") # デバッグモード情報の取得
        
        # セーブデータから値を取得し、Noneの場合はデフォルト値を設定
        self.friendship_level = save_data.get("relationship")
        if self.friendship_level is None:
            self.friendship_level = 1  # デフォルトレベル
            
        self.friendship_exp = save_data.get("relationship_exp")
        if self.friendship_exp is None:
            self.friendship_exp = 0  # デフォルト経験値
            
        self.consecutive_days = save_data.get("consecutive_days")
        if self.consecutive_days is None:
            self.consecutive_days = 0  # デフォルト連続日数

        self.last_clear_date = save_data.get("last_clear_date")
        if not self.last_clear_date:
            self.last_clear_date = datetime.date(2000, 1, 1).strftime("%Y-%m-%d")
        self.last_clear_date = datetime.datetime.strptime(self.last_clear_date, "%Y-%m-%d").date()

        # 作業集中度の評価で用いる指標(イベントで開始を受け取ったらリセット)
        self.game_exit = 0  # ゲームプレイをやめた回数
        self.work_up = 0  # 休憩を取った回数
        self.paused = 0  # 中断した回数

        # 連続日数のリセット判定
        if self.last_clear_date:
            days_diff = (datetime.date.today() - self.last_clear_date).days
            if days_diff > 1:
                self.consecutive_days = 0

        # アニメーション用の変数初期化
        self._anim = None

        # --- UI ---
        #レイアウト背景のデザイン
        palette = self.palette()
        # 背景に画像を設定
        self._bg_pix = QtGui.QPixmap("./assets/level_counter/bg.png")  # ウィジェットの背景画像パス
        self._bg_mode = "stretch_xy"   # "stretch_xy" | "contain" | "cover"
        self._bg_scale_x = 1.0         # 横の倍率（stretch_xy 用）
        self._bg_scale_y = 1.0         # 縦の倍率（stretch_xy 用）
        self._bg_uniform = 1.0         # contain/cover 用の一括スケール（拡大縮小の微調整）

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)


        print(f"[levelCounter] Friendship Level: {self.friendship_level}, Friendship EXP: {self.friendship_exp}")
        self.resize(350, 90)



        """
        ここに、ウィジェットのUI要素を追加。
        """
        # 経験値バー
        self.friendship_level_label = QLabel(f"親密度: {self.friendship_level}")
        self.friendship_level_label.setStyleSheet("font-weight: bold; font-size: 16pt; color: black;")
        self.exp_value_label = QLabel(f"EXP: {self.friendship_exp}")
        self.exp_value_label.setStyleSheet("font-size: 8pt;color:black;")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        initial_exp_percent = self.friendship_exp * 100 // self.MAX_EXP if self.MAX_EXP > 0 else 0
        self.slider.setValue(initial_exp_percent)
        self.slider.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: none;
                height: 10px;
                margin: 0px;
                border-radius: 5px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dcdcdc,
                    stop:1 #f5f5f5
                );
            }

            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #66ccff,
                    stop:1 #3399ff
                );
                border: none;
                height: 10px;
                border-radius: 5px;
            }

            QSlider::add-page:horizontal {
                background: transparent;
                border: none;
                height: 10px;
                border-radius: 5px;
            }

            /* つまみを消す */
            QSlider::handle:horizontal {
                background: transparent;
                border: none;
                width: 0px;
            }

            """    
        )
        # 経験値バーレイアウト
        exp_layout = QtWidgets.QVBoxLayout()
        exp_layout.addWidget(self.friendship_level_label)
        exp_layout.addWidget(self.slider)
        exp_layout.addWidget(self.exp_value_label)

        # デバッガーレイアウト
        if self.debug_mode:
            debug_layout = QHBoxLayout()
            self.increase_button = QtWidgets.QPushButton("経験値+100")
            debug_layout.addWidget(self.increase_button)

        # 連続日数ラベル
        self.consecutive_days_layout = QVBoxLayout()
        self.consecutive_days_text_label = QLabel(" 連続")
        self.consecutive_days_text_label.setStyleSheet("font-size: 8pt; color: black;")
        self.consecutive_days_label = QLabel(f"{self.consecutive_days}")
        self.consecutive_days_label.setStyleSheet("font-weight: bold; font-size: 16pt; color: orange;")
        self.consecutive_days_label2 = QLabel("日目")
        self.consecutive_days_label2.setStyleSheet("font-size: 8pt; color: black;")
        # 連続日数レイアウト
        self.consecutive_days_layout.addWidget(self.consecutive_days_text_label)
        self.consecutive_days_layout.addWidget(self.consecutive_days_label)
        self.consecutive_days_layout.addWidget(self.consecutive_days_label2)

        # マスターレイアウト
        layout = QtWidgets.QHBoxLayout(self)
        friendship_layout = QVBoxLayout()
        friendship_layout.addLayout(exp_layout)
        layout.addLayout(friendship_layout)

        if self.debug_mode:
            friendship_layout.addLayout(debug_layout)

        layout.addLayout(self.consecutive_days_layout)

        # --- 配線 ---
        """
        ここに、各ウィジェットのイベントを接続するコードを記述。
        """

        if self.debug_mode:
            self.increase_button.clicked.connect(self.debug_increase_wrap)

        # --- イベント ---
        self.event_bus.on("timer.started", self.reset_counters)
        self.event_bus.on("game_checker.game_exit", self.inc_game_exit)
        self.event_bus.on("sleep_checker.woke_up", self.inc_work_up)
        self.event_bus.on("timer.paused", self.inc_paused)
        self.event_bus.on("timer.finished", self.timer_cleared)
        self.event_bus.on("GAME_OVER", self.reset_counters)


    """
    ここに、各種ロジックを記述。
    """

    def inc_game_exit(self,dmy):
        self.game_exit += 1
    def inc_work_up(self,dmy):
        self.work_up += 1
    def inc_paused(self,dmy):
        self.paused += 1
    def reset_counters(self,dmy):
        self.game_exit = 0
        self.work_up = 0
        self.paused = 0

    def timer_cleared(self, dmy):
        self.paused = 0
        consecutive_days_updated = False
        will_level_up = False

        if self.last_clear_date == datetime.date.today():
            # 今日すでにクリアしている場合は連続日数を増やさない
            print(f"[levelCounter] Timer already cleared today. No change to consecutive days.")
            consecutive_days_updated = False
        else:
            self.consecutive_days += 1
            consecutive_days_updated = True
            self.event_bus.emit("level_counter.consecutive_days", days = self.consecutive_days)
        self.last_clear_date = datetime.date.today()
        self.consecutive_days_label.setText(f"{self.consecutive_days}")
        self.save_data.set({
            "consecutive_days": int(self.consecutive_days),
            "last_clear_date": self.last_clear_date.strftime("%Y-%m-%d")
        })
        
        print(f"[levelCounter] Timer Cleared! Consecutive Days: {self.consecutive_days}, Last Clear Date: {self.last_clear_date}")
        print(f"[levelCounter] Game Exits: {self.game_exit}, Work Ups: {self.work_up}, Paused: {self.paused}")
        exp = 100  # 基本クリア報酬
        # 連続日数ボーナス
        if self.consecutive_days >= 5 and consecutive_days_updated:
            print(f"[levelCounter] Consecutive Days Bonus: 50")
            exp += 50
        elif self.consecutive_days >= 3 and consecutive_days_updated:
            print(f"[levelCounter] Consecutive Days Bonus: 30")
            exp += 30
        elif self.consecutive_days >= 2 and consecutive_days_updated:
            print(f"[levelCounter] Consecutive Days Bonus: 10")
            exp += 10
        # 作業集中度ボーナス
        if self.game_exit == 0 and self.work_up == 0 and self.paused == 0:
            print(f"[levelCounter] Focused Work Bonus: 50")
            exp += 50
        elif self.game_exit == 0 and self.work_up == 0:
            print(f"[levelCounter] Focused Work Bonus: 30")
            exp += 30
        elif self.game_exit <= 1:
            print(f"[levelCounter] Focused Work Bonus: 10")
            exp += 10

        # レベルアップ判定
        next_exp = self.friendship_exp + exp
        if next_exp >= self.MAX_EXP and self.friendship_level < self.MAX_LEVEL:
            will_level_up = True

        self.increase_exp(exp) # 経験値増加処理
        self.reset_counters(None)  # カウンターリセット

        # クリア演出
        if will_level_up:
            self.level_up_performance()
        elif consecutive_days_updated:
            self.consecutive_days_performance()
        else:
            self.normal_clear_performance()
            
    def level_up_performance(self):
        """レベルアップ時のパフォーマンス（音声再生など）"""
        self.ctrl.smile(500)
        voice_name = f"レベルアップ{self.friendship_level}"
        self.voice_service.play_async(voice_name)

    def consecutive_days_performance(self):
        """連続クリア日数のパフォーマンス（音声再生など）"""
        self.ctrl.smile(500)
        self.voice_service.play_async_random("レンゾク", 1, 3)

    def normal_clear_performance(self):
        """通常クリア時のパフォーマンス（音声再生など）"""
        self.ctrl.smile(500)
        self.voice_service.play_async_random("シュウリョウ", 1, 4)



    def debug_increase_wrap(self):
            print(f"[levelCounter] Debug Increase: 100")
            self.increase_exp(100)

    def increase_exp(self, amount: int):
        if self.friendship_level >= self.MAX_LEVEL:
            return  # 最大レベルに達している場合は何もしない
        
        print(f"[levelCounter] Increasing EXP by {amount}")
        new_exp = self.friendship_exp + amount
        
        if new_exp >= self.MAX_EXP:
            # レベルアップ処理
            old_level = self.friendship_level
            self.friendship_level += 1
            self.event_bus.emit("level_counter.level_up", level = self.friendship_level)
            self.friendship_exp = new_exp - self.MAX_EXP
            if self.friendship_level > self.MAX_LEVEL:
                self.friendship_level = self.MAX_LEVEL
                self.friendship_exp = self.MAX_EXP  # 最大経験値で固定
            
            # レベルアップアニメーション（一度最大まで上げてから新しい値に下げる）
            self._animate_level_up(old_level, self.friendship_level, self.friendship_exp)
        else:
            # 通常の経験値増加
            self.friendship_exp = new_exp
            # UI更新
            self.friendship_level_label.setText(f"親密度: {self.friendship_level}")
            self.exp_value_label.setText(f"EXP: {self.friendship_exp}")
            self._animate_slider_to(self.friendship_exp * 100 // self.MAX_EXP)

        # セーブデータ更新
        self.save_data.set({
            "relationship": self.friendship_level,
            "relationship_exp": self.friendship_exp
        })

    def _animate_slider_to(self, target_value: int):
        """スライダーを指定値までアニメーションで移動"""
        if self._anim is not None:
            self._anim.stop()
            self._anim.deleteLater()
            self._anim = None

        current_value = self.slider.value()
        self._anim = QPropertyAnimation(self.slider, b"value", self)
        self._anim.setStartValue(current_value)
        self._anim.setEndValue(target_value)
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _animate_level_up(self, old_level: int, new_level: int, final_exp: int):
        """レベルアップ時の特別なアニメーション"""
        # Step 1: 経験値バーを最大まで上げる
        current_exp_percent = self.slider.value()
        
        # 進行中のアニメーションがあれば止める
        if self._anim is not None:
            self._anim.stop()
            self._anim.deleteLater()
            self._anim = None

        # まず最大値(100%)まで上げるアニメーション
        self._anim = QPropertyAnimation(self.slider, b"value", self)
        self._anim.setStartValue(current_exp_percent)
        self._anim.setEndValue(100)
        self._anim.setDuration(500)  # 0.5秒で最大まで
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # アニメーション完了後の処理
        def on_max_reached():
            # レベル表示を更新
            self.friendship_level_label.setText(f"親密度: {new_level}")
            self.exp_value_label.setText(f"EXP: {final_exp}")
            
            # Step 2: 新しい経験値値まで下げる
            final_exp_percent = final_exp * 100 // self.MAX_EXP
            
            self._anim = QPropertyAnimation(self.slider, b"value", self)
            self._anim.setStartValue(100)
            self._anim.setEndValue(final_exp_percent)
            self._anim.setDuration(300)  # 0.3秒で新しい値まで下げる
            self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self._anim.start()
        
        self._anim.finished.connect(on_max_reached)
        self._anim.start()

   
    def paintEvent(self, e):
        super().paintEvent(e)
        if self._bg_pix.isNull():
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = self.rect()
        pix = self._bg_pix
        pw, ph = pix.width(), pix.height()
        if pw == 0 or ph == 0:
            return

        # ターゲットサイズ計算
        if self._bg_mode == "stretch_xy":
            # 縦横を独立にスケール（比率を自由に調整したいとき）
            tw = int(rect.width()  * self._bg_scale_x)
            th = int(rect.height() * self._bg_scale_y)
            scaled = pix.scaled(tw, th, QtIgnore, QtSmooth)

        elif self._bg_mode == "contain":
            # 画像全体が収まるように等倍スケール（黒帯が出る可能性）
            s = min(rect.width() / pw, rect.height() / ph) * self._bg_uniform
            tw, th = max(1, int(pw * s)), max(1, int(ph * s))
            scaled = pix.scaled(tw, th, QtKeep, QtSmooth)

        elif self._bg_mode == "cover":
            # 埋め尽くす（はみ出し切り抜きあり）
            s = max(rect.width() / pw, rect.height() / ph) * self._bg_uniform
            tw, th = max(1, int(pw * s)), max(1, int(ph * s))
            scaled = pix.scaled(tw, th, QtKeep, QtSmooth)

        else:
            # 想定外の指定は等倍contain扱い
            s = min(rect.width() / pw, rect.height() / ph)
            tw, th = max(1, int(pw * s)), max(1, int(ph * s))
            scaled = pix.scaled(tw, th, QtKeep, QtSmooth)

        # 中央配置
        target = QtCore.QRect(0, 0, scaled.width(), scaled.height())
        target.moveCenter(rect.center())

        painter.drawPixmap(target, scaled)