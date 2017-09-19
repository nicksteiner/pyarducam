import os
import sys
import time
import glob
import datetime
import multiprocessing as mp
from threading import Thread
from multiprocessing import Queue, Value

import psutil
from PIL import Image
from cv2 import cvtColor, imwrite
import numpy as np

from model import AR0134, MT9N001, get_model

import ArducamSDK

_PATH = os.path.dirname(os.path.realpath(__file__))
RUN_PATH = os.path.join(_PATH, 'running.info')

# File utils.
# ~~~~~~~~~~~

def set_dirs():
    parse_ = lambda x: os.path.basename(x).replace('flt_', '')
    current_int = max(
        [int(parse_(fld)) for fld, _, _ in os.walk(os.path.join(_PATH, 'dat', '.')) if parse_(fld) != '.'] + [0]) + 1
    # current_int = max([os.path.basename(fld)for fld, _, _ in os.walk(os.path.join(_PATH, 'dat', '.'))] + [0]) + 1
    current_path = os.path.join(_PATH, 'dat', 'flt_{:05d}'.format(current_int))
    print(current_path)
    try:
        os.makedirs(current_path)
    except:
        pass
    return current_path

def get_file_name(current_path, format_='tif', nCam=0):
    """

    :param format_: format file extension
    :param nCam: cam position
    :return: path to image-file
    """
    time_ = datetime.datetime.now().strftime('%Y%m%dT%H%M%S%fZ')
    fname = 'img_{}_cam{}.{}'.format( time_,nCam, format_)
    return os.path.join(current_path, fname)

