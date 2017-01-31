import logging

from .ngramgraph import GramGraph
from .scaler import ScalerFactory
from .bantry import Bantry, BantryFile
from .classifier import Classifier
from .ngram import Ngram


class OCR():
    def __init__(self,
                 nnet_fname,
                 scaler_fname,
                 labels_fname,
                 ngram_fname,
                 logbase=1,
                 loglevel=logging.INFO,):
        self.nnet_fname = nnet_fname
        self.scaler_fname = scaler_fname
        self.labels_fname = labels_fname
        self.ngram_fname = ngram_fname
        self.logbase = logbase
        self.loglevel = loglevel
        self.loglevelname = logging._levelToName[loglevel].lower()

        Bantry.scaler = ScalerFactory(scaler_fname)
        Bantry.classifier = Classifier(nnet_fname, labels_fname,
                                       logbase=logbase)
        self.ng = Ngram(ngram_fname)
        Bantry.ngram = self.ng
        GramGraph.set_ngram(self.ng)
        logging.basicConfig(level=self.loglevel,
                            filename=None)

    def ocr_box_file(self, box_fname):
        # Set up the names of output files
        replace = lambda s: box_fname.replace('.box', s)

        log_fname = replace('.{}.log'.format(self.loglevelname))
        log = logging.getLogger()  # root logger
        print("Log : ", log_fname)
        for hdlr in log.handlers[:]:  # remove all old handlers
            # hdlr.stream.close()
            log.removeHandler(hdlr)
        log_fh = logging.FileHandler(log_fname, 'w')
        log.addHandler(log_fh)

        # Read Bantries & get Most likely output
        bf = BantryFile(box_fname)

        def get_gramgraph():
            # Process using ngrams
            for linenum in range(bf.num_lines):
                line_bantries = bf.get_line_bantires(linenum)
                gramgraph = GramGraph(line_bantries)
                gramgraph.process_tree()
                yield gramgraph

        return bf, get_gramgraph()