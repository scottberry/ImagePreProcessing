#! /usr/bin/env python

import time
import warnings
import logging
import argparse
import numpy as np
import multiprocessing as mp
import imageio
import os
import re
import glob
from subprocess import check_call, CalledProcessError
from MultiProcessingLog import MultiProcessingLog
from jtmodules import smooth, threshold_manual, filter, label


warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


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
    logger.debug('loading image %s from %s',fname, source_dir)
    try:
        image = imageio.imread(os.path.join(source_dir,fname))
    except IOError:
        logger.info('failed to load %s in %s',fname, source_dir)
        pass
    return image


def list_all_files_same_site(source_dir, fname):
    pattern = (r'(?P<stem>.+)_(?P<well>[A-Z]\d{2})_T(?P<t>\d+)' +
               r'F(?P<site>\d+)L\d+A\d+Z(?P<z>\d+)(?P<c>[C]\d{2})\.')
    matches = re.match(pattern, fname)
    search_string = (r'^' +
                     re.escape(matches.group('stem')) +
                     r'_' + matches.group('well') +
                     r'_T(?P<t>\d+)' +
                     r'F' + matches.group('site') +
                     r'L\d+A\d+Z(?P<z>\d+)(?P<c>[C]\d{2})\.')
    logger.debug('finding files in %s, in well %s, site %s',
                 source_dir,
                 matches.group('well'),
                 matches.group('site'))
    files = [f for f in os.listdir(source_dir) if re.match(search_string, f)]
    return files


def check_site_and_move(source_dir, fname, target_dir, move_empty=False):
    dapi = load_image(source_dir,fname)
    if not contains_nucleus(dapi):
        logger.info('image %s does not contain any nuclei',fname)
        files = list_all_files_same_site(source_dir,fname)
        if move_empty:
            for file in files:
                try:
                    source_path = os.path.join(source_dir,file)
                    dest_path = os.path.join(target_dir,file)
                    logger.info('moving %s to %s',file, target_dir)
                    os.rename(source_path,dest_path)
                except OSError:
                    pass
        else:
            print fname
    else:
        logger.info('image %s contains > 0 nuclei')
    return


def check_site_and_move_star(args):
    return check_site_and_move(*args)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='move_empty_sites',
        description=('Checks all images in a folder for'
                     ' nuclei. Sites without any cells'
                     ' are identified and listed or moved.'
                     )
    )
    parser.add_argument(
        '-v', '--verbosity', action='count', default=0,
        help='increase logging verbosity'
    )
    parser.add_argument('source_dir', help='path to source directory')
    parser.add_argument('target_dir', help='path to destination directory')
    parser.add_argument('--move', action='store_true', help='move sites identified as empty')

    return(parser.parse_args())


def main(args):

    # setup logging
    formatter = logging.Formatter('%(asctime)s %(levelname)s | %(filename)s/%(funcName)s: %(message)s')
    mp_log = MultiProcessingLog(
        os.path.join(args.source_dir,
                  'find-empty-sites-' +
                  time.strftime('%Y%m%d-%H%M%S') +
                  '.log'),
        'w', 0, 0
    )
    mp_log.setFormatter(formatter)
    logger.addHandler(mp_log)

    if args.move and (not os.path.exists(args.target_dir)):
        os.makedirs(args.target_dir)

    images = [os.path.basename(full_path) for full_path in glob.glob(args.source_dir + '*C01.tif')]
    logger.debug('found %d images in %s',len(images),args.source_dir)
    source_dirs = [args.source_dir for image in images]
    target_dirs = [args.target_dir for image in images]
    params = [args.move for image in images]

    function_args = zip(source_dirs,images,target_dirs,params)

    # use a multi-processing pool to get the work done
    pool = mp.Pool()
    pool.map(
        check_site_and_move_star,
        function_args
    )
    pool.close()
    pool.join()

    return


if __name__ == "__main__":
    args = parse_arguments()
    mp.freeze_support()
    main(args)
