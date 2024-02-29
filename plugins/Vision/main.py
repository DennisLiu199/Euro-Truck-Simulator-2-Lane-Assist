from plugins.plugin import PluginInformation
PluginInfo = PluginInformation(
    name="Vision",
    description="In Development",
    version="0.0",
    author="Glas42",
    url="https://github.com/Tumppi066/Euro-Truck-Simulator-2-Lane-Assist",
    type="dynamic",
    dynamicOrder="lane detection"
)

from src.mainUI import switchSelectedPlugin
from src.translator import Translate
from src.mainUI import resizeWindow
import src.variables as variables
import src.settings as settings
import src.controls as controls
import src.helpers as helpers
from src.logger import print
import src.sounds as sounds
from tkinter import ttk
import tkinter as tk

import ctypes
import numpy
import time
import mss
import cv2

sct = mss.mss()

############################################################################################################################    
# Settings
############################################################################################################################
def LoadSettings():
    global screen_width
    global screen_height

    global screencapture_x1
    global screencapture_y1
    global screencapture_x2
    global screencapture_y2

    global frame
    global last_frame

    global reset_window
    global last_execution

    monitor = settings.GetSettings("bettercam", "display", 0)
    monitor = sct.monitors[(monitor + 1)]
    screen_width = monitor["width"]
    screen_height = monitor["height"]
    
    screencapture_x1 = settings.GetSettings("TrafficLightDetection", "x1ofsc", 0)
    screencapture_y1 = settings.GetSettings("TrafficLightDetection", "y1ofsc", 0)
    screencapture_x2 = settings.GetSettings("TrafficLightDetection", "x2ofsc", screen_width-1)
    screencapture_y2 = settings.GetSettings("TrafficLightDetection", "y2ofsc", round(screen_height/1.5)-1)

    frame = cv2.cvtColor(numpy.array(sct.grab(sct.monitors[settings.GetSettings("bettercam", "display", 0)])), cv2.COLOR_BGRA2BGR)
    frame = frame[screencapture_y1:screencapture_y2, screencapture_x1:screencapture_x2]
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    frame = cv2.blur(frame, (25, 25))
    last_frame = frame.copy()

    reset_window = True
    last_execution = 0
    
LoadSettings()


############################################################################################################################
# Code
############################################################################################################################
def plugin(data):
    global screen_width
    global screen_height

    global screencapture_x1
    global screencapture_y1
    global screencapture_x2
    global screencapture_y2

    global frame
    global last_frame

    global reset_window
    global last_execution

    if time.time() > last_execution + 0.05:

        try:
            frameFull = data["frameFull"]
            frame = frameFull[screencapture_y1:screencapture_y2, screencapture_x1:screencapture_x2]
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            frame = cv2.blur(frame, (25, 25))
            frame_width = frame.shape[1]
            frame_height = frame.shape[0]
        except:
            return data


        difference = cv2.absdiff(frame, last_frame)

        threshold = 20
        _, difference_mask = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)

        last_frame = frame.copy()

        frame = cv2.bitwise_and(frame, frame, mask=difference_mask)


        if reset_window == True:
            try:
                cv2.destroyWindow('Vision')
            except:
                pass

        window_handle = ctypes.windll.user32.FindWindowW(None, 'Vision')
        if window_handle == 0 or reset_window == True:
            cv2.namedWindow('Vision', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Vision', round(frame_width*0.5), round(frame_height*0.5))
            cv2.setWindowProperty('Vision', cv2.WND_PROP_TOPMOST, 1)
        cv2.imshow('Vision', frame)

        if reset_window == True:
            reset_window = False

        last_execution = time.time()
    
    return data
        

def onEnable():
    pass

def onDisable():
    pass

class UI():
    try:
        def __init__(self, master) -> None:
            self.master = master
            self.exampleFunction()
            resizeWindow(950,600)        
        
        def destroy(self):
            self.done = True
            self.root.destroy()
            del self
        
        def tabFocused(self):
            resizeWindow(950,600)

        def UpdateSettings(self):
            LoadSettings()
        
        def exampleFunction(self):
            try:
                self.root.destroy()
            except: pass
            
            self.root = tk.Canvas(self.master, width=950, height=600, border=0, highlightthickness=0)
            self.root.grid_propagate(1)
            self.root.pack_propagate(0)
            
            notebook = ttk.Notebook(self.root)
            notebook.pack(anchor="center", fill="both", expand=True)
            
            generalFrame = ttk.Frame(notebook)
            generalFrame.pack()

            notebook.add(generalFrame, text=Translate("General"))
            
            self.root.pack(anchor="center", expand=False)
            self.root.update()
            
            ############################################################################################################################
            # UI
            ############################################################################################################################
            
        def save(self):
            LoadSettings()

        def update(self, data):
            self.root.update()
    
    except Exception as ex:
        print(ex.args)