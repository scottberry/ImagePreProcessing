#! /usr/bin/env python

import time
import warnings
import logging
import argparse
import numpy as np
import os
import re
import glob
from MultiProcessingLog import MultiProcessingLog


warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

pattern = (r'(?P<stem>.+)_(?P<well>[A-Z]\d{2})_T(?P<t>\d+)' +
           r'F(?P<site>\d+)L(?P<l>\d+)A(?P<a>\d+)Z(?P<z>\d+)(?P<c>[C]\d{2})\.')


def list_all_files_same_site(source_dir, fname):
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


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='move_empty_sites',
        description=('Generates a second folder containing hard links'
                     ' to images with their filenames modified for '
                     ' contiguous site numbering')
    )
    parser.add_argument(
        '-v', '--verbosity', action='count', default=0,
        help='increase logging verbosity'
    )
    parser.add_argument('source_dir', help='path to source directory')
    parser.add_argument('target_dir', help='path to destination directory')

    return(parser.parse_args())


def main(args):

    # setup logging
    formatter = logging.Formatter('%(asctime)s %(levelname)s | %(filename)s/%(funcName)s: %(message)s')
    mp_log = MultiProcessingLog(
        os.path.join(args.source_dir,
                  'modify-site-order-' +
                  time.strftime('%Y%m%d-%H%M%S') +
                  '.log'),
        'w', 0, 0
    )
    mp_log.setFormatter(formatter)
    logger.addHandler(mp_log)

    if not os.path.exists(args.target_dir):
        os.makedirs(args.target_dir)

    extant_filenames_C01 = sorted([os.path.basename(full_path) for full_path in glob.glob(args.source_dir + '*C01.tif')])

    files_to_link = []
    new_site_number = 0
    for fname_C01 in extant_filenames_C01:
        new_site_number += 1
        for old_name in sorted(list_all_files_same_site(args.source_dir, fname_C01)):
            matches = re.match(pattern, old_name)
            new_name = (matches.group('stem') +
                        '_' + matches.group('well') +
                        '_T0001' +
                        'F' + str(new_site_number).zfill(3) +
                        'L' + matches.group('l') +
                        'A' + matches.group('a') +
                        'Z' + matches.group('z') +
                        matches.group('c') + '.tif')
            print old_name, new_name
            files_to_link.append((old_name,new_name))

#    print files_to_link

    return

if __name__ == "__main__":
    args = parse_arguments()
    main(args)
