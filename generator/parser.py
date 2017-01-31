import enum
import logging
import os
import numpy as np

from banti.bantry import Space, Bantry
from banti.linegraph import LineGraph
from TeluguDiacriticMap import Map
from TeluguFontProperties import ABBR_DICT, PPU

logger = logging.getLogger(__name__)
logw = logger.warn
logi = logger.info
logd = logger.debug


@enum.unique
class Task(enum.Enum):
    whole = 1
    split = 2
    first = 3
    second = 4
    whole_opt_both = 5
    whole_opt_first = 6
    whole_opt_second = 7
    ppu = 8

    def __repr__(self):
        return self.name


class TaskAkshara():
    def __init__(self, task, whole, first=None, second=None):
        self.task = task
        self.whole = whole
        self.first = first
        self.second = second

    def __repr__(self):
        return "Whole {}: Task={} First={} Second={}" \
               "".format(self.whole, self.task, self.first, self.second)

    def __eq__(self, other):
        return self.task == other


def get_parts(akshara):
    # Class of tick plus underlying consonant + vowel
    if '''ఘాఘుఘూఘౌపుపూఫుఫూషుషూసుసూహా
    హుహూహొహోహౌ'''.find(akshara) >= 0:
        return ['✓', akshara]

    # Class of vowel-mark + underlying consonant base
    if '''ఘిఘీఘెఘేపిపీపెపేఫిఫీఫెఫేషిషీషెషేసిసీసె
    సేహిహీహెహేఘ్ప్ఫ్ష్స్హ్ '''.find(akshara) >= 0:
        return [akshara[1], akshara[0]]

    # Detached ai-karams
    if 'ఘైపైఫైషైసైహై'.find(akshara) >= 0:
        raise ValueError
        # return ['ె' , akshara[0], 'ై']

    # gho
    if 'ఘొఘో'.find(akshara) >= 0:
        if 'T' == 'T':  # Telugu gho_style style ఘొఘో
            return ['✓', akshara]
        else:  # Kannada style
            return ['ె', 'ఘా' if akshara == 'ఘో' else 'ఘు']

    # Combining marks like saa, pau etc.
    return [akshara]


def nature(akshara):
    if akshara.startswith("క్ష"):
        ret = TaskAkshara(Task.whole_opt_second, akshara, second="్ష")

    elif akshara[0] in "ఘపఫసషహ":
        parts = get_parts(akshara)
        if len(parts) == 1:
            ret = TaskAkshara(Task.whole, akshara)
        else:
            ret = TaskAkshara(Task.whole_opt_both, akshara, parts[0], "-" + parts[1])

    elif akshara[-1] in "ఁంఃృౄౢౣ":
        ret = TaskAkshara(Task.split, akshara, akshara[0], akshara[1])

    elif akshara == "కై":
        ret = TaskAkshara(Task.second, akshara, "కె", "ై")

    elif akshara[-1] in "ుూ":
        ret = TaskAkshara(Task.whole_opt_second, akshara, second=akshara[-1])

    elif akshara in "ౘౙ":
        ret = TaskAkshara(Task.whole_opt_first, akshara, first="౨౨")

    elif "్" in akshara[:-1]:
        assert len(akshara) == 4
        ret = TaskAkshara(Task.split, akshara, akshara[0] + akshara[-1], akshara[1:3])

    elif akshara == "ప్పు":
        ret = TaskAkshara(Task.ppu, akshara)

    else:
        ret = TaskAkshara(Task.whole, akshara)

    logd("Nature {}".format(ret))
    return ret


def known(s):
    if s in Bantry.classifier.unichars.labels:
        return True
    else:
        logd("{} is not found in labellings.lbl".format(s))
        return False


