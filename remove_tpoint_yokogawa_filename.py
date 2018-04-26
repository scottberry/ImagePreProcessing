import argparse
import os
import re
import glob

pattern = (r'(?P<stem>.+)_(?P<well>[A-Z]\d{2})_T(?P<t>\d+)' +
           r'F(?P<site>\d+)L(?P<l>\d+)A(?P<a>\d+)Z(?P<z>\d+)(?P<c>[C]\d{2})\.')

replacement = (r'\g<stem>_\g<well>_T0001F\g<site>L\g<l>A\g<a>Z\g<z>\g<c>.')


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='remove_tpoint_yokogawa_filename',
        description=('replaces T*** with T0001 in filename')
    )
    parser.add_argument('source_dir', help='path to source directory')

    return(parser.parse_args())


def main(args):

    # get all image filenames
    filenames = [os.path.basename(full_path) for full_path in glob.glob(args.source_dir + '*.png')]

    regex = re.compile(pattern)
    for filename in filenames:
        new_name = re.sub(regex,replacement,filename)
        os.rename(
            os.path.join(args.source_dir,filename),
            os.path.join(args.source_dir,new_name)
        )

    return


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
