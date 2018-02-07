#! /usr/bin/env python

import time
import warnings
import logging
import argparse
import multiprocessing as mp
from os import path, makedirs, walk
from subprocess import check_call, CalledProcessError
from MultiProcessingLog import MultiProcessingLog

warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def convert_single_image(source_path, target_dir):

    logger.info('Converting %s to PNG in %s', source_path, target_dir)
    try:
        check_call(
            ['mogrify','-depth', '16',
             '-colorspace', 'gray', '-format','png',
             '-path', target_dir, source_path]
        )
    except (CalledProcessError, OSError) as err:
        logger.error(
            'Mogrify failed to convert %s, %s',
            source_path, err
        )
        return -1

    return 0


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
        path.join(args.output_dir,
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
