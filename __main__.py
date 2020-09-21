# file app/__main__.py
#!/usr/bin/python
import pigpio
import time
import Tkinter as tk
import numpy as np 
import ttk
import os
import time
import threading

from PIL import Image, ImageTk
from Camera import *
from ImageAnalyzer import *
from MotorController import *
import camera_utils as cam_util
from Tix import Tk
from subprocess import call

#import sys
#sys.path.append(r'/home/pi/pysrc')
#import pydevd
#pydevd.settrace('192.168.1.103') # replace IP with address 
                                 # of Eclipse host machine

class relayThread (threading.Thread):
    def __init__(self, gpio, pin, button_text, stop_event, delay=(2.0*60.0), debug=False):
        threading.Thread.__init__(self)
        self.delay = delay
        self.gpio = gpio
        self.pin = pin
        self.button_text = button_text
        self.stop_event = stop_event
        self.debug = debug
     
    def waitTime(self):
        for i in range(int(self.delay*2)):
            if self.debug:
                print("{s}".format(s=(0.5*i)))
            time.sleep(0.5)
            if self.stop_event.is_set():
                break
        self.button_text.set("Air on")
        self.gpio.write(self.pin, 1)
        self.stop_event.clear()
    
    #def stop(self):
    #    self.thread_active = False
        
    def run(self):
        self.waitTime()


class LogoScreen(tk.Toplevel):
    def __init__(self,master=None, logo=None):
        tk.Toplevel.__init__(self,master=master)
        self.logo_label = tk.Label(self, image=logo)
        self.logo_label.imgtk = logo
        self.logo_label.pack()
        self.overrideredirect(1)
        

