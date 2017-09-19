import os
import sys
import capture
import model
import time
import argparse



def main_threaded():
    cam_handles = capture.get_cam_handles(args)
    try:
        # startup
        capture_list, read_list, write_list, queue = capture.startup(cam_handles, args)
        while True:
            assert not all([write_.exit.is_set() for write_ in write_list])

    except:
        capture.shutdown(capture_list, read_list, write_list)
    finally:
        [capture.cam_shutdown(cam, handle) for cam, handle in cam_handles]

def main(args):

    if args.stop:
        args.nocapture = True
        capture.stop()
        return

    if args.reformat:
        args.nocapture = True
        capture.convert_np(args.model, args.format)

    if ((not args.nocapture) | (args.force)) & (args.threaded):
        main_threaded()
    else:
        tm_ = time.time()
        ct = 0.
        current_path = capture.set_dirs()
        while True:
            tm0 = time.time()
            capture.capture(0, model=args.model, nCapture=1, format_='jpg', current_path=current_path)
            ct += 1
            tmC = time.time()
            print('CRT : {}'.format(1./(tm0-tmC)))
            print('FPS : {}'.format(ct/(tmC-tm_)))

def parse_arguments():
    parser = argparse.ArgumentParser(description="Arducam python wrapper")
    parser.add_argument("-v", "--verbose", action="store_true", default=True)
    parser.add_argument("-n", "--nexposure", type=int, help="number of exposures, 0 for infinite", default=0)
    parser.add_argument("-s", "--filestart", type=str, help="filename starting string", default='img')
    parser.add_argument("-m", "--model", type=str, help="camera model name", default='AR0134')
    parser.add_argument("-x", "--nocapture", action="store_true", help="Inhibit capture mode",  default=False)
    parser.add_argument("-c", "--cameras", type=int, help="number of cameras", default=1)
    parser.add_argument("-w", "--writers", type=int, help="number of writers", default=2)
    parser.add_argument("-T", "--reformat", action="store_true", help="reformat all files in /dat folder",  default=False)
    parser.add_argument("-o", "--format", help="image format",  default='npy')
    parser.add_argument("-p", "--threaded", help="capture using threads",  action='store_true', default=True)
    parser.add_argument("-S", "--stop", help="stop running process",  action='store_true', default=False)
    parser.add_argument("-f", "--force", action="store_true", help="Force capture mode in format or stop",  default=False)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    sys.exit(main(args))