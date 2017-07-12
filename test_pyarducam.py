import sys
import os
import model
import capture

def test_convert_raw():
    file_name = '/home/nsteiner/pyarducam/img_20170707T135733471897Z_cam0.raw'
    capture.convert_raw(model.AR0134(), file_name, 'tif')

def main():
    test_convert_raw()

if __name__ == '__main__':
    sys.exit(main())