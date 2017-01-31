#! /usr/bin/env python3
import sys
import re
from random import shuffle, seed


################### Arguments

try:
    input_file = sys.argv[1]
except IndexError:
    print(
'''Usage:{0} <glyph_count.ast> [replicas=2] [aksharas_per_line=20] [seed=84]
    Generates a nice training set with the log of glyph_count data
    given in the pickle file. aksharas_per_line is the aksharas per line.
    seed is random seed for shuffling'''.format(sys.argv[0]))
    sys.exit()

try:
    replicas = int(sys.argv[2])
except IndexError:
    replicas = 2

try:
    aksharas_per_line = int(sys.argv[3])
except IndexError:
    aksharas_per_line = 20

try:
    seed_at = int(sys.argv[4])
except IndexError:
    seed_at = 84

with open(input_file, 'r') as fp:
    glyphs = fp.read().splitlines()
print(glyphs, len(glyphs))

#################### Initializations

bad_hallulu_str = 'కఖఘఙఛఝఞటఠఢథధపఫభమయషసహ'
bad_gunintams_str = 'ాుూొోౌ'  # All except ిీెే
independents_str = """^[అ-ఔౠౡఽౘౙ౾!(),\-.0-9=?'"౦-౯।॥‌/+{}%&:;<>]$"""

hallulu = []
bad_hallulu = []
vattulu = []
achallulu = []
bad_achallulu = []  # The bad ones again
ubhayalu = []
indeps = []

################# Read various letters

for akshara in glyphs:
    aksharas = [akshara] * replicas

    if akshara.startswith('#'):
        continue

    elif re.match(independents_str, akshara):
        indeps += aksharas

    elif akshara.startswith('క్ష'):
        indeps += aksharas

    elif re.match(r'^[క-హ]$', akshara):
        if akshara[0] in bad_hallulu_str:
            bad_hallulu += aksharas
        else:
            hallulu += aksharas

    elif re.match(r'^్[క-హ]$', akshara):
        vattulu += aksharas

    elif re.match(r'^[ఁంఃృౄ]$', akshara):
        ubhayalu += aksharas

    elif re.match(r'^[క-హ][ా-ౌ]$', akshara):
        if akshara[1] == 'ై':
            indeps += aksharas
        elif akshara[0] in bad_hallulu_str or akshara[1] in bad_gunintams_str:
            bad_achallulu += aksharas
        else:
            achallulu += aksharas

    elif re.match(r'^[క-హ]్$', akshara):
        indeps += aksharas

    else:
        print("ERROR in recognizing ", akshara)

print("indeps ", len(indeps), indeps)
print("hallulu ", len(hallulu), hallulu)
print("hallulu2 ", len(bad_hallulu), bad_hallulu)
print("ubhayalu ", len(ubhayalu), ubhayalu)
print("achallulu ", len(achallulu), achallulu)
print("achallulu2 ", len(bad_achallulu), bad_achallulu)
print("vattulu ", len(vattulu), vattulu)

assert len(achallulu) >= len(vattulu)
assert len(hallulu) >= len(ubhayalu)

seed(seed_at)
shuffle(vattulu)
shuffle(ubhayalu)

print("Adding vattulu to acchallulu.")
for i in range(len(vattulu)):
    achallulu[i] = achallulu[i][0] + vattulu[i] + achallulu[i][1]

print("Adding ubhayalu to hallulu.")
for i in range(len(ubhayalu)):
    hallulu[i] += ubhayalu[i]

print("Combining and shuffling.")
text = indeps + hallulu + achallulu + bad_hallulu + bad_achallulu
shuffle(text)

print("Adding space.")
spacing = '    '
data = ''
for i, t in enumerate(text):
    data += t + spacing
    if (i+1) % aksharas_per_line == 0:
        data += "\n"
    if (i+1) % (aksharas_per_line * 5) == 0:
        data += "\n"

data += '\n' + (spacing+spacing).join(['కౢ', 'కౣ', 'క్ష్', 'ప్పు'])

out_file = input_file + '_{:d}_{:d}.txt'.format(aksharas_per_line, seed_at)
print("Writing output to file: ", out_file)
with open(out_file, 'w') as out_fp:
    out_fp.write(data)
