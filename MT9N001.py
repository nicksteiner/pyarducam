from ctypes import *

import ctypes

import os
import cv2
import time
import Image
import argparse
import numpy as np
import thread as thread

from select import select
from evdev import InputDevice

import ArducamSDK

COLOR_BYTE2RGB = 49
CAMERA_MT9F002 = 0x4D091031
SensorShipAddr = 32
I2C_MODE_16_16  = 3
usbVid = 0x52cb
Width = 3488
Height = 2616
cfg ={"u32CameraType":CAMERA_MT9F002,
      "u32Width":Width,"u32Height":Height,
      "u32UsbVersion":1,
      "u8PixelBytes":1,
      "u16Vid":0x52cb,
      "u8PixelBits":8,
      "u32SensorShipAddr":SensorShipAddr,
      "emI2cMode":I2C_MODE_16_16 }

global saveNum,saveFlag,downFlag,flag,handle,openFlag
openFlag = False
saveNum = 0
handle = {}
downFlag = False
flag = True
saveFlag = False


regArr= [
        [0x0100, 0x0], # Mode    Select = 0x0
        [0x0300, 0x4], # vt_pix_clk_div = 0x4
        [0x0302, 0x01], # vt_sys_clk_div = 0x1
        [0x0304, 0x02], # pre_pll_clk_div = 0x2
        [0x0306, 0x40], # pll_multiplier = 0x40
        [0x0308, 0x08], # op_pix_clk_div = 0x8
        [0x030A, 0x01], # op_sys_clk_div = 0x1
        [0x3064, 0x805], # RESERVED_MFR_3064 = 0x805
        [0x0104, 0x1], # Grouped    Parameter    Hold = 0x1
        [0x3016, 0x111], # Row    Speed = 0x111
        [0x0344, 0x008], # Column    Start = 0x8
        [0x0348, 0xDA7], # Column    End = 0xDA7
        [0x0346, 0x008], # Row    Start = 0x8
        [0x034A, 0xA3F], # Row    End = 0xA3F
        [0x3040, 0x0041], # Read    Mode = 0x41
        [0x0400, 0x0], # Scaling    Mode = 0x0
        [0x0404, 0x10], # Scale_M = 0x10
        [0x034C, 0xDA0], # Output    Width = 0xDA0
        [0x034E, 0xA38], # Output    Height = 0xA38
        [0x0342, 0x202B], # Line    Length = 0x202B
        [0x0340, 0x0AC7], # Frame    Lines = 0xAC7
        [0x3014, 0x056A], # Fine    Integration    Time = 0x56A
        [0x3010, 0x0100], # Fine    Correction = 0x100
        [0x3018, 0x0000], # Extra    Delay = 0x0
        [0x30D4, 0x1080], # Cols    Dbl    Sampling = 0x1080
        [0x0104, 0x0], # Grouped    Parameter    Hold = 0x0
        [0x0100, 0x1], # Mode    Select = 0x1
        [0x0304, 0x0008],
        [0x0306, 0x0040],
        [0x3012, 500],
        [0x301A, 0x5CCC],
        [0xffff, 0xffff],
        [0xffff, 0xffff]
    ]


ap = argparse.ArgumentParser()
ap.add_argument("--type",default = "jpg",required = False, help = "type to the image file")
ap.add_argument("--name",required = False, help = "name to the image file")
args = vars(ap.parse_args())

def readThread(threadName,read_Flag):
	global flag,handle
	data = {}
	#cv2.namedWindow("MT9F002",1)
	while flag:
		if ArducamSDK.Py_ArduCam_availiable(handle) > 0:
			
			res,data = ArducamSDK.Py_ArduCam_read(handle,Width * Height)
			if res == 0:
				ArducamSDK.Py_ArduCam_del(handle)
			else:
				print "read data fail!"
			
		else:
			print "is not availiable"
		if len(data) >= Width * Height:
			show(data)
			flag = False
		else:
			print "data length is not enough!"
		if flag == False:		
			break
	
thread.start_new_thread( readThread,("Thread-2", flag,))

pass

def show(bufferData):
	global downFlag,saveFlag,saveNum
	image = Image.frombuffer("L",(Width,Height),bufferData)
	img = np.array(image)
	height,width = img.shape[:2]
	'''
	img2 = cv2.cvtColor(img,COLOR_BYTE2RGB)
        saveNum += 1
	
	if args["name"] != "":
                name = args["name"]   
        else:
                name = str(saveNum)
	if "bmp" == args["type"]:        
                name += ".bmp"
        if "png" == args["type"]:        
                name += ".png"
        if "jpg" == args["type"]:        
                name += ".jpg"
	cv2.imwrite(name,img2)	
	'''

def video():
	global flag,regArr,handle
	regNum = 0
	res,handle = ArducamSDK.Py_ArduCam_autoopen(cfg)
	capFlag = True
	if res == 0:
		openFlag = True
		print "device open success!"
		while (regArr[regNum][0] != 0xFFFF):
			ArducamSDK.Py_ArduCam_writeSensorReg(handle,regArr[regNum][0],regArr[regNum][1])
			regNum = regNum + 1
		res = ArducamSDK.Py_ArduCam_beginCapture(handle)
		
		if res == 0:
			print "transfer task create success!"
			while flag :
                                if capFlag:
                                        res = ArducamSDK.Py_ArduCam_capture(handle)
                                        if res != 0:
                                                print "capture fail!"
                                                break
                                        else:
                                                capFlag = False
                                time.sleep(0.4)
				if flag == False:		
					break
		else:
			print "transfer task create fail!"
		res = ArducamSDK.Py_ArduCam_close(handle)
		if res == 0:
			openFlag = False
			print "device close success!"
		else:
			print "device close fail!"
	else:
		print "device open fail!"

if __name__ == "__main__":		
	video()



