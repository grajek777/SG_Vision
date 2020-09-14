import cv2
import os
import datetime
from picamera import PiCamera
from picamera.array import PiRGBArray
import time

class Camera(object):
    
    def __init__(self):
        try:
            self.camera = PiCamera()
            self.camera.resolution = (640, 480)
            # create a default directory where photos will be stored
            self.directory = "/home/pi/python_programs/SG_Vision/Saved_Photos"
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            os.chdir ("/home/pi/python_programs/SG_Vision/Saved_Photos")
        except IOError as e:
            self.camera = None
            print("I/O error({0}): {1} of RPI Camera".format(e.errno, e.strerror))
            raise
    
    def takePhoto(self, save=0):
        rawCapture = PiRGBArray(self.camera, size=(640, 480))
        #allow the camera to warmup
        time.sleep(0.1)
        #grab an image from the camera
        self.camera.capture(rawCapture, format="bgr")
        temp_image = rawCapture.array
        if save==1:
            photoname = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S.jpg")
            cv2.imwrite(photoname,temp_image)
        
        return temp_image
    
    def shutdown(self):
        if self.camera is not None:
            self.camera.close()
            
