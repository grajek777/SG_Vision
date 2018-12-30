import cv2
from PIL import Image, ImageTk

from picamera.array import PiRGBArray
import time


def show_frame(temp, c, lmain):
    cv2image = cv2.cvtColor(temp, cv2.COLOR_BGR2RGBA)
    resized_img = cv2.resize(cv2image, (640, 480))
    cv2.drawContours(resized_img, c, -1, (0, 255, 0), 2)
    img = Image.fromarray(resized_img)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)

# test functions
def test_DrawImg(temp, lmain):
    cv2image = cv2.cvtColor(temp, cv2.COLOR_BGR2HSV)
    resized_img = cv2.resize(cv2image, (640, 480))
    img = Image.fromarray(resized_img)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)