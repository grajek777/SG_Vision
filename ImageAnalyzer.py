import cv2
import numpy as np
from ExpertSystem import *

class ImageAnalyzer(object):
    
    def __init__(self):
        self.expertSystem = ExpertSystem()
        self.width = 640
        self.high = 480

    def findROI(self, temp):
        cv2image = cv2.resize(temp, (self.width, self.high))
        blurred = cv2.GaussianBlur(cv2image, (5, 5), 0)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)[1]
        #find contours of ROI
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[1] # get contours
        
        #cv2.imshow("cv2image", cv2image)
        #cv2.imshow("blurred", blurred)
        #cv2.imshow("gray", gray)
        #cv2.imshow("thresh", thresh)
        #print cnts
        #cv2.waitKey(0)
        
        return cnts
    
    def findROI_2(self, temp):
        
        cv2image = cv2.resize(temp, (self.width, self.high))
        # first phase of finding ROI -> mask all but the central square
        c_x = int(self.width/2)
        c_y = int(self.high/2)
        masked = np.zeros(cv2image.shape,np.uint8)
        masked[(c_y-85):(c_y+85),(c_x-100):(c_x+100)] = cv2image[(c_y-85):(c_y+85),(c_x-100):(c_x+100)]
        cv2.imshow('Masked Image',masked)
        cv2.waitKey(0)

        hsv = cv2.cvtColor(masked, cv2.COLOR_BGR2HSV)
        cv2.imshow('HSV Image',hsv)
        cv2.waitKey(0)

        hue ,saturation ,value = cv2.split(hsv)
        cv2.imshow('Saturation Image',saturation)
        #cv2.imshow('Hue Image',hue)
        cv2.waitKey(0)

        retval, thresholded = cv2.threshold(saturation, 230, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imshow('Thresholded Image',thresholded)
        cv2.waitKey(0)

        medianFiltered = cv2.medianBlur(thresholded,3)
        cv2.imshow('Median Filtered Image',medianFiltered)
        cv2.waitKey(0) 
        cnts = cv2.findContours(medianFiltered.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #gaussianFiltered = cv2.GaussianBlur(thresholded, (5, 5), 0)
        #cv2.imshow('Gaussian Filtered Image',gaussianFiltered)
        #cv2.waitKey(0) 
        #cnts = cv2.findContours(gaussianFiltered.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #cnts = cv2.findContours(thresholded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #for c in cnts:
        #  # compute the center of the contour
        #  #M = cv2.moments(c)
        #  #cX = int(M["m10"] / M["m00"])
        #  #cY = int(M["m01"] / M["m00"])
        #  cv2.drawContours(cv2image, c, -1, (0, 255, 0), -1)
        #  #first = cv2.drawContours(cv2image, [c], -1, (0, 255, 0), 2)
        #  #second =cv2.circle(cv2image, (cX, cY),1 , (255, 255, 255), -1)


        #cv2.imshow('Objects Detected',cv2image)
        #cv2.waitKey(0)
        cnts = cnts[1] # get contours
        return cnts
    
    # function classifyColor(pix)
    # This function classifies color of a pixel based on its hue.
    # pixel has to be provided in HSV format
    def classifyColor(self, pix):
        ret = -1
        Hue = pix.item(0)
    
        # normalized in range 0-180
        if Hue <= 15 or Hue > 165:
            ret = 0
        elif Hue > 15 and Hue <= 45:
            ret = 1
        elif Hue > 45 and Hue <= 75:
            ret = 2
        elif Hue > 75 and Hue <= 105:
            ret = 3
        elif Hue > 105 and Hue <= 135:
            ret = 4
        elif Hue > 135 and Hue <= 165:
            ret = 5
    
        return ret


    def analyzeImageHSV(self, img_HSV):
        colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta']
        result_array = np.zeros(6)
        Saturation_array = np.zeros(6)
        HueAvg = 0
        SatAvg = 0
        ValAvg = 0
        noPix = 0
        
        rows, cols, pix = img_HSV.shape
        for i in range(0, rows):
            for j in range(0, cols):
                #if the sample is bright enough
                if (img_HSV.item(i, j, 2) > 0):
                    # classify color based on hue
                    color = self.classifyColor(img_HSV[i, j, :])
                    if(color != -1 and color <= 5):
                        noPix += 1
                        result_array[color] += 1
                        Saturation_array[color] += img_HSV.item(i, j, 1)
                        # sum values in channels to compute average
                        HueAvg += img_HSV.item(i, j, 0)
                        SatAvg += img_HSV.item(i, j, 1)
                        ValAvg += img_HSV.item(i, j, 2)
                    else:
                        print("ERROR - Unrecognized color")
                        print((img_HSV.item(i, j, 0)))
    
        # determine the most frequent color
        temp = 0
        MFColor = 0
        for i in range(0, len(result_array)):
            print("{0}: {1}".format(colors[i],result_array[i]))
            if result_array[i] > temp:
                MFColor = i
                temp = result_array[i]
        # compute averages
        if(noPix > 0):
            HueAvg = HueAvg/noPix
            SatAvg = SatAvg/noPix
            ValAvg = ValAvg/noPix
        # calculate average saturation of the most frequent color
        if(result_array[MFColor] != 0):
            MFSaturation = Saturation_array[MFColor]/result_array[MFColor]
        else:
            print("WARNING: no color classified")
            return ("no color", 0, 0, 0, 0)
        
        return (colors[MFColor], MFSaturation, HueAvg, SatAvg, ValAvg)
    

    def colorDetection(self, temp, c):
        cv2image = cv2.resize(temp, (self.width, self.high))
        mask = np.zeros(cv2image.shape[:2], dtype="uint8")
        cv2.drawContours(mask, c, -1, 255, -1)
        roi = cv2.bitwise_and(cv2image, cv2image, mask=mask)
    
        cv2.imshow("roi", roi)
        cv2.waitKey(0)
    
        img_HSV = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        (MFColor, MFSaturation, HueAvg, SatAvg, ValAvg) = self.analyzeImageHSV(img_HSV)
        
        return (MFColor, MFSaturation)


    
