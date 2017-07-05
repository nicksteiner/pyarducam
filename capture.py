import os
import sys
import time
import datetime

import cv2
from PIL import Image
import numpy as np
#import netCDF4 as nc


import ArducamSDK


class CAM(object):

    success = 0

    @property
    def cfg(self):
        return {"u32CameraType": self.CAMERA_,
               "u32Width": self.Width, "u32Height": self.Height,
               "u32UsbVersion": 1,
               "u8PixelBytes": 1,
               "u16Vid": 0x52cb,
               "u8PixelBits": 8,
               "u32SensorShipAddr": self.SensorShipAddr,
               "emI2cMode": self.I2C_MODE_16_16}

    def set_reg_options(self, handle):
        regNum = 0
        while (self.reg_options[regNum][0] != 0xFFFF):
            ArducamSDK.Py_ArduCam_writeSensorReg(handle, self.reg_options[regNum][0], self.reg_options[regNum][1])
            regNum = regNum + 1
"""
    // {0x0202, 0x0000}, // Coarse Integration Time(OPTIONAL) = 0x0
    // DELAY = 1 // Allow PLL to lock
"""


class MT9N001(CAM):
    #COLOR_BYTE2RGB = 49
    COLOR_BYTE2RGB = cv2.COLOR_BAYER_GB2RGB
    CAMERA_ = 0x4D091031
    SensorShipAddr = 32
    I2C_MODE_16_16 = 3
    usbVid = 0x52cb
    Width = 3488
    Height = 2616

    reg_options = [
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

class AR0134(CAM):
    #COLOR_BYTE2RGB = 48
    COLOR_BYTE2RGB = cv2.COLOR_BAYER_BG2RGB
    CAMERA_ = 0x4D091031
    SensorShipAddr = 32
    I2C_MODE_16_16 = 3
    usbVid = 0x52cb # can see this with
    Width = 1280
    Height = 960

    reg_options = [
        # //[PLL_settings]
        [0x3028, 0x0010],  # //ROW_SPEED = 16
        [0x302A, 0x0010],  # //VT_PIX_CLK_DIV = 16
        [0x302C, 0x0001],  # //VT_SYS_CLK_DIV = 1
        [0x302E, 0x0002],  # //PRE_PLL_CLK_DIV = 2
        [0x3030, 0x0028],  # //PLL_MULTIPLIER = 40
        [0x3032, 0x0000],  # //DIGITAL_BINNING = 0
        [0x30B0, 0x0080],  # //DIGITAL_TEST = 128

        # //[Timing_settings]
        [0x301A, 0x00D8],  # //RESET_REGISTER = 216
        [0x301A, 0x10DC],  # //RESET_REGISTER = 4316
        [0x3002, 0x0000],  # //Y_ADDR_START = 0
        [0x3004, 0x0000],  # //X_ADDR_START = 0
        [0x3006, 0x03BF],  # //Y_ADDR_END = 959
        [0x3008, 0x04FF],  # //X_ADDR_END = 1279
        [0x300A, 0x0488],  # //FRAME_LENGTH_LINES = 1160
        [0x300C, 0x056C],  # //LINE_LENGTH_PCK = 1388
        [0x3012, 0x00D8],  # //COARSE_INTEGRATION_TIME = 216
        [0x3014, 0x00C0],  # //FINE_INTEGRATION_TIME = 192
        [0x30A6, 0x0001],  # //Y_ODD_INC = 1
        [0x308C, 0x0000],  # //Y_ADDR_START_CB = 0
        [0x308A, 0x0000],  # //X_ADDR_START_CB = 0
        [0x3090, 0x03BF],  # //Y_ADDR_END_CB = 959
        [0x308E, 0x04FF],  # //X_ADDR_END_CB = 1279
        [0x30AA, 0x0488],  # //FRAME_LENGTH_LINES_CB = 1160
        [0x3016, 0x00D8],  # //COARSE_INTEGRATION_TIME_CB = 216
        [0x3018, 0x00C0],  # //FINE_INTEGRATION_TIME_CB = 192
        [0x30A8, 0x0001],  # //Y_ODD_INC_CB = 1
        [0x3040, 0x4000],  # //READ_MODE = 0
        # //{0x3064, 0x1982},		#//EMBEDDED_DATA_CTRL = 6530
        [0x3064, 0x1802],
        [0x31C6, 0x8008],  # //HISPI_CONTROL_STATUS = 32776
        [0x301E, 0x0000],  # //data_pedestal
        # //{0x3100, 0x0001},		#//auto exposure

        [0x3002, 0],  # // Y_ADDR_START
        [0x3012, 150],

        [0x3056, 0x0024],  # // Gr_GAIN
        [0x3058, 0x0028],  # // BLUE_GAIN
        [0x305a, 0x0028],  # // RED_GAIN
        [0x305c, 0x0024],  # // Gb_GAIN

        [0x3046, 0x0100],  # //en_flash/Flash indicator

        [0x301a, 0x10DC],

        [0xffff, 0xffff],
        [0xffff, 0xffff]]


def open(cam):
    res, handle = ArducamSDK.Py_ArduCam_autoopen(cam.cfg)
    try:
        assert res == cam.success
        cam.open = True
        print('AUTO-OPEN: {},{}'.format(res, handle))
    except Exception as error:
        print('Camera not open. Check permissions.')
        raise
    return handle

def close(cam, handle):
    res = ArducamSDK.Py_ArduCam_close(handle)
    try:
        assert res == cam.success
        cam.open = False
        print('AUTO-CLOSE: {},{}'.format(res, handle))
    except Exception as error:
        print('Camera not closing. Check permissions.')
        raise
    return handle

def read(cam, handle):
    count = 0
    time0 = time.time()
    time1 = time.time()
    data = {}
    if ArducamSDK.Py_ArduCam_availiable(handle) > 0:

        res, data = ArducamSDK.Py_ArduCam_read(handle, cam.Width * cam.Height)
        if res == 0:
            count += 1
            time1 = time.time()
            ArducamSDK.Py_ArduCam_del(handle)
        else:
            print("read data fail!")

    else:
        print("is not availiable")

    if len(data) >= cam.Width * cam.Height:
        if time1 - time0 >= 1:
            print("fps: {} /s\n".format(count))
            count = 0
            time0 = time1
        return data
    else:
        print("data length is not enough!")

def get_file_name():
    return 'cap' + datetime.datetime.now().strftime('%Y%m%dT%H%M%S_%fZ') + '.tif'

def write(cam, data):

    image = Image.frombuffer("L", (cam.Width, cam.Height), data)
    img = np.array(image)
    height, width = img.shape[:2]
    img2 = cv2.cvtColor(img, cam.COLOR_BYTE2RGB)
    #print(img)
    #print(img.shape)
    #print(img2)
    #print(img2.shape)
    file_name = get_file_name()
    cv2.imwrite(file_name, img2)
    """    if saveFlag:
            saveFlag = False
            saveNum += 1
            name = ""
            if "bmp" == args["type"]:
                name = str(saveNum) + ".bmp"
            if "png" == args["type"]:
                name = str(saveNum) + ".png"
            if "jpg" == args["type"]:
                name = str(saveNum) + ".jpg"
        cv2.imwrite(name, img2)
    
        M = np.float32([[1, 0, lx + H_value], [0, 1, ly + V_value]])
        img3 = cv2.warpAffine(img2, M, (width, height))
        img4 = cv2.resize(img3, (width + W_zoom, height + H_zoom), interpolation=cv2.INTER_CUBIC)
        cv2.imshow("AR0134", img4)
        cv2.waitKey(1)
    """

def main():
    cam = AR0134()
    handle = open(cam)
    cam.set_reg_options(handle)
    if ArducamSDK.Py_ArduCam_beginCapture(handle) == cam.success:
        res = ArducamSDK.Py_ArduCam_capture(handle)

    data = read(cam, handle)

    write(cam, data)

    close(cam, handle)

if __name__ == '__main__':
    sys.exit(main())
