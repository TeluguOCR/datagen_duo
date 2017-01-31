#! /usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from itertools import product
import multiprocessing
import cairo
import pango
import pangocairo
import sys
import os
from TeluguFontProperties import FP_DICT

#################################### Arguments
if len(sys.argv) < 2:
    print("""
Writes a given piece of text to an image files.
One image per font style.
The images will be located in <text_file>.images/*.tif
Usage:
{0} <text_file>
 or
{0}  <(echo 'text')""".format(sys.argv[0]))
    sys.exit()

text_file = sys.argv[1]
if text_file.endswith('.txt'):
    imagedir = text_file[:-4]
else:
    imagedir = text_file
imagedir += '.images/'
imagedir = imagedir.replace('/dev/fd', '.')

os.system('mkdir ' + imagedir)
print ("Output directory ", imagedir)

#################################### Init
with open(text_file) as fin:
    print("Opening ", text_file)
    text = fin.read().decode('utf8')

lines = text.split('\n')
n_lines = len(lines)
n_letters = max(len(line) for line in lines)
size_x = 30 * n_letters + 50
size_y = 150 * n_lines + 25
print ("Lines: ", n_lines)
print ("Letters: ", n_letters)
print ("Size X: ", size_x)
print ("Size Y: ", size_y)

#################################### Pango Cairo

surf = cairo.ImageSurface(cairo.FORMAT_RGB24, size_x, size_y)
context = cairo.Context(surf)
pangocairo_context = pangocairo.CairoContext(context)
pangocairo_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

layout = pangocairo_context.create_layout()
layout.set_text(text)

style_ids = {'': 'NR', ' Bold': 'BL', ' Italic': 'IT', ' Bold Italic': 'BI'}
image_file_namer = "{}{{}}_{{}}.png".format(imagedir).replace(" ", "_").format
png_dir = imagedir+'pngs/'
os.system('mkdir ' + png_dir)

#################################### Main Rendering Function
def render((fontname, style)):
    [sz, gho, rep, ppu, spc, abbr, hasbold] = FP_DICT[fontname]

    png_file_name = image_file_namer(abbr,  style_ids[style])
    tif_file_name = png_file_name.replace("png", "tif")

    if os.path.isfile(tif_file_name):
        print("Skipping ", tif_file_name)
        return

    if not hasbold and style[:5] == ' Bold':
        print("No bold for ", abbr)
        return

    fontstyle = fontname + ',' + style + ' ' + str(sz)

    font = pango.FontDescription(fontstyle)
    layout.set_font_description(font)
    layout.set_spacing(spc * 20480)
    context.rectangle(0, 0, size_x, size_y)
    context.set_source_rgb(1, 1, 1)
    context.fill()
    context.translate(50, 25)
    context.set_source_rgb(0, 0, 0)
    pangocairo_context.update_layout(layout)
    pangocairo_context.show_layout(layout)

    print("Rendering ", abbr + style)
    with open(png_file_name, "wb") as image_file:
        surf.write_to_png(image_file)
    context.translate(-50, -25)

    os.system('bin/zealous ' + png_file_name)
    print ("Moving " + png_file_name)
    os.system('mv {} {}'.format(png_file_name, png_dir))

######################################### Main Loop
pool = multiprocessing.Pool(4)
pool.map(render, product(sorted(FP_DICT), style_ids))
