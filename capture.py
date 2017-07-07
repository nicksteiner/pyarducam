import os
import sys
import time
import glob
import datetime

import cv2
from PIL import Image
import numpy as np
#import netCDF4 as nc
import multiprocessing as mp


from model import AR0134

import ArducamSDK

def convert_raw(cam, file_name, format_):
    with open(file_name, 'rb') as f:
        data = f.read()
        image = Image.frombuffer("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1)
        img = np.array(image)
        img2 = cv2.cvtColor(img, cam.COLOR_BYTE2RGB)
        file_name = get_file_name(format_)
        cv2.imwrite(file_name, img2)

def cam_open(cam, nCam=0):
    res, handle = ArducamSDK.Py_ArduCam_open(cam.cfg, nCam)
    try:
        assert res == cam.success
        cam.open = True
        print('AUTO-OPEN: {},{}'.format(res, handle))
    except Exception as error:
        print('Camera not open. Check permissions.')
        raise
    return handle

def cam_begin(cam, handle):
    if ArducamSDK.Py_ArduCam_beginCapture(handle) == cam.success:
        res = ArducamSDK.Py_ArduCam_capture(handle)
    return res

def cam_close(cam, handle):
    res = ArducamSDK.Py_ArduCam_close(handle)
    try:
        assert res == cam.success
        cam.open = False
        print('AUTO-CLOSE: {},{}'.format(res, handle))
    except Exception as error:
        print('Camera not closing. Check permissions.')
        raise
    return handle

def cam_read(cam, handle):
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

def get_file_name(format_='tif', nCam=0):
    time_ = datetime.datetime.now().strftime('%Y%m%dT%H%M%S%fZ')
    return 'img_{}_cam{}.{}'.format( time_,nCam, format_)

def cam_write(cam, data, format_='raw', nCam=0):
    file_name = get_file_name(format_, nCam)
    if format_ == 'raw':
        with open(file_name, 'wb') as f:
            f.write(data)
    else:
        image = Image.frombuffer("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1)
        img = np.array(image)
        img2 = cv2.cvtColor(img, cam.COLOR_BYTE2RGB)
        cv2.imwrite(file_name, img2)

def init_cam(nCam, model=AR0134):
    cam = model()
    handle = cam_open(cam, nCam)
    cam.set_reg_options(handle)
    return cam, handle

def trigger_cam(cam, handle):
    try:
        assert cam_begin(cam, handle) == cam.success
    except:
        print('Cam Failed to Begin!!')
        raise
    if ArducamSDK.Py_ArduCam_availiable(handle) > 0:
        data = cam_read(cam, handle)
    return data

def capture(nCam, model=AR0134, nCapture=20, format_='raw'):
    cam, handle = init_cam(nCam, model)
    for n in range(nCapture):
        lock.acquire()
        data = trigger_cam(cam, handle)
        print(time.time() - time_),
        print('_ CAM{}'.format(nCam))
        lock.release()
        cam_write(cam, data, format_, nCam)
    cam_close(cam, handle)

def init_proc(l):
    global lock
    lock = l

def main():
    lock_ = mp.Lock()
    global time_
    time_ = time.time()
    pool = mp.Pool(2, initializer=init_proc, initargs=(lock_, ))
    pool.map(capture, [0, 1])

if __name__ == '__main__':
    sys.exit(main())
