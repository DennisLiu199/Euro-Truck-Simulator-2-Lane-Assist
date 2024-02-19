"""
This is an example of a plugin (type="dynamic"), they will be updated during the stated point in the mainloop.
If you need to make a panel that is only updated when it's open then check the Panel example!
"""


from plugins.plugin import PluginInformation
from src.logger import print

PluginInfo = PluginInformation(
    name="ImageTilt", # This needs to match the folder name under plugins (this would mean plugins\Plugin\main.py)
    # In case the plugin is not the main file (for example plugins\Plugin\Plugin.py) then the name would be "Plugin.Plugin"
    
    description="ExamplePlugin.",
    version="0.1",
    author="Tumppi066",
    url="https://github.com/Tumppi066/Euro-Truck-Simulator-2-Lane-Assist",
    type="dynamic", # = Plugin
    dynamicOrder="before lane detection" # Will run the plugin before anything else in the mainloop (data will be empty)
)

import tkinter as tk
from tkinter import ttk
import src.helpers as helpers
import src.mainUI as mainUI
import src.variables as variables
import src.settings as settings
import src.controls as controls # use controls.RegisterKeybind() and controls.GetKeybindValue()
import os
import cv2
import numpy as np
import time
from scipy import ndimage
import math

pixelMultiplier = -1.8
atResolution = 301  # scaler for the multiplier 
angle = 25
secondsToCapture = 10
def vertical_perspective_warp(image):
    global angle
    height, width = image.shape[:2]
    src_pts = np.float32([[0, 0], [width - 1, 0], [0, height - 1], [width - 1, height - 1]])
    dst_pts = np.float32([[0, 0], [width - 1, 0], [int(width * np.sin(np.radians(angle))), height - 1], [width - 1 - int(width * np.sin(np.radians(angle))), height - 1]])
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_image = cv2.warpPerspective(image, matrix, (width, height))
    warped_image = cv2.blur(warped_image, (7, 7))
    lower_red = np.array([0, 0, 190])
    upper_red = np.array([40, 40, 255])
    lower_green = np.array([0, 200, 0])
    upper_green = np.array([230, 255, 150])
    mask_red = cv2.inRange(warped_image, lower_red, upper_red)
    mask_green = cv2.inRange(warped_image, lower_green, upper_green)
    warped_image = cv2.bitwise_or(mask_red, mask_green)
    return warped_image

def rotateImage(image, angle, center=None):
    # Check if the angle is negative
    if angle < 0:
        angle = 360 + angle
    if center == None:
        center = tuple(np.array([col/2,row/2]))
    else:
        center = tuple(center)
    row,col = image.shape[0:2]
    rot_mat = cv2.getRotationMatrix2D(center,angle,1.0)
    new_image = cv2.warpAffine(image, rot_mat, (col,row))
    return new_image

def getTiltedCenterCoordinate(width, height):
    x = width / 2
    y = height * 0.5245 # The approximate center of the nav arrow in ETS2
    # Create an image, that has a 10x10 "white" pixel at the center
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[int(y) - 20:int(y) + 20, int(x) - 20:int(x) + 20] = [20, 20, 220]
    # Warp the image
    warpedImage = vertical_perspective_warp(image)
    # Find the white pixel
    whitePixel = np.where(warpedImage == 255)
    # If there is no white pixel, return the center of the image
    if len(whitePixel[0]) == 0:
        return (x, y)
    # Else return the average of the white pixels
    return (int(np.mean(whitePixel[1])), int(np.mean(whitePixel[0])))


# The main file runs the "plugin" function each time the plugin is called
# The data variable contains the data from the mainloop, plugins can freely add and modify data as needed
# The data from the last frame is contained under data["last"]
pastImages = [] # Will save the last 5s of images
def plugin(data):
    try:
        frame = data["frame"]
        centerCoord = getTiltedCenterCoordinate(frame.shape[1], frame.shape[0])
        pxPerMeter = pixelMultiplier * (frame.shape[0] / atResolution)
        
        tiltedFrame = vertical_perspective_warp(frame)
        
        timestamp = time.time()
        # Save the image, timestamp and position to the list
        position = (data["api"]["truckPlacement"]["coordinateX"], data["api"]["truckPlacement"]["coordinateZ"])
        rotation = (data["api"]["truckPlacement"]["rotationX"], data["api"]["truckPlacement"]["rotationY"], data["api"]["truckPlacement"]["rotationZ"])
        rotatedFrame = rotateImage(tiltedFrame, rotation[0]*360, center=centerCoord)
        pastImages.append((rotatedFrame, timestamp, position, rotation))
        # Check if the first image is older than the given time
        while pastImages[0][1] < timestamp - secondsToCapture:
            pastImages.pop(0)
            
        # Draw the last 5s of images as the frame. The last image will be the most visible, with the first image having an alpha of 0
        frame = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
        length = len(pastImages)
        imagePerFrame = 10 # int(length)
        counter = 0
        for i, (image, timestamp, position, rotation) in enumerate(pastImages):
            if counter < imagePerFrame and not i == length - 1:
                counter += 1
                continue
            
            counter = 0
            # Set alpha to between 1 and 0 depending on the position in the list
            alpha = (i / length)
            # Apply b&w filter
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            # Move the image up 4/5 of the screen
            image = np.roll(image, int(frame.shape[0] / 5)*4, axis=0)
            # Translate the image based on the change of position
            # The position is in meters, so we need to convert it to pixels
            changeInPosition = (pastImages[-1][2][0] - position[0], pastImages[-1][2][1] - position[1])
            changeInPosition = (int(changeInPosition[0] * pxPerMeter), int(changeInPosition[1] * pxPerMeter))
            image = np.roll(image, changeInPosition[0], axis=1)
            image = np.roll(image, changeInPosition[1], axis=0)
            # Draw the images with the alpha
            # frame = image
            frame = cv2.addWeighted(frame, 1, image, alpha, 0)
        
        data["frame"] = frame
    except: 
        import traceback
        print(traceback.format_exc())
    
    return data # Plugins need to ALWAYS return the data


# Plugins need to all also have the onEnable and onDisable functions
def onEnable():
    pass

def onDisable():
    pass