class Parser():
    def __init__(self, ocr, txt_file, dir_prefix):
        self.ocr = ocr
        self.txt_file, self.dir_prefix = txt_file, dir_prefix
        with open(txt_file, "r") as fp:
            lines = fp.read().splitlines()
            self.text = [l for l in lines if l]

        self.existings_dirs = set()
        dir_prefix += "" if dir_prefix.endswith(".") else "."
        self.dir = self.ensure_dir(dir_prefix + "glyphs")

        # Current File
        self.font, self.font_style, self.font_properties = "", "", []
        # Current Line
        self.lbantries = []
        self.lgraph = LineGraph([Bantry()])
        self.lindices = []
        self.laksharas = []

        self.iline, self.iword = 0, 0

    def ensure_dir(self, d):
        if d not in self.existings_dirs:
            if not os.path.isdir(d):
                logi("Creating folder {}".format(d))
                os.system('mkdir ' + d)
            self.existings_dirs.update(d)
        return d + '/'

    def ensure_glyph_dir(self, parent_dir, akshara):
        if not parent_dir.endswith("/"):
            parent_dir += "/"

        subdir = Map(akshara) if akshara is not None else ""
        return self.ensure_dir(parent_dir + subdir)

    def get_image_name(self, box):
        return '{}_{}_L{:02}W{:02}_{}_{}.tif'.format(
            self.font, self.font_style, box.linenum, box.wordnum,
            box.y - box.topline,
            box.y + box.ht - box.baseline)

    def save_bantry_img(self, akshara, bantry, parent_dir_tag):
        parent_dir = self.ensure_dir(self.dir + parent_dir_tag)
        out_imgname = self.ensure_glyph_dir(parent_dir, akshara) + self.get_image_name(bantry)
        logd("Saving image: " + out_imgname)
        bantry.img.save(out_imgname, compression="packbits")

    def process_file(self, box_file_name):
        just_file_name = os.path.splitext(os.path.basename(box_file_name))[0]
        logi("Processing " + just_file_name)

        self.font, self.font_style = just_file_name.split("_")
        self.font_properties = ABBR_DICT[self.font]

        bantry_file, get_gramgraph = self.ocr.ocr_box_file(box_file_name)

        for iline in range(bantry_file.num_lines):
            logi("Processing line number {}".format(iline))
            self.iline = iline
            self.lbantries = bantry_file.get_line_bantires(iline)
            self.lgraph = next(get_gramgraph)
            self.process_line()

    def process_line(self):
        self.laksharas = self.text[self.iline].split()
        start_indices = [i + 1 for (i, b) in enumerate(self.lbantries)
                         if b is Space]
        self.lindices = [0] + start_indices + [len(self.lbantries) + 1]

        naksharas = len(self.laksharas)
        nspaces = len(self.lindices) - 1
        assert naksharas == nspaces, "#Aksharas={} != {}=#Spaces!".format(naksharas, nspaces)
        logi("Number of Words: {}"
             "\nNumber of Spaces: {}"
             "\nWords: {}"
             "\nIndices: {}".format(naksharas, nspaces, self.laksharas, self.lindices))

        for iword in range(naksharas):
            logi("Processing word number {}".format(iword))
            self.iword = iword
            self.process_word()

    def get_all_combos(self, start, end):
        return ((left_bantry, right_bantry)
                for (left_id, left_bantry) in self.lgraph.lchildren[start]
                for (right_id, right_bantry) in self.lgraph.lchildren[left_id]
                if right_id == end)

    def get_best_combo(self, start, end, first, second):
        wt = {False: .5, True: 1}
        max_strength, lb0, rb0 = 0, None, None
        for lb, rb in self.get_all_combos(start, end):
            strength = np.exp(lb.strength() + rb.strength())
            if known(first):
                strength *= wt[first == lb.best_char]
            if known(second):
                strength *= wt[second == rb.best_char]

            if strength > max_strength:
                max_strength, lb0, rb0 = strength, lb, rb

        return lb0, rb0

    def save_whole_banty(self, akshara, start, end, parent_dir_tag):
        if end - start == 1:
            whole_bantry = self.lbantries[start]
        else:
            child_ids, child_bantries = zip(*self.lgraph.lchildren[start])
            whole_bantry = child_bantries[child_ids.index(end)]

        self.save_bantry_img(akshara, whole_bantry, parent_dir_tag)

    def process_word(self):
        akshara = self.laksharas[self.iword]
        start, end = self.lindices[self.iword:self.iword + 2]
        end -= 1  # Do not pick up space
        bantries = self.lbantries[start:end]

        tskak = nature(akshara)
        nbantries = end - start
        bestchars = [b.best_char for b in bantries]
        info = "L{:2} W{:2} {} GlyphMatches:{}".format(self.iline, self.iword, tskak, bestchars)
        logi("Word Info " + info)

        if tskak == Task.whole:
            self.save_whole_banty(tskak.whole, start, end, "good")
            if nbantries > 1:
                if nbantries > 2:
                    logi("\t Expected whole, got {:2} pieces in {}".format(nbantries, info))

                lb, rb = self.get_best_combo(start, end, None, None)
                self.save_bantry_img(None, lb, "leftpieces")
                self.save_bantry_img(None, rb, "rightpieces")

        elif tskak == Task.split:
            if nbantries == 2:
                self.save_bantry_img(tskak.first, bantries[0], "good")
                self.save_bantry_img(tskak.second, bantries[1], "good")

            elif nbantries == 1:
                logw("\t {:2} pieces are attached! {}".format(nbantries, info))
                self.save_bantry_img(None, bantries[0], "attached")

            elif nbantries > 2:
                logw("\t 2 pieces expected  got {:2}. Finding best. {}".format(nbantries, info))
                lb, rb = self.get_best_combo(start, end, tskak.first, tskak.second)
                self.save_bantry_img(tskak.first, lb, "maybe")
                self.save_bantry_img(tskak.second, rb, "maybe")

        elif tskak == Task.whole_opt_both:
            self.save_whole_banty(tskak.whole, start, end, "good")
            if nbantries == 2:
                self.save_bantry_img(tskak.first, bantries[0], "leftpieces")
                self.save_bantry_img(tskak.second, bantries[1], "rightpieces")

        elif tskak == Task.whole_opt_first:
            self.save_whole_banty(tskak.whole, start, end, "good")
            if nbantries == 2:
                self.save_bantry_img(tskak.first, bantries[0], "leftpieces")

        elif tskak == Task.whole_opt_second:
            self.save_whole_banty(tskak.whole, start, end, "good")
            if nbantries == 2:
                self.save_bantry_img(tskak.second, bantries[1], "rightpieces")

        elif tskak == Task.second:
            if nbantries == 1:
                self.save_bantry_img(None, bantries[0], "attached")

            elif nbantries == 2:
                self.save_bantry_img(tskak.second, bantries[1], "good")

            elif nbantries > 2:
                _, rb = self.get_best_combo(start, end, tskak.first, tskak.second)
                self.save_bantry_img(tskak.second, rb, "maybe")

        elif tskak == Task.first:
            raise NotImplementedError(tskak)

        elif tskak == Task.ppu:
            if self.font_properties[PPU]:
                logi("Ignoring ppu")

        else:
            raise ValueError(tskak)

    def __repr__(self):
        return """Parser:
        Text:{}
        Dir_prefix:{}
        Output Dir:{}
        Currently
            Font:{} Style:{}
            Line:{} Word:{}""".format(
            self.txt_file, self.dir_prefix, self.dir,
            self.font, self.font_style, self.iline, self.iword
        )