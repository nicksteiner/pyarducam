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


from model import AR0134, MT9N001

import ArducamSDK

_PATH = os.path.dirname(os.path.realpath(__file__))

def convert_raw(cam, file_name, format_):
    with open(file_name, 'rb') as f:
        data = f.read()[::-1]
    image = Image.frombuffer("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1)
    img = np.array(image)
    img2 = cv2.cvtColor(img, cam.COLOR_BYTE2RGB)
    file_name = file_name.replace('raw', format_)
    cv2.imwrite(file_name, img2)

def cam_open(cam):
    res, handle = ArducamSDK.Py_ArduCam_open(cam.cfg, cam.nCam)
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
    ArducamSDK.Py_ArduCam_del(handle)
    res = ArducamSDK.Py_ArduCam_endCapture(handle)
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
    # check data ready
    """

    :param cam: <Cam> Class object
    :param handle: handle to camera
    :return:
    """
    try:
        assert ArducamSDK.Py_ArduCam_availiable(handle) > 0
        res, data = ArducamSDK.Py_ArduCam_read(handle, cam.Width * cam.Height)
    except Exception as error:
        raise
    # check data good
    try:
        assert len(data) >= cam.Width * cam.Height
        #ArducamSDK.Py_ArduCam_del(handle)
    except Exception as error:
        raise
    return Image.frombuffer("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1).tostring()

def get_file_name(format_='tif', nCam=0):
    """

    :param format_: format file extension
    :param nCam: cam position
    :return: path to image-file
    """
    time_ = datetime.datetime.now().strftime('%Y%m%dT%H%M%S%fZ')
    fname = 'img_{}_cam{}.{}'.format( time_,nCam, format_)
    return os.path.join(_PATH, 'dat', fname)

def cam_write(cam, data, format_='raw', nCam=0):
    image = Image.fromstring("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1)
    file_name = get_file_name(format_, nCam)
    if format_ == 'raw':
        with open(file_name, 'wb') as f:
            f.write(image)
    else:
        img = np.array(image)
        img2 = cv2.cvtColor(img, cam.COLOR_BYTE2RGB)
        cv2.imwrite(file_name, img2)

def init_cam(nCam, model=AR0134):
    cam = model(nCam)
    handle = cam_open(cam)
    cam.set_reg_options(handle)
    begin_error = ArducamSDK.Py_ArduCam_beginCapture(handle)
    assert begin_error == cam.success
    time.sleep(.03)
    return cam, handle

# Threading

class Writer(mp.Process):

    def __init__(self, queue, format):
        self.exit = mp.Event()
        self.queue = queue
        self.format = format
        super(Writer, self).__init__()

    def run(self):
        #while True:
        while not self.exit.is_set():
            cam, data = self.queue.get()
            if cam is None:
                print('Stopping Writer: {}'.format(self.pid))
                break
            cam_write(cam, data, self.format)

    def stop(self):
        print('Stopping Writer: {}'.format(self.pid))
        self.exit.set()


class Transfer(mp.Process):

    def __init__(self, cam, handle, transfer_lock, write_queue, ct):
        self.exit = mp.Event()
        self.transfer_lock = transfer_lock
        self.cam = cam
        self.write_queue = write_queue
        self.handle = handle
        self.ct = ct
        self.time = time.time()
        super(Transfer, self).__init__()

    def run(self):
        while not self.exit.is_set():

            assert ArducamSDK.Py_ArduCam_capture(self.handle) == self.cam.success
            with self.transfer_lock:
                data = cam_read(self.cam, self.handle)
                self.ct += 1
                print('Transfer Done')
                tm_ = time.time() - self.time
                print(tm_)
            print('CAM{}; Frame: {}; Elapsed: {}, FPS: {:g}'.format(self.cam.nCam, self.ct, tm_, self.ct / tm_))
            self.write_queue.put((self.cam, data))

    def stop(self):
        print('Stopping Transfer: {}'.format(self.pid))
        self.exit.set()


def trigger_cam(cam, handle):
    try:
        assert cam_begin(cam, handle) == cam.success
    except:
        print('Cam Failed to Begin!!')
        raise
    avail_ = ArducamSDK.Py_ArduCam_availiable(handle)
    print(avail_)
    if  avail_ > 0:
        data = cam_read(cam, handle)
    return data

def init_proc(l):
    global lock
    lock = l

def capture(nCam, model=MT9N001, nCapture=1, format_='raw', lock=None):
    cam, handle = init_cam(nCam, model)
    for n in range(nCapture):
        if lock:
            lock.acquire()
        data = trigger_cam(cam, handle)
        #print(time.time() - time_),
        print('_CAM{}'.format(nCam))
        if lock:
            lock.release()
        cam_write(cam, data, format_, nCam)
    cam_close(cam, handle)

def main():
    capture(0)

if __name__ == '__main__':
    sys.exit(main())
