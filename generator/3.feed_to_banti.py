#! /usr/bin/env python3
import os
import sys

########################## Process Arguments
try:
    img_dir = sys.argv[1]
except IndexError:
    print('Usage: ' + sys.argv[0] + ' <Directory>/ [banti_exe]\n'
          'Directory is location of the images to be fed to banti')
    sys.exit()

try:
    banti_exe = sys.argv[2] + ' '
except IndexError:
    banti_exe = 'bin/segmenter'

if img_dir[-1] != '/':
    img_dir += '/'
flags = '2 9 >'

########################### Process all the tif files with banti segmenter
file_list = sorted(os.listdir(img_dir))

for img_name in file_list:
    if img_name[-4:] != '.tif':
        continue

    full_name = img_dir + img_name
    if os.path.isfile(full_name[:-3] + 'out'):
        print("Skipping processed file:", img_name)
        continue

    print("Feeding ", img_name)
    command = "{} {} {} {}".format(banti_exe, full_name, flags, full_name.replace('.tif', '.out'))
    os.system(command)