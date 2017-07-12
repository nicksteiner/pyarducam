import sys
import capture
import model
import time



def main():
    cam, handle = capture.init_cam(0, model=model.MT9N001)
    #try:
    transfer_lock = capture.mp.Lock()
    # start writer
    queue = capture.mp.Queue()
    writer = capture.Writer(queue, 'raw')


    #start transfer
    transfer = capture.Transfer(cam, handle, transfer_lock, queue)
    transfer.start()
    writer.start()

    transfer.join()
    writer.join()

    #except:pass
    #finally:
    #capture.cam_close(cam, handle)

if __name__ == '__main__':
    sys.exit(main())