import cv2
import time
import handmodule as hm
import pyautogui
import math

class SwipeDetector:
    def __init__(self, frame_count=10, swipe_threshold=150, fist_threshold=15):
        self.positions = []
        self.frame_count = frame_count
        self.swipe_threshold = swipe_threshold
        self.fist_threshold = fist_threshold
        self.last_swipe_time = time.time()
        self.debounce_time = 0.5
        self.fist_closed = False

    def update_positions(self, lmList):
        if len(lmList) == 0:
            return False

        # Positions of all fingertips (indexes: 4, 8, 12, 16, 20 for thumb to pinky)
        current_positions = [lmList[i][1] for i in [4, 8, 12, 16, 20]]
        self.positions.append(current_positions)

        if len(self.positions) > self.frame_count:
            self.positions.pop(0)

        return len(self.positions) == self.frame_count

    def detect_swipe(self):
        if len(self.positions) != self.frame_count:
            return None

        start_positions = [pos[0] for pos in zip(*self.positions)]
        end_positions = [pos[-1] for pos in zip(*self.positions)]

        if time.time() - self.last_swipe_time > self.debounce_time:
            if all(end - start < -self.swipe_threshold for start, end in zip(start_positions, end_positions)):
                self.last_swipe_time = time.time()
                self.positions.clear()
                return 'forward'
            elif all(end - start > self.swipe_threshold for start, end in zip(start_positions, end_positions)):
                self.last_swipe_time = time.time()
                self.positions.clear()
                return 'backward'

        return None

    def detect_fist(self, lmList):
        if len(lmList) == 0:
            return False

        # Calculate distances between fingertips and palm center (landmark 0)
        distances = [
            math.hypot(lmList[i][1] - lmList[0][1], lmList[i][2] - lmList[0][2])
            for i in [4, 8, 12, 16, 20]
        ]

        # If all distances are below the threshold, consider it a fist
        if all(d < self.fist_threshold for d in distances):
            self.fist_closed = True
            return True
        else:
            self.fist_closed = False
            return False

def main():
    cap = cv2.VideoCapture(0)
    detector = hm.HandDetector(detectionCon=0.7, trackCon=0.7)
    swipe_detector = SwipeDetector()

    while True:
        success, img = cap.read()
        if not success:
            break

        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=True)

        if swipe_detector.update_positions(lmList):
            if not swipe_detector.fist_closed:
                swipe_type = swipe_detector.detect_swipe()
                if swipe_type == 'forward':
                    pyautogui.press('left')
                    print("Swipe forward detected")
                elif swipe_type == 'backward':
                    pyautogui.press('right')
                    print("Swipe backward detected")

        if swipe_detector.detect_fist(lmList):
            print("Fist detected!")

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()