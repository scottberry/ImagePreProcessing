import warnings
import logging
import itertools
import skimage.io
import numpy as np
from os import path, getcwd
import multiprocessing as mp
from MultiProcessingLog import MultiProcessingLog

warnings.filterwarnings('ignore')

logger = logging.getLogger()
mp_log = MultiProcessingLog(path.join(getcwd(), 'StackToMaxSum.log'), 'a', 0, 0)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
mp_log.setFormatter(formatter)
logger.addHandler(mp_log)
logger.setLevel(logging.INFO)


def project_single_site(base_dir, fname_stub,
                        well_name, timeline_name,
                        field, l_name,
                        action_name, input_channel_name,
                        output_channel_names, z_planes,
                        input_dir, output_dir):

    logger.info('Processing channel %s, well %s, site %d',
                input_channel_name, well_name, field)
    field_name = 'F' + str(field).zfill(3)

    image_names = []
    for z in range(1, z_planes + 1):
        z_name = 'Z' + str(z).zfill(2)

        image_names.append(
            (
                fname_stub + well_name + '_' + timeline_name + field_name +
                l_name + action_name + z_name + input_channel_name + '.tif'
            )
        )

    image_paths = [
        path.join(base_dir, input_dir, in_name) for in_name in image_names
    ]

    logger.debug('Well %s, site %d, image paths %s', well_name, field, image_paths)
    ic = skimage.io.imread_collection(image_paths)
    arr = skimage.io.concatenate_images(ic)
    sum_proj = np.sum(arr, axis=0, dtype=np.uint16)
    max_proj = np.max(arr, axis=0)

    max_name = (
        fname_stub + well_name + '_' + timeline_name + field_name +
        l_name + action_name + 'Z01' + output_channel_names[0] + '.tif'
    )
    sum_name = (
        fname_stub + well_name + '_' + timeline_name + field_name +
        l_name + action_name + 'Z01' + output_channel_names[1] + '.tif'
    )

    max_path = path.join(base_dir, output_dir, max_name)
    sum_path = path.join(base_dir, output_dir, sum_name)

    logger.info('Channel %s, well %s, Site %d, saving max projection: %s',
                input_channel_name, well_name, field, max_path)
    skimage.io.imsave(fname=max_path, arr=max_proj)

    logger.info('Channel %s, well %s, Site %d, saving sum projection: %s',
                input_channel_name, well_name, field, sum_path)
    skimage.io.imsave(fname=sum_path, arr=sum_proj)

    return


def project_single_site_star(args):
    return project_single_site(*args)


def main():

    # Define parameters
    # -----------------
    base_dir = path.join(
        path.expanduser('~'), 'pelkmans-sc-storage',
        '20170807-Kim2-NascentRNA-Inhibitors'
    )
    input_dir = 'ACQ03'
    output_dir = 'MAXSUM'

    fname_stub = '20170807-Kim2-NascentRNA-Inhibitors-DAPI-EU-Beads-SE-3_'

    well_name_list = (
        ['G' + str(i).zfill(2) for i in range(8, 9)]
#        ['E' + str(i).zfill(2) for i in range(9, 12)] +
#        ['F' + str(i).zfill(2) for i in range(9, 12)] +
#        ['G' + str(i).zfill(2) for i in range(9, 12)]
    )

    timeline_name = 'T0002'
    action_name = 'A02'
    l_name = 'L02'
    z_planes = 16
    n_fields = 48

    # Map input channel C03 to C03 (max), C04 (sum)
    input_channel_name = 'C03'
    output_channel_names = ['C03', 'C04']

    # create a multiprocessing pool for parallelisation
    pool = mp.Pool()
    fields = range(1, n_fields + 1)
    pool.map(
        project_single_site_star,
        [(base_dir, fname_stub,
            well, timeline_name,
            site, l_name,
            action_name, input_channel_name,
            output_channel_names, z_planes,
            input_dir, output_dir) for well, site in itertools.product(well_name_list, fields)]
    )
    pool.close()
    pool.join()

    # Map input channel C04 to C05 (max), C06 (sum)
    input_channel_name = 'C04'
    output_channel_names = ['C05', 'C06']

    # create a multiprocessing pool for parallelisation
    pool = mp.Pool()
    fields = range(1, n_fields + 1)
    pool.map(
        project_single_site_star,
        [(base_dir, fname_stub,
            well, timeline_name,
            site, l_name,
            action_name, input_channel_name,
            output_channel_names, z_planes,
            input_dir, output_dir) for well, site in itertools.product(well_name_list, fields)]
    )
    pool.close()
    pool.join()


if __name__ == "__main__":
    mp.freeze_support()
    main()
