import os
from PIL import Image as im
import sys
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d as gauss
from getch import getch

################################### Utils

def side_stack(counts, width):
    ret = np.zeros((len(counts), width))
    for i, x in enumerate(counts):
        ret[i, 1:x + 1] = 1
    return ret


def down_stack(counts, ht):
    ret = np.zeros((ht, len(counts)))
    for i, x in enumerate(counts):
        ret[1:x + 1, i] = 1
    return ret


def slab(arr2, markers=()):
    for irow, row in enumerate(arr2.astype(int)):
        end = ""
        if irow in markers:
            row[row == 0] = 2
            end = str(markers.index(irow) + 1)
        for c in row:
            print(" #_"[c], end="")
        print(end)


def get_gauss_filtered(hist, order):
    g = gauss(hist, 1, axis=-1, order=order, output=None, mode='nearest', truncate=2.0)
    return (g - g.min()) / (g.max() - g.min())


def get_num_ink_runs(arr):
    diffs = arr[:, 1:] - arr[:, :-1]
    runs = np.maximum(diffs, 0).sum(axis=1) + arr[:, 0]
    return runs / runs.max()

################################### Main Code
TOP = 3


class File():
    from_dir = ""
    to_dir = ""

    def __init__(self, name):
        self.name = name
        base_name = os.path.splitext(name)[0]
        self.font, self.style, self.loc, self.top, self.bot = base_name.split("_")
        self.line, self.word = int(self.loc[1:3]), int(self.loc[-2:])
        self.img = im.open(self.from_dir + name)
        self.arr = 1 - np.array(self.img) / 255
        self.ht, self.wd = self.arr.shape
        self.top = int(self.top)
        self.bot = int(self.bot)

    def __repr__(self):
        return "{} {} {} Line{} Word{} Top{} Bot{}".format(self.name,
                                                           self.font, self.style, self.line,
                                                           self.word, self.top, self.bot)

    def __lt__(self, other):
        if self.loc != other.loc:
            return self.loc < other.loc
        else:
            return self.font + self.style < other.font + other.style

    def process(self):
        self.hist = self.arr.sum(axis=1)
        self.ghist2 = get_gauss_filtered(self.hist, 2)
        self.ink_runs = get_num_ink_runs(self.arr)

        self.candidates = np.argsort(-self.ghist2[self.ht // 2:-self.ht // 10]) + self.ht // 2
        at = 0
        while at + TOP <= len(self.candidates):
            curr_candidates = self.candidates[at:at + TOP]
            slab(self.arr, list(curr_candidates - 1))
            print(self)
            cut = getch()
            print(cut)

            if ord(cut) == 3:
                raise KeyboardInterrupt

            if cut == "\r":
                return "skip_rest"

            try:
                cut = int(cut)
            except ValueError:
                return "skipped"

            if 0 < cut <= TOP:
                cut_at = curr_candidates[cut - 1]
                print("Cutting at {} (Ht: {})".format(cut_at, self.ht))
                self.cut_n_save(cut_at)
                return "ok"

            if cut == 0:
                at = max(0, at - TOP)
            else:
                at += TOP

        return "skipped"

    def cut_n_save(self, cut_at):
        top, bot = self.arr[:cut_at], self.arr[cut_at:]
        namer = "{}{}_{}_{}_{{}}_{{}}.tif".format(self.to_dir, self.font, self.style, self.loc)

        def saver(arr_tosave, t, b):
            arr_tosave = (255 * (1 - arr_tosave)).astype('uint8')
            name = namer.format(t, b)
            im.fromarray(arr_tosave).convert("1").save(name)
            print("saved", name)

        saver(top, self.top, self.bot - (self.ht - cut_at))
        saver(bot, self.top + cut_at, self.bot)

    def save_appended(self):
        arr_tosave = np.hstack((self.arr,
                                side_stack(self.wd * self.ghist2, self.wd),
                                side_stack(self.wd * self.ink_runs, self.wd)))

        arr_tosave[self.ht // 2, :self.wd] = 0
        l = self.candidates[0]
        arr_tosave[l, :self.wd] = .5
        png_name = self.to_dir + self.name.replace('tif', 'png')
        arr_tosave = (255 * (1 - arr_tosave)).astype('uint8')
        im.fromarray(arr_tosave).save(png_name)
        print("Saved ", png_name)


def process_files(files):
    for file in files:
        ret = file.process()
        if ret == "skip_rest":
            return

##########################################################

img_dir = sys.argv[1]
File.from_dir = img_dir
File.to_dir = "/home/rakesha/tmp/rakesha/"
files = sorted([File(f) for f in os.listdir(img_dir) if str(f).endswith(".tif")])


def file_groups():
    group = [files[0]]
    for i in range(1, len(files)):
        f_prev, f = files[i - 1:i + 1]
        if f.loc == f_prev.loc:
            group.append(f)
        else:
            yield group
            group = [f]
    yield group

resps = ['n', 'y', 'y', 'n', 'n', 'n', 'y', 'y', 'y', 'y', 'y', 'y', 'n', 'n', 'n', 'n', 'y',
         'n', 'n', 'n', 'n', 'y', 'y', 'y', 'y', 'n', 'y', 'y', 'y', 'y', 'y', 'n', 'y', 'y',
         'y', 'y', 'n', 'y', 'y']
print(sum([r=='y' for r in resps]))
print(sum([r=='n' for r in resps]))

for i, file_group in enumerate(file_groups()):
    print(i, "New group\n", file_group)
    # process_files(file_group)
    slab(file_group[0].arr)
    print(resps[i])
    getch()