import os
import sys
import capture
import model
import time


def main():
    cam, handle = capture.init_cam(0, model=model.MT9N001)
    run_path = os.path.join(capture._PATH, 'running.info')
    try:
        transfer_lock = capture.mp.Lock()

        # start writer
        queue = capture.mp.Queue()
        ct = 0
        nWriter = 3
        nTransfer = 1
        writer_list = [capture.Writer(queue, 'tif') for n in range(nWriter)]

        #start transfer
        transfer_list = [capture.Transfer(cam, handle, transfer_lock, queue, ct) for n in range(nTransfer)]

        [transfer.start() for transfer in transfer_list]
        running = []
        for transfer in transfer_list:
            running.append(transfer.pid)
            print('Transfer: {}'.format(transfer.pid))
        [writer.start() for writer in writer_list]
        for writer in writer_list:
            running.append(writer.pid)
            print('Writer: {}'.format(writer.pid))
        with open(run_path, 'w') as f:
            for line in running:
                f.write('{}\n'.format(line))

        [transfer.join() for transfer in transfer_list]
        [writer.join() for writer in writer_list]
    except: pass
    finally:
        [transfer.stop() for transfer in transfer_list]
        capture.cam_close(cam, handle)
        [writer.stop() for writer in writer_list]
        with open(run_path, 'w') as f: pass

        #[queue.put((None, None)) for writer in writer_list]



if __name__ == '__main__':
    sys.exit(main())