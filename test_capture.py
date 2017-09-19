import time
import multiprocess as mp
from threading import Thread
from multiprocess import Queue
import numpy as np
from cv2 import cvtColor, imwrite

from PIL import Image
import ArducamSDK

global end_capture

cfg = {
    "u32CameraType": 0x4D091031,
    "u32Width": 1280,
    "u32Height": 960,
    "u32UsbVersion": 1,
    "u8PixelBytes": 1,
    "u16Vid": 0x52cb,
    "u8PixelBits": 8,
    "u32SensorShipAddr": 32,
    "emI2cMode": 3,
    "COLOR_BYTE2RGB": 47
}


class Read(Thread):

    def __init__(self, handle, write_queue):
        self.exit = mp.Event()
        self.ct = 0
        self.handle = handle
        #self.handle = handle
        self.write_queue = write_queue
        #self.daemon = True
        super(Read, self).__init__()
        print('**********READINIT**************')

    def run(self):
        print('Read Running: ')
        while not self.exit.is_set():
            #print('Read Running: {}'.format(self.pid))
            #    #res = ArducamSDK.Py_ArduCam_availiable(self.handle)
            #print('DATA-AVAILABLE-TEST : {}'.format(0, res))
            #print(ArducamSDK.Py_ArduCam_availiable(self.handle))
            #if not self.handle_queue.empty():
            #time.sleep(0.005)
            #    print('**********AVAIL**************: {}'.format(ArducamSDK.Py_ArduCam_availiable(self.handle)))
            #    handle = self.handle_queue.get()
            #print('Thread buffer length: {}'.format(ArducamSDK.Py_ArduCam_availiable(self.handle)))

            if ArducamSDK.Py_ArduCam_availiable(self.handle) > 0:
                time0 = time.time()

                #if self.ct%1000000 == 0:
                self.ct += 1
                res, data = ArducamSDK.Py_ArduCam_read(self.handle, cfg["u32Width"] * cfg["u32Height"])
                #print('DATA-READ-TEST (cam): {}'.format( res))
                len_data = len(data)
                #print('FRAME-LENGTH-TEST (cam): {}'.format(len_data))
                #if len_data >= cfg["u32Width"] * cfg["u32Height"]:
                #print('Less than full frame')
                image = Image.frombuffer("L", (cfg["u32Width"], cfg["u32Height"]), data, 'raw', "L", 0, 1)
                self.write_queue.put(image.tostring())
                res = ArducamSDK.Py_ArduCam_del(self.handle)
                #print('***PUT DATA ********')

                #print('FRAME-DELETE-TEST (cam{}): {}'.format(0, res))
                print('Read queue size: {}'.format(self.write_queue.qsize()))
                print('RPS: {}'.format(1 / (time.time() - time0)))

                #print('**********READCT**************: {}'.format(self.ct))

    def stop(self):
        print('Stopping Read')
        self.exit.set()

class Write(mp.Process):

    def __init__(self, queue):
        self.exit = mp.Event()
        self.queue = queue
        self.ct = 0
        #self.daemon = True
        super(Write, self).__init__()
        print('**********WRITERINIT**************')

    def run(self):
        #print('Writer running ... ')
        while not self.exit.is_set():
            #print('Write queue size: {}'.format(self.queue.qsize()))
            time.sleep(.001)
            if not self.queue.empty():
                if self.ct == 0:
                    time0 = time.time()
                #time0 = time.time()
                image_str = self.queue.get()
                image = Image.fromstring("L", (cfg["u32Width"], cfg["u32Height"]), image_str, 'raw', "L", 0, 1)
                image_bayer = np.array(image)
                image_rgb = cvtColor(image_bayer, cfg["COLOR_BYTE2RGB"])
                imwrite('/home/nsteiner/test_dat/test{}.jpg'.format(self.ct), image_rgb)
                self.ct += 1
                #print('**********WRITECT**************: {}'.format(self.ct))
                print('WPS: {}'.format(self.ct / (time.time() - time0)))

    def stop(self):
        print('Stopping Capture')
        self.exit.set()

class Capture(Thread):
    def __init__(self, handle, end_capture):
        self.exit = mp.Event()
        self.ct = 0
        self.handle = handle
        super(Capture, self).__init__()
        print('**********CAPTUREINIT**************')

    def run(self):
        print('Capture Running: ')
        while not self.exit.is_set():
            time0 = time.time()
            res = ArducamSDK.Py_ArduCam_capture(self.handle)
            print('CAPTURE (cam): {}'.format(res))
            print('CPS: {}'.format(1 / (time.time() - time0)))
            self.ct += 1
            if end_capture:
                break

    def stop(self):
        print('Capture Stopping')
        self.exit.set()

