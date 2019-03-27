import time
import logging
import argparse
import os
import re
import glob
import random

yokogawa_pattern = (r'(?P<stem>.+)_(?P<well>[A-Z]\d{2})_T(?P<t>\d+)' +
                    r'F(?P<site>\d+)L(?P<l>\d+)A(?P<a>\d+)Z(?P<z>\d+)' +
                    r'(?P<c>[C]\d{2})\.')


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='extend_plate_to_full_size',
        description=('Fills partially complete plates by matching '
                     'the number of wells/sites from a set of input '
                     'plates. Input directory should contain subfolders '
                     'called "plate_name"/images/.')
    )
    parser.add_argument(
        'plates_dir',
        help='path to directory containing plate subfolders')

    return(parser.parse_args())


def initialise_logger():

    logger = logging.getLogger('extend_plate_to_full_size')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(
        os.path.join(
            'extend_plate_to_full_size-' +
            time.strftime('%Y%m%d-%H%M%S') +
            '.log')
    )
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s ' +
                                  '| %(filename)s/%(funcName)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return(logger)


def list_all_files_for_well(src_dir, well):
    search_string = (r'(?P<stem>.+)_' +
                     well +
                     r'_T(?P<t>\d+)' +
                     r'F\d+' +
                     r'L\d+A\d+Z(?P<z>\d+)(?P<c>[C]\d{2})\.')
    files = [f for f in os.listdir(src_dir) if re.match(search_string, f)]
    return files


def main(args):

    logger = initialise_logger()

    # find all "images" directories
    logger.info('Scanning source directory for "images" folders')
    images_paths = []
    for root, dirs, files in os.walk(args.plates_dir):
        for name in dirs:
            if (name == "images"):
                logger.info("Found image folder %s",os.path.join(root, name))
                images_paths.append(os.path.join(root, name))

    # scan "images" directories and find which wells exist
    plate_wells = []
    for image_folder in images_paths:
        logger.info('Scanning %s for images',image_folder)
        files = [os.path.basename(full_path)
                 for full_path in glob.glob(image_folder + '/*C01.png')]

        # get unique wells
        well_names = [m.group('well') for f in files
                      for m in [re.match(yokogawa_pattern,f)] if m]
        unique_wells = sorted(list(set(well_names)))
        logger.info('In %s, found %d wells',image_folder,len(unique_wells))
        logger.info('Wells: {}'.format(', '.join(unique_wells)))
        plate_wells.append([image_folder, unique_wells])

    # compile a list of wells present in at least one plate
    all_wells = [x[1] for x in plate_wells]
    all_wells = sorted(list(set(
        [item for sublist in all_wells for item in sublist])))
    logger.info('Unique well list over all plates: {}'.format(
        ' ,'.join(all_wells)))

    # for every image folder compile a list of missing wells
    missing_plate_wells = [[w[0], list(set(all_wells) - set(w[1]))]
                           for w in plate_wells]

    # separate plates that have and do not have missing wells
    missing_plate_wells = [w for w in missing_plate_wells if len(w[1]) != 0]

    # for each plate with missing wells,
    # replace the missing wells with randomly chosen wells
    for images_path, wells in missing_plate_wells:
        logger.info('Missing wells in plate {} : {}'.format(
            images_path,' ,'.join(wells))
        )
        plate_path = os.path.split(images_path)[0]
        root, plate_name = os.path.split(plate_path)
        filled_plate_path = os.path.join(root,plate_name + '_filled','images')

        logger.info('Creating path {}'.format(filled_plate_path))
        if not os.path.exists(filled_plate_path):
            os.makedirs(filled_plate_path)

        for well in wells:
            # generate a list of plates that contain the current well
            # and select one randomly
            available_plate_paths = [p[0] for p in plate_wells if well in p[1]]
            random_plate_path = random.choice(available_plate_paths)

            # get a list of all files from the current well in the random plate
            src_files = list_all_files_for_well(random_plate_path, well)
            logger.info('Found {} images for well {} on plate {}'.format(
                len(src_files),well,random_plate_path))

            # create hard links in the new "filled"
            # folder from the chosen files
            for src_file in src_files:

                src_path = os.path.join(random_plate_path, src_file)
                dest_path = os.path.join(filled_plate_path, src_file)

                logger.info('Linking {} to {}'.format(
                    src_path, dest_path))

                if not os.path.isfile(dest_path):
                    os.link(src_path, dest_path)
                else:
                    logger.warn(
                        'Destination file {} already exists'.format(dest_path)
                    )

        # also link the original "non-missing" image files
        nonmissing_files = os.listdir(images_path)
        for src_file in nonmissing_files:
            src_path = os.path.join(images_path, src_file)
            dest_path = os.path.join(filled_plate_path, src_file)

            logger.info('Linking original {} to {}'.format(
                src_path, dest_path))

            if not os.path.isfile(dest_path):
                os.link(src_path, dest_path)
            else:
                logger.warn(
                    'Destination file {} already exists'.format(dest_path)
                )


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
