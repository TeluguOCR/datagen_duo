import random
import sys
import os
import logging

import banti.ocr as ocr

########################################## Arguments
from parser import Parser

try:
    prefix = sys.argv[1]
except IndexError:
    print('Usage: ' + sys.argv[0] + ''' <prefix for the images and text file> [loglevel=info]
        <prefix>.images are read one by one and box files are scanned using the text file
        <prefix>.txt
        loglevel is one of c(ritical), e(rror), w(arning), i(nfo), d(ebug)''')
    sys.exit()

if prefix[-1] != '.':
    prefix += '.'

img_dir = prefix + 'images/'
txt_file = prefix + 'txt'

try:
    log_level = sys.argv[2]
except IndexError:
    log_level = "info"
log_level = {
    'c': logging.CRITICAL,
    'e': logging.ERROR,
    'w': logging.WARNING,
    'i': logging.INFO,
    'd': logging.DEBUG}.get(log_level.lower()[0], logging.INFO)

######################################### Init OCR

oseer = ocr.OCR('banti/library/nn.pkl',
        'banti/library/rel48.scl',
        'banti/library/alphacodes.lbl',
        'banti/library/mega.123.pkl',
        loglevel=log_level)

######################################### Final Loop
if 1:
    import multiprocessing
    import traceback

    def process_file(fname):
        parser = Parser(oseer, txt_file, prefix)
        print("Processing", fname)
        try:
            parser.process_file(img_dir + fname)
        except KeyboardInterrupt:
            raise
        except:
            print("Failed ", fname)
            return fname, traceback.format_exc()
        print("Done ", fname)
        return fname, "Success"

    file_list = [f for f in os.listdir(img_dir) if f.endswith('.box')]
    file_list = tuple(sorted(file_list))
    pool = multiprocessing.Pool(8)
    returns = pool.map(process_file, file_list, chunksize=1)
    for f, e in returns:
        print(f)
        print(e)

else:
    parser = Parser(oseer, txt_file, prefix)
    file_list = [f for f in sorted(os.listdir(img_dir)) if f.endswith('.box')]

    for box_file_name in file_list:
        if random.random() < 1 and box_file_name.startswith('G'):
            try:
                print(box_file_name)
                parser.process_file(img_dir + box_file_name)
            except KeyboardInterrupt:
                inpt = input("Continue to next file? y/[n]?")
                if inpt != 'y':
                    break

    print(parser)