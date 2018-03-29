#! /usr/bin/env python

import time
import warnings
import logging
import argparse
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


def links_per_well(source_dir, filenames_C01):

    files_to_link = []
    new_site_number = 0

    for fname_C01 in filenames_C01:
        new_site_number += 1
        old_names = sorted(list_all_files_same_site(source_dir, fname_C01))
        for old_name in old_names:
            matches = re.match(pattern, old_name)
            new_name = (matches.group('stem') +
                        '_' + matches.group('well') +
                        '_T0001' +
                        'F' + str(new_site_number).zfill(3) +
                        'L' + matches.group('l') +
                        'A' + matches.group('a') +
                        'Z' + matches.group('z') +
                        matches.group('c') + '.tif')
            files_to_link.append((old_name,new_name))

    return(files_to_link)


def main(args):

    if not os.path.exists(args.target_dir):
        os.makedirs(args.target_dir)

    # setup logging
    formatter = logging.Formatter('%(asctime)s %(levelname)s | %(filename)s/%(funcName)s: %(message)s')
    mp_log = MultiProcessingLog(
        os.path.join(args.target_dir,
                  'modify-site-order-' +
                  time.strftime('%Y%m%d-%H%M%S') +
                  '.log'),
        'w', 0, 0
    )
    mp_log.setFormatter(formatter)
    logger.addHandler(mp_log)

    # get all names for channel 01
    all_filenames_C01 = sorted([os.path.basename(full_path) for full_path in glob.glob(args.source_dir + '*C01.tif')])

    # get unique wells
    well_names = [m.group('well') for f in all_filenames_C01 for m in [re.match(pattern,f)] if m]
    unique_well_names = sorted(list(set(well_names)))

    # generate a list of tuples containing files to be linked
    files_to_link = []
    for well in unique_well_names:

        # split list by well_name
        well_regex = re.compile('.*_' + well + '_')
        fnames_C01 = filter(well_regex.match, all_filenames_C01)

        # generate list of links per well
        files_to_link.extend(
            links_per_well(args.source_dir, fnames_C01)
        )

    for fname_pair in files_to_link:
        logger.info('creating %s as link to %s',
                    os.path.join(args.target_dir,fname_pair[1]),
                    os.path.join(args.source_dir,fname_pair[0]))
        os.link(os.path.join(args.source_dir,fname_pair[0]),
                os.path.join(args.target_dir,fname_pair[1]))

    return


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