def main_working():
    ct = 0
    n_cam = 0
    res, handle = ArducamSDK.Py_ArduCam_open(cfg, n_cam)
    print('AUTO-OPEN-TEST (cam{}): {}'.format(n_cam, res))
    try:
        res = ArducamSDK.Py_ArduCam_beginCapture(handle)
        print('CAPTURE-TASK-TEST (cam{}): {}'.format(n_cam, res))
        # capture thread
        while True:
            res = ArducamSDK.Py_ArduCam_capture(handle)
            print('CAPTURE-TEST (cam{}): {}'.format(n_cam, res))
            if res == 32:
                break
            res = ArducamSDK.Py_ArduCam_availiable(handle)
            print('DATA-AVAILABLE-TEST (cam{}): {}'.format(n_cam, res))

            res, data = ArducamSDK.Py_ArduCam_read(handle, cfg["u32Width"] * cfg["u32Height"])
            print('DATA-READ-TEST (cam{}): {}'.format(n_cam, res))

            len_data = len(data)
            print('FRAME-LENGTH-TEST (cam{}): {}'.format(n_cam, len_data))
            if len_data >= cfg["u32Width"] * cfg["u32Height"]:
                print('Less than full frame')

            res = ArducamSDK.Py_ArduCam_del(handle)
            print('FRAME-DELETE-TEST (cam{}): {}'.format(n_cam, res))

    finally:
        res = ArducamSDK.Py_ArduCam_endCapture(handle)
        print('END-CAPTURE-TEST  (cam{}): {}'.format(n_cam, res))

        res = ArducamSDK.Py_ArduCam_close(handle)
        print('AUTO-CLOSE-TEST  (cam{}): {}'.format(n_cam, res))


def main():
    ct = 0
    n_cam = 0
    res, handle = ArducamSDK.Py_ArduCam_open(cfg, n_cam)
    print('AUTO-OPEN-TEST (cam{}): {}'.format(n_cam, res))
    try:
        res = ArducamSDK.Py_ArduCam_beginCapture(handle)
        print('CAPTURE-TASK-TEST (cam{}): {}'.format(n_cam, res))
        # capture thread
        time0 = time.time()
        global end_capture
        end_capture = False

        capture = Capture(handle, end_capture)
        #capture.start()
        #capture1 = Capture(handle, end_capture)
        #capture2 = Capture(handle, end_capture)

        capture.start()
        #capture1.start()
        #capture2.start()

        #time.sleep(1)

        #if capture.ct == 5:  # setup
        write_queue = Queue()

        read = Read(handle, write_queue)
        read.start()
        #read1 = Read(handle, write_queue)
        #read1.start()

        write = Write(write_queue)
        write.start()
        write1 = Write(write_queue)
        write1.start()
        #write2 = Write(write_queue)
        #write2.start()

        while read.ct < 50:
            pass # print(read.ct)
        raise



    except:

        capture.stop()
        #capture1.stop()
        #capture2.stop()

        read.stop()
        #read1.stop()

        write.stop()
        write1.stop()
        #write2.stop()

        capture.join()
        #capture1.join()
        #capture2.join()

        read.join()
        #read1.join()
        write.join()
        write1.join()
        #write2.join()

    finally:
        res = ArducamSDK.Py_ArduCam_endCapture(handle)
        print('END-CAPTURE-TEST  (cam{}): {}'.format(n_cam, res))

        res = ArducamSDK.Py_ArduCam_close(handle)
        print('AUTO-CLOSE-TEST  (cam{}): {}'.format(n_cam, res))

if __name__ == '__main__':
    main()


"""
do not mess

def main_working():
    ct = 0
    n_cam = 0
    res, handle = ArducamSDK.Py_ArduCam_open(cfg, n_cam)
    print('AUTO-OPEN-TEST (cam{}): {}'.format(n_cam, res))
    try:
        res = ArducamSDK.Py_ArduCam_beginCapture(handle)
        print('CAPTURE-TASK-TEST (cam{}): {}'.format(n_cam, res))
        # capture thread
        while True:
            res = ArducamSDK.Py_ArduCam_capture(handle)
            print('CAPTURE-TEST (cam{}): {}'.format(n_cam, res))
            if res == 32:
                break
            res = ArducamSDK.Py_ArduCam_availiable(handle)
            print('DATA-AVAILABLE-TEST (cam{}): {}'.format(n_cam, res))

            res, data = ArducamSDK.Py_ArduCam_read(handle, cfg["u32Width"] * cfg["u32Height"])
            print('DATA-READ-TEST (cam{}): {}'.format(n_cam, res))

            len_data = len(data)
            print('FRAME-LENGTH-TEST (cam{}): {}'.format(n_cam, len_data))
            if len_data >= cfg["u32Width"] * cfg["u32Height"]:
                print('Less than full frame')

            res = ArducamSDK.Py_ArduCam_del(handle)
            print('FRAME-DELETE-TEST (cam{}): {}'.format(n_cam, res))

    finally:
        res = ArducamSDK.Py_ArduCam_endCapture(handle)
        print('END-CAPTURE-TEST  (cam{}): {}'.format(n_cam, res))

        res = ArducamSDK.Py_ArduCam_close(handle)
        print('AUTO-CLOSE-TEST  (cam{}): {}'.format(n_cam, res))

"""