def convert_raw(cam, file_name, format_):
    with open(file_name, 'rb') as f:
        data = f.read()[::-1]
    image = Image.frombuffer("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1)
    img = np.array(image)
    img2 = cvtColor(img, cam.COLOR_BYTE2RGB)
    file_name = file_name.replace('raw', format_)
    imwrite(file_name, img2)

def convert_np(model, img_format):
    cam = get_model(model)
    for np_file_ in glob.glob(os.path.join(_PATH, 'dat', '*.npy')):
        print('Converting ... {}'.format(np_file_))
        array = np.load(np_file_)
        img2 = cvtColor(array, cam.COLOR_BYTE2RGB)
        imwrite(np_file_.replace('npy', img_format), img2)

def cam_write(cam, data, current_path, format_='npy', nCam=0, ):
    image = Image.fromstring("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1)
    file_name = get_file_name(current_path, format_, nCam)
    if format_ == 'raw':
        with open(file_name, 'wb') as f:
            f.write(image.tostring())
    else:
        img = np.array(image)
        if format_ == 'npy':
            np.save(file_name, image)
        else:
            img2 = cvtColor(img, cam.COLOR_BYTE2RGB)
            imwrite(file_name, img2)

# Arducam camera functions
# ------------------------
def cam_init(nCam, model_str='AR0134'):
    model_obj = get_model(model_str)
    cam = model_obj(nCam)
    handle = cam_open(cam)
    cam.set_reg_options(handle)
    cam_init_capture(cam, handle)
    return cam, handle

def cam_open(cam):
    res, handle = ArducamSDK.Py_ArduCam_open(cam.cfg, cam.nCam)
    print('AUTO-OPEN (cam{}): {}'.format(cam.nCam, res))
    try:
        assert res == cam.success
        cam.open = True
    except:
        print('Camera not open. Check permissions.')
        raise
    return handle

def cam_init_capture(cam, handle):
    res = ArducamSDK.Py_ArduCam_beginCapture(handle)
    print('CAPTURE-TASK (cam{}): {}'.format(cam.nCam, res))
    try:
        assert  res == cam.success
    except:
        raise Exception("Cannot start capture task list")
    return res

def cam_capture(handle, ncam=0):
    res = ArducamSDK.Py_ArduCam_capture(handle)
    print('CAM-CAPTURE (cam{}): {}'.format(ncam, res))
    try:
        assert res == 0
    except:
        raise Exception('CAM-CAPTURE (cam{}); capture fail !!!'.format(ncam))
    time.sleep(0.03)

def cam_read(cam, handle):
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
        ArducamSDK.Py_ArduCam_del(handle)
    except Exception as error:
        raise
    return Image.frombuffer("L", (cam.Width, cam.Height), data, 'raw', "L", 0, 1).tostring()

def cam_shutdown(cam, handle):
    # end capture task list
    res = ArducamSDK.Py_ArduCam_endCapture(handle)
    print('END-CAPTURE  (cam{}): {}'.format(cam.nCam, res))
    try:
        assert res == cam.success
    except:
        print("problem stopping capture task list :(")
    # close camera
    res = ArducamSDK.Py_ArduCam_close(handle)
    print('AUTO-CLOSE  (cam{}): {}'.format(cam.nCam, res))
    try:
        assert res == cam.success
        cam.open = False
    except Exception as error:
        print('Camera not closing. Check permissions.')
        raise
    return handle

# Threading
#  --------
class Write(mp.Process):

    def __init__(self, queue, format, current_path, ct, max):
        self.current_path = current_path
        self.exit = mp.Event()
        self.queue = queue
        self.format = format
        self.time = time.time()
        self.ct = ct
        self.max = max
        super(Write, self).__init__()

    def run(self):
        print('Writer Running: {}'.format(self.pid))
        while not self.exit.is_set():
            if not self.queue.empty():
                time0 = time.time()
                cam, data = self.queue.get()
                cam_write(cam, data, self.current_path, format_=self.format)
                time1 = time.time()
                delT = time1 - time0
                delTT = time1 - self.time
                self.ct.value += 1
                print('CAM{} Frame: {}; Elapsed: {}, FPS: {:g}, CNT: {}'.format(cam.nCam, self.ct.value, delT, self.ct.value / delTT, self.ct.value))
                if (self.ct.value >= self.max) & (self.max != 0):
                    print('Stopping Reader')
                    self.exit.set()

    def stop(self):
        print('Stopping Writer: {}'.format(self.pid))
        self.exit.set()

class Capture(Thread):

    def __init__(self, cam, handle):
        self.exit = mp.Event()
        self.cam = cam
        self.handle = handle
        self.ct = 0
        super(Capture, self).__init__()

    def run(self):
        print('CAM{} capture; running ... '.format(self.cam.nCam))
        while not self.exit.is_set():
            time0 = time.time()
            res = ArducamSDK.Py_ArduCam_capture(self.handle)
            #print('CPS: {}'.format(1 / (time.time() - time0)))
            assert res == self.cam.success

    def stop(self):
        print('Stopping Capture')
        self.exit.set()

class Read(Thread):

    def __init__(self, cam, handle, transfer_lock, write_queue):
        self.exit = mp.Event()
        self.transfer_lock = transfer_lock
        self.cam = cam
        self.write_queue = write_queue
        self.handle = handle
        super(Read, self).__init__()

    def run(self):
        print('CAM{} read; running'.format(self.cam.nCam))
        while not self.exit.is_set():
            if ArducamSDK.Py_ArduCam_availiable(self.handle) > 0:
                res, data = ArducamSDK.Py_ArduCam_read(self.handle, self.cam.Width * self.cam.Height)
                image = Image.frombuffer("L", (self.cam.Width, self.cam.Height), data, 'raw', "L", 0, 1)
                self.write_queue.put((self.cam, image.tostring()))

    def stop(self):
        print('Stopping Read')
        self.exit.set()

def capture(nCam, model=AR0134, nCapture=1, format_='raw', lock=None, current_path=None):
    if current_path is None:
        current_path = set_dirs()
    cam, handle = cam_init(nCam, model)
    try:
        for n in range(nCapture):
            res = ArducamSDK.Py_ArduCam_capture(handle)
            print('CAPTURE-TEST (cam{}): {}'.format(0, res))
            if res == 32:
                break
            res = ArducamSDK.Py_ArduCam_availiable(handle)
            print('DATA-AVAILABLE-TEST (cam{}): {}'.format(0, res))

            res, data = ArducamSDK.Py_ArduCam_read(handle, cam.Width*cam.Height)
            print('DATA-READ-TEST (cam{}): {}'.format(0, res))

            len_data = len(data)
            print('FRAME-LENGTH-TEST (cam{}): {}'.format(0, len_data))
            if len_data >= cam.Width * cam.Height:
                print('Less than full frame')

            res = ArducamSDK.Py_ArduCam_del(handle)
            print('FRAME-DELETE-TEST (cam{}): {}'.format(0, res))

            cam_write(cam, data, current_path, format_, nCam)
    finally:
        cam_shutdown(cam, handle)


def get_cam_handles(args):
    return [cam_init(n, model_str=args.model) for n in range(args.cameras)]

def startup(cam_handles, args):
    transfer_lock = mp.Lock()
    current_path = set_dirs()

    ct = Value('i', 0)


    # set writer and queue
    queue = Queue()
    write_list = [Write(queue, args.format, current_path, ct, args.nexposure) for n in range(args.writers)]

    # init capture
    capture_list = [Capture(cam, handle) for cam, handle in cam_handles]

    #init transfer
    read_list = [Read(cam, handle, transfer_lock, queue) for cam, handle in
                     cam_handles]
    [capture_.start() for capture_ in capture_list]
    [read_.start() for read_ in read_list]
    [write_.start() for write_ in write_list]

    """    running = []
    # start cam capture
    
    for capture_ in capture_list:
        running.append(capture_.pid)
        print('Capture: {}'.format(capture_.pid))

    # start data transfer
    [transfer.start() for transfer in read_list]
    running = []
    for transfer in read_list:
        running.append(transfer.pid)
        print('Transfer: {}'.format(transfer.pid))

    # start writers
    [writer.start() for writer in writer_list]
    for writer in writer_list:
        running.append(writer.pid)
        print('Writer: {}'.format(writer.pid))

    # set current writers
    with open(RUN_PATH, 'w') as f:
        for line in running:
            f.write('{}\n'.format(line))
    """
    return capture_list, read_list, write_list, queue

def shutdown(capture_list, read_list, write_list):
    if read_list:
        [read_.stop() for read_ in read_list]

    if capture_list:
        [capture_.stop() for capture_ in capture_list]

    if write_list:
        [write_.stop() for write_ in write_list]

    [read_.join() for read_ in read_list]
    [capture_.join()  for capture_  in capture_list]

    [write_.join() for write_ in write_list]

    #with open(RUN_PATH, 'w') as f: pass

def stop():
    proc_ids = []
    with open(os.path.join(_PATH, 'running.info'), 'r') as f:
        for line in f.readlines():
            proc_ids.append(int(line.rstrip()))

    for proc in psutil.process_iter():
        for running_id in proc_ids:
            if proc.pid == running_id:
                print(proc.name())
                proc.kill()