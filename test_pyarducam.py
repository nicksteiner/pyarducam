import sys
import os
import model
import capture

def test_convert_raw():
    file_name = '/home/nsteiner/pyarducam/dat/img_20170713T141213578384Z_cam0.raw'
    capture.convert_raw(model.AR0134(), file_name, 'tif')

def main():
    test_convert_raw()

if __name__ == '__main__':
    sys.exit(main())