import os
import cv2
import dlib
import numpy as np
import time

DEFAULT_PREDICTOR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "data", "shape_predictor_68_face_landmarks.dat"
)

def calc_ear(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

LEFT_EYE_IDX = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_IDX = [42, 43, 44, 45, 46, 47]

class SleepDetector:
    def __init__(self, device=0, predictor_path: str = None, view=False):
        self.device = device
        self.view = view
        self.cap = cv2.VideoCapture(self.device)
        if not self.cap.isOpened():
            raise RuntimeError("カメラが開けません")

        self.predictor_path = predictor_path or DEFAULT_PREDICTOR_PATH

        if not os.path.isfile(self.predictor_path):
            print(f"[SleepDetector] predictor未発見: {self.predictor_path}")
            print("  → フォールバック: 検出常に False")
            self._predictor = None
        else:
            try:
                self._predictor = dlib.shape_predictor(self.predictor_path)
            except Exception as e:
                print(f"[SleepDetector] predictor読み込み失敗: {e}")
                self._predictor = None

        self._detector = dlib.get_frontal_face_detector()

        self.ear_thresh = 0.20           # EAR閾値
        self.closed_sec_thresh = 2.0     # 連続閉眼秒数
        self.frame_rate = 10             # 1秒あたりフレーム数

    def detect(self):
        if self._predictor is None:
            # モデル無い場合は検出不能→常に起きている扱い
            return False, "predictor missing"

        frames = []
        start = time.time()
        while time.time() - start < self.closed_sec_thresh:
            ret, frame = self.cap.read()
            if not ret:
                return False, "capture error"
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._detector(gray)
            ear = 1.0
            if faces:
                shape = self._predictor(gray, faces[0])
                coords = np.array([[p.x, p.y] for p in shape.parts()])
                left_eye = coords[LEFT_EYE_IDX]
                right_eye = coords[RIGHT_EYE_IDX]
                left_ear = calc_ear(left_eye)
                right_ear = calc_ear(right_eye)
                ear = (left_ear + right_ear) / 2.0

                if self.view:
                    for idx in LEFT_EYE_IDX + RIGHT_EYE_IDX:
                        pt = (coords[idx][0], coords[idx][1])
                        cv2.circle(frame, pt, 2, (0,255,0), -1)
                    cv2.putText(frame, f'EAR: {ear:.2f}', (10,30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                    cv2.imshow("Debug", frame)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
            frames.append(ear)
            time.sleep(1.0 / self.frame_rate)

        closed = [v < self.ear_thresh for v in frames]
        closed_ratio = sum(closed) / len(closed) if frames else 0
        closed_sec = closed_ratio * self.closed_sec_thresh
        if closed_sec >= self.closed_sec_thresh * 0.9:
            info = f"EAR={np.mean(frames):.2f} / {closed_sec:.1f}s"
            return True, info
        return False, f"EAR={np.mean(frames):.2f} / {closed_sec:.1f}s"

    def release(self):
        if hasattr(self, "cap") and self.cap:
            self.cap.release()
        if self.view:
            cv2.destroyAllWindows()