#! /usr/bin/env python

import time
import warnings
import logging
import argparse
import os
import re
import glob
import random
from MultiProcessingLog import MultiProcessingLog
from operator import itemgetter

warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

pattern = (r'(?P<stem>.+)_(?P<well>[A-Z]\d{2})_T(?P<t>\d+)' +
           r'F(?P<site>\d+)L(?P<l>\d+)A(?P<a>\d+)Z(?P<z>\d+)(?P<c>[C]\d{2})\.')

possible_site_numbers = sorted(list(set([i * j for j in range(10,20) for i in range(j-5,j)])))


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
        prog='extend_wells_to_max_site_number',
        description=('Finds the maximum site number for a well and extends'
                     ' all wells to that length using random images')
    )
    parser.add_argument('source_dir', help='path to source directory')
    parser.add_argument('empty_dir', help='path to directory containing empty images')
    parser.add_argument('target_dir',
                        help='path to directory where new links should be created')

    return(parser.parse_args())


def main(args):

    if not os.path.exists(args.target_dir):
        os.makedirs(args.target_dir)

    # setup logging
    formatter = logging.Formatter('%(asctime)s %(levelname)s | %(filename)s/%(funcName)s: %(message)s')
    mp_log = MultiProcessingLog(
        os.path.join(args.target_dir,
                  'extend-wells-to-max-site-number' +
                  time.strftime('%Y%m%d-%H%M%S') +
                  '.log'),
        'w', 0, 0
    )
    mp_log.setFormatter(formatter)
    logger.addHandler(mp_log)

    # get all names for channel 01
    all_filenames_C01 = sorted([os.path.basename(full_path) for full_path in glob.glob(args.source_dir + '*C01.tif')])

    # get unique well and sites
    well_site_names = [(m.group('well'), int(m.group('site'))) for f in all_filenames_C01 for m in [re.match(pattern,f)] if m]

    # find number of sites per well
    unique_wells = sorted(list(set([i[0] for i in well_site_names])))
    logger.info('found %d wells in %s', len(unique_wells), args.source_dir)
    max_sites_per_well = []
    for well in unique_wells:
        sites = [x for x in well_site_names if x[0] == well]
        n = max(sites,key=itemgetter(1))
        max_sites_per_well.append(n)
        logger.debug('well %s has %d sites', well, n[1])

    # find maximum number of sites and select the next largest value from list
    required_sites = max(max_sites_per_well,key=itemgetter(1))[1]
    n_sites = next(v for i,v in enumerate(possible_site_numbers) if v >= required_sites)
    logger.info('%d sites are required, generating links for %d sites per well', required_sites, n_sites)

    # generate a list of (well, site) pairs to add
    well_site_names_to_add = []
    for well in unique_wells:
        last_real_site = [x[1] for x in max_sites_per_well if x[0] == well]
        well_site_names_to_add.extend([(well,s) for s in range(last_real_site[0] + 1,n_sites + 1)])

    # convert this list to filenames for all channels
    # 1. use the first site as a template for new filenames
    # 2. randomly select a site from the empty directory and
    #    link the corresponding channels to that site
    filenames_single_site = sorted(
        list_all_files_same_site(
            args.source_dir, all_filenames_C01[0]
        )
    )
    files_to_link = []
    empty_files = [os.path.basename(full_path) for full_path in glob.glob(args.empty_dir + '*.tif')]

    logger.debug('selecting random sites from %s',args.empty_dir)
    for well, site in well_site_names_to_add:
        empty_site = re.match(pattern,random.choice(empty_files))
        for basefile in filenames_single_site:
            new_site = re.match(pattern, basefile)
            link_name = (
                new_site.group('stem') +
                '_' + well +
                '_T' + new_site.group('t') +
                'F' + str(site).zfill(3) +
                'L' + new_site.group('l') +
                'A' + new_site.group('a') +
                'Z' + new_site.group('z') +
                new_site.group('c') + '.tif'
            )

            # add a couple of catches to account for differing dimensions between sites
            if (int(new_site.group('z')) < 20) and (new_site.group('c') == 'C04'):
                z_plane = new_site.group('z')
            elif (int(new_site.group('z')) < 40) and (new_site.group('c') == 'C03'):
                z_plane = new_site.group('z')
            else:
                z_plane = '01'

            source_file = (
                empty_site.group('stem') +
                '_' + empty_site.group('well') +
                '_T' + new_site.group('t') +
                'F' + empty_site.group('site') +
                'L' + new_site.group('l') +
                'A' + new_site.group('a') +
                'Z' + z_plane +
                new_site.group('c') + '.tif'
            )
            files_to_link.append((source_file, link_name))

    for source, link in files_to_link:
        logger.info(
            'creating hard link %s to file %s',
            os.path.join(args.target_dir,link),
            os.path.join(args.empty_dir,source)
        )
        try:
            os.link(os.path.join(args.empty_dir,source),
                    os.path.join(args.target_dir,link))
        except OSError:
            logger.warning(
                'could not link %s to %s',
                os.path.join(args.target_dir,link),
                os.path.join(args.empty_dir,source)
            )
            pass

    return

if __name__ == "__main__":
    args = parse_arguments()
    main(args)
