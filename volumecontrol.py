import cv2
import time
import numpy as np
import handmodule as hm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
device = AudioUtilities.GetSpeakers()

wCam = 640
hCam = 480

cap = cv2.VideoCapture(1)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = hm.HandDetector(detectionCon=0.7)


interface = device.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
)
volume = cast(interface, POINTER(IAudioEndpointVolume))
#volume.GetMute()
#volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]


while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw = False)
    if len(lmList) !=0:
        #print(lmList[4], lmList[8])

        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2,  (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        #print(length)

        # Volume range -45 - 0
        # Hand Range 50 - 300

        vol = np.interp(length, [20, 250], [minVol, maxVol])
        print(int(length), vol)
        volume.SetMasterVolumeLevel(vol, None)

        if length < 20:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)



    cTime = time.time()
    fps = 1/(cTime-pTime)
    pTime = cTime

    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Img", img)
    cv2.waitKey(1)