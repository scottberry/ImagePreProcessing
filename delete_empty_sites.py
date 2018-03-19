#! /usr/bin/env python

import time
import warnings
import logging
import argparse
import numpy as np
import multiprocessing as mp
import tifffile as tiff
import os
import re
from subprocess import check_call, CalledProcessError
from MultiProcessingLog import MultiProcessingLog
from jtmodules import smooth, threshold_manual, filter, label

# open DAPI tiff
# segment DAPI tiff
# count objects with size > xx


warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def segment_primary(dapi):
    dapiSmooth = smooth.main(dapi,'gaussian',7)
    nucleiMask = threshold_manual.main(
        image=dapiSmooth.smoothed_image,
        threshold=107
    )
    nucleiMaskFiltered = filter.main(
        mask=nucleiMask.mask,
        feature='area',
        lower_threshold=2000,
        upper_threshold=None,
        plot=False
    )
    nuclei = label.main(mask=nucleiMaskFiltered.filtered_mask)

    return nuclei


def contains_nucleus(dapi):
    nuclei = segment_primary(dapi)
    return True if np.max(nuclei.label_image) > 0 else False


def load_image(source_dir, fname):
    image = tiff.imread(os.path.join(source_dir,fname))
    return image


def list_all_files_same_site(source_dir, fname):
    pattern = (r'(?P<stem>.+)_(?P<well>[A-Z]\d{2})_T(?P<t>\d+)' +
               r'F(?P<site>\d+)L\d+A\d+Z(?P<z>\d+)(?P<c>[C]\d{2})\.')
    matches = re.match(pattern, fname)
    search_string = (r'^' +
        re.escape(matches.group('stem')) +
        r'_' + matches.group('well') +
        r'_T(?P<t>\d+)' +
        matches.group('site') +
        r'L\d+A\d+Z(?P<z>\d+)(?P<c>[C]\d{2})\.')
    files = [f for f in os.listdir(source_dir) if re.match(search_string, f)]
    return files


def check_image(source_dir, fname, delete_empty=False):
    dapi = load_image(source_dir,fname)
    if not contains_nucleus(dapi):
        files = list_all_files_same_site(fname)
        if delete_empty:
            for file in files:
                try:
                    logger.info('deleting %s',file)
                    #os.remove(file)
                except OSError:
                    pass
    return



def convert_single_site_star(args):
    return convert_single_image(*args)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='convert_tiff_to_png',
        description=('Converts all files in a directory from TIFF'
                     ' to 16-bit grayscale PNG files.'
                     ' The directory structure from source_dir'
                     ' is re-created in output_dir.')
    )
    parser.add_argument(
        '-v', '--verbosity', action='count', default=0,
        help='increase logging verbosity'
    )
    parser.add_argument('source_dir', help='path to source directory')
    parser.add_argument('output_dir', help='path to output directory')

    return(parser.parse_args())


def main(args):

    # setup logging
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    mp_log = MultiProcessingLog(
        os.path.join(args.output_dir,
                  'png_conversion-' +
                  time.strftime('%Y%m%d-%H%M%S') +
                  '.log'),
        'w', 0, 0
    )
    mp_log.setFormatter(formatter)
    logger.addHandler(mp_log)

    tiff_paths = []
    output_dirs = []

    # find tiff files and keep track of the source directory structure
    for root, dirs, files in walk(args.source_dir):
        for file in files:
            if file.endswith('.tif'):
                tiff_paths.append(path.join(root, file))
                output_dirs.append(
                    path.join(args.output_dir, root[len(args.source_dir):])
                )

    # re-create the directory structure in output_dir
    unique_dirs = list(set(output_dirs))
    logger.info(
        'found %d TIFF files in subfolders: %s',
        len(tiff_paths),
        unique_dirs)
    for d in unique_dirs:
        if not path.exists(d):
            logger.info('creating output directory: %s',d)
            makedirs(d)
        else:
            logger.info('output directory %s already exists',d)

    # generate list of tuples containing input/output pairs
    convert_args = zip(tiff_paths, output_dirs)

    # use a multi-processing pool to get the work done
    pool = mp.Pool()
    pool.map(
        convert_single_site_star,
        convert_args
    )
    pool.close()
    pool.join()

    return


if __name__ == "__main__":
    args = parse_arguments()
    mp.freeze_support()
    main(args)