class App(tk.Frame):

    def __init__(self, window):
        # save name of LedRing path which needs to be run in python3
        self.led_ring_script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                      "LedRing.py")
        logo_w = window.winfo_screenwidth()
        logo_h = window.winfo_screenheight()/3
        self.logo_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                      "SG_Papertronics_logo.gif")
        # prepare logo (resize)
        self.logo_img_org = Image.open(self.logo_path)
        resized = self.logo_img_org.resize((logo_w, logo_h),
                                            Image.ANTIALIAS)
        self.logo_imgtk = ImageTk.PhotoImage(resized)
        # create logo
        self.logo = LogoScreen(master=window, logo=self.logo_imgtk)
        self.logo.geometry("%dx%d+%d+%d" % (logo_w,
                                            logo_h,
                                            0, window.winfo_screenheight()/3))
        tk.Frame.__init__(self,master=window)
        self.after(5000,self.logo.destroy)
        
        self.window = window
        #self.LED_Pin_Top  = 18
        self.Relay_Pin    = 5
        self.Setup_Brightness = 20
        self.roi = np.zeros((0, 0))
        self.Lift_Jump_Microsteps = 8500
        self.Time_of_scavenge = 2.0*60.0
        self.TOS_Dictionary = {"2 min" : 2.0*60.0,
                               "5 min" : 5.0*60.0,
                               "10 min" : 10.0*60.0}
        self.waitTosThread = None
        self.waitTos_stop = threading.Event()
        # Create application objects
        self.camera = Camera()
        self.imgAnalyzer = ImageAnalyzer()
        self.motorController = MotorController.create_MC()
        
        
        ControlFrame = tk.LabelFrame(self.window, text="Control", 
                                     width=self.window.winfo_screenwidth(),
                                     height=(self.window.winfo_screenheight()/5))
        ControlFrame.grid(row=0, column=0, padx=0, pady=0)
        ControlFrame.grid_propagate(False)
        AuxFrame = tk.Frame(ControlFrame, 
                            width=self.window.winfo_screenwidth()/6,
                            height=(self.window.winfo_screenheight()/5))
        AuxFrame.grid(row=0, column=0, padx=0, pady=0)
        AuxFrame.grid_propagate(False)
        AuxFrame1 = tk.Frame(ControlFrame, 
                            width=self.window.winfo_screenwidth()/6,
                            height=(self.window.winfo_screenheight()/5))
        AuxFrame1.grid(row=0, column=40, padx=0, pady=0)
        AuxFrame1.grid_propagate(False)
        ##################################################
        #Expert System window
        ##################################################
        # Combobox with Expert Systems
        ExpertComboFrame = tk.LabelFrame(AuxFrame, text="Expert System", 
                                         width=self.window.winfo_screenwidth()/6,
                                         height=self.window.winfo_screenheight())
        ExpertComboFrame.pack()
        ExpertComboFrame.grid_propagate(False)
        #ComboboxFrame.pack()
        self.boxValue = tk.StringVar()
        self.box = ttk.Combobox(ExpertComboFrame, textvariable=self.boxValue, width=15)
        self.box['values'] = ('Expert System 1', 'Expert System 2')
        self.box.current(0)
        self.box.grid(row=0, column=0)
        self.box.bind("<<ComboboxSelected>>", self.comboSelection_callback)
        self.box.pack()
        
        ##################################################
        #Camera window
        ##################################################
        CameraFrame = tk.LabelFrame(ControlFrame, text="Camera", 
                                    width=self.window.winfo_screenwidth()-self.window.winfo_screenheight(),
                                    height=self.window.winfo_screenheight())
        CameraFrame.grid(row=0, column=10, padx=0, pady=0)
        CameraFrame.grid_propagate(False)
        #Find ROI Button
        #self.FROI_button = tk.Button(CameraFrame, text="Find ROI",
        #                             command=self.FindROI_callback)
        #self.FROI_button.pack()
        
        #Take Photo
        self.savePhoto = tk.IntVar()
        self.SavePhotoCheckBox = tk.Checkbutton(CameraFrame, text="Save photo", 
                                                variable=self.savePhoto)
        self.SavePhotoCheckBox.pack()
        self.TP_button = tk.Button(CameraFrame, text="Take a Photo", state="normal",
                                   command=self.TakePhoto_callback)
        self.TP_button.pack()
        
        ##################################################
        #Pneumatics window
        ##################################################
        PneumaticFrame = tk.LabelFrame(AuxFrame1, text="Pneumatics", 
                                       width=self.window.winfo_screenwidth()/6,
                                       height=self.window.winfo_screenheight())
        #PneumaticFrame.grid(row=0, column=40, padx=0, pady=0)
        PneumaticFrame.pack()
        PneumaticFrame.grid_propagate(False)
        #solenoid valve
        self.Relay_button_text = tk.StringVar()
        self.Relay_button_text.set("Air on")
        self.Relay_button = tk.Button(PneumaticFrame, textvariable=self.Relay_button_text,
                                      command=self.Relay_callback)
        self.Relay_button.pack()
        
        self.TOSValue = tk.StringVar()
        self.TOSbox = ttk.Combobox(PneumaticFrame, textvariable=self.TOSValue, width=10)
        self.TOSbox['values'] = ('2 min', '5 min', '10 min')
        self.TOSbox.current(0)
        self.TOSbox.grid(row=0, column=0)
        self.TOSbox.bind("<<ComboboxSelected>>", self.TOS_comboSelection_callback)
        self.TOSbox.pack()
        
        
        ##################################################
        #LED window
        ##################################################
        #Slider knob for TOP LED brightness
        LedRingFrame = tk.LabelFrame(AuxFrame, text="LED RING", 
                                     width=self.window.winfo_screenwidth()/6,
                                     height=self.window.winfo_screenheight())
        LedRingFrame.pack()
        LedRingFrame.grid_propagate(False)
        self.LedRing_button_text = tk.StringVar()
        self.LedRing_button_text.set("LED on")
        self.LedRing_button = tk.Button(LedRingFrame, textvariable=self.LedRing_button_text,
                                        command=self.LedRing_callback)
        self.LedRing_button.pack()
        
        ##################################################
        #Motor Controller  window
        ##################################################
        # Motor Controller 
        if self.motorController is not None:
            MCFrame = tk.LabelFrame(AuxFrame1, text="Motor Controller", 
                                    width=self.window.winfo_screenwidth()-self.window.winfo_screenheight(),
                                    height=self.window.winfo_screenheight())
            #MCFrame.grid(row=1, column=40, padx=0, pady=0)
            MCFrame.pack()
            MCFrame.grid_propagate(False)
            
            ######## Speed Control ########
            #self.MCSpeedSlider = tk.Scale(MCFrame, from_=0, to=self.motorController.ticT825.MAX_SPEED,
            #                              resolution=1, state="normal", orient=tk.HORIZONTAL,
            #                              command=self.MCSpeedSlider_callback)
            #self.MCSpeedSlider.pack()
            #
            #self.dir_var = tk.StringVar()
            #self.MCDownDirRadio = tk.Radiobutton(MCFrame, text="down",
            #                                     variable=self.dir_var,
            #                                     value='down', command=self.MCDirRadio_callback)
            #self.MCDownDirRadio.pack()
            #self.MCDownDirRadio.select()
            #self.MCUpDirRadio = tk.Radiobutton(MCFrame, text="up",
            #                                   variable=self.dir_var,
            #                                   value='up', command=self.MCDirRadio_callback)
            #self.MCUpDirRadio.pack()
            #
            #self.energize_button_text = tk.StringVar()
            #self.energize_button_text.set("Energize")
            #self.MCEnergize_button = tk.Button(MCFrame, textvariable=self.energize_button_text, state="active",
            #                                   command=self.MCEnergize_callback)
            #self.MCEnergize_button.pack()
            
            ######## Position Control ########
            self.Lift_button_text = tk.StringVar()
            self.Lift_button_text.set("Lift Up")
            self.Lift_button = tk.Button(MCFrame, textvariable=self.Lift_button_text,
                                          command=self.Lift_callback)
            self.Lift_button.pack()
        
        ##################################################
        #Summary window
        ##################################################
        SummaryFrame = tk.LabelFrame(ControlFrame, text="Summary", 
                                     width=self.window.winfo_screenwidth()-self.window.winfo_screenheight(),
                                     height=self.window.winfo_screenheight())
        SummaryFrame.grid(row=0, column=50, padx=0, pady=0)
        SummaryFrame.grid_propagate(False)
        #Result label and its frame
        Result = tk.LabelFrame(SummaryFrame, text="Result", width=100, height=50)
        Result.grid_propagate(False)
        Result.pack()
        self.ResultLabel = tk.Label(Result)
        self.ResultLabel.config(text="TEMP_Result", fg="red")
        self.ResultLabel.pack()
        
        #Saturation label and its frame
        SaturationFrame = tk.LabelFrame(SummaryFrame, text="Saturation", width=100, height=50)
        SaturationFrame.grid_propagate(False)
        SaturationFrame.pack()
        self.SaturationLabel = tk.Label(SaturationFrame)
        self.SaturationLabel.config(text="0", fg="black")
        self.SaturationLabel.pack()
        
        ##################################################    
        # Graphics window
        ##################################################
        imageFrame = tk.LabelFrame(self.window, text="Photo", 
                                   width=self.window.winfo_screenwidth(),
                                   height=self.window.winfo_screenheight())
        imageFrame.grid(row=10, column=0, padx=0, pady=0)
        imageFrame.grid_propagate(False)
        
        # Capture video frames
        self.lmain = tk.Label(imageFrame)
        self.lmain.grid(row=0, column=0)
        
        # Setup GPIO 
        self.pi = pigpio.pi()
        self.pi.set_mode(self.Relay_Pin, pigpio.OUTPUT)
        self.pi.write(self.Relay_Pin, 1)
    
    
    def on_closing(self):
        exit_code = call("sudo python3 {0} --turn off".format(self.led_ring_script_path), shell=True)
        self.pi.write(self.Relay_Pin, 1)
        if self.waitTosThread is not None:
            #self.waitTosThread.stop()
            self.waitTos_stop.set()
            self.waitTosThread.join(0.6)
        if self.motorController is not None:
            self.motorController.shutdown()
        if self.camera is not None:
            self.camera.shutdown()
        self.pi.stop()
        self.window.destroy()
    
    
    #def FindROI_callback(self):
    #    #Set top LED to setup phase
    #    self.pi.set_PWM_dutycycle(self.LED_Pin_Top, self.Setup_Brightness)
    #    time.sleep(1.0)
    #    temp_image = self.camera.takePhoto()
    #    #search for ROI
    #    self.roi = np.zeros((0, 0))
    #    self.roi = self.imgAnalyzer.findROI(temp_image)
    #    #turn back to default setting
    #    self.pi.set_PWM_dutycycle(self.LED_Pin_Top, 0)
    #    #enable widgets
    #    self.TP_button.config(state="normal")
    #    self.TopLEDSlider.config(state="normal")


    def TakePhoto_callback(self):
        temp_image = self.camera.takePhoto(self.savePhoto.get())
        cam_util.show_frame(temp_image, self.roi, self.lmain)
        (MFColor, Saturation) = self.imgAnalyzer.colorDetection(temp_image, self.roi)
        #set results into the label objects
        self.ResultLabel.config(text=MFColor, fg="black")
        self.SaturationLabel.config(text="{:.2f}".format(Saturation), fg="black")
    
    def MCSpeedSlider_callback(self, arg1):
        self.motorController.setTargetMotorVelo(int(arg1))
    

    def MCDirRadio_callback(self):
        self.motorController.updateMotorDirection(self.dir_var.get())


    def MCEnergize_callback(self):
        if(self.energize_button_text.get() == "Energize"):
            self.motorController.energizeMotor()
            self.energize_button_text.set("Deenergize")
        elif(self.energize_button_text.get() == "Deenergize"):
            self.motorController.deenergizeMotor()
            self.energize_button_text.set("Energize")


    def comboSelection_callback(self, arg):
        expertSys = self.box.get()
        print("{0} creation".format(expertSys))
        # TODO: creation of proper Expert system

    def TOS_comboSelection_callback(self, arg):
        self.Time_of_scavenge = self.TOS_Dictionary[self.TOSbox.get()]
    
    def LedRing_callback(self):
        if(self.LedRing_button_text.get() == "LED on"):
            self.LedRing_button_text.set("LED off")
            exit_code = call("sudo python3 {0} --turn on".format(self.led_ring_script_path), shell=True)
        elif(self.LedRing_button_text.get() == "LED off"):
            self.LedRing_button_text.set("LED on")
            exit_code = call("sudo python3 {0} --turn off".format(self.led_ring_script_path), shell=True)
    
    def Relay_callback(self):
        if(self.Relay_button_text.get() == "Air on"):
            self.pi.write(self.Relay_Pin, 0)
            self.Relay_button_text.set("Air off")
            self.waitTosThread = relayThread(gpio=self.pi, 
                                             pin=self.Relay_Pin, 
                                             button_text=self.Relay_button_text, 
                                             delay=self.Time_of_scavenge,
                                             stop_event=self.waitTos_stop,
                                             debug=False)
            self.waitTosThread.start()
        elif(self.Relay_button_text.get() == "Air off"):
            self.Relay_button_text.set("Air on")
            self.waitTos_stop.set()
            self.waitTosThread.join(0.6)

    def Lift_callback(self):
        if(self.Lift_button_text.get() == "Lift Up"):
            self.Lift_button.config(state="disabled")
            self.motorController.goToTargetPositionProcedure(self.Lift_Jump_Microsteps)
            self.Lift_button.config(state="normal")
            self.Lift_button_text.set("Lift Down")
            
        elif(self.Lift_button_text.get() == "Lift Down"):
            self.Lift_button.config(state="disabled")
            self.motorController.goToTargetPositionProcedure(0)
            self.Lift_button.config(state="normal")
            self.Lift_button_text.set("Lift Up")

    #def LiftJumpSlider_callback(self, arg1):
    #    self.Lift_Jump_Microsteps = int(arg1)
        

if __name__ == '__main__':
    # Set up GUI
    window = tk.Tk()
    window.wm_title("SG Vision")
    window.config(background="#FFFFFF")
    #window.resizable(0, 0)
    #window.attributes('-fullscreen', True)
    
    w, h = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry("%dx%d+0+0" % (w, h))
    #window.attributes('-zoomed', True)
    # Create Application
    app = App(window)
    window.protocol("WM_DELETE_WINDOW", app.on_closing)
    # Start GUI
    window.mainloop()
