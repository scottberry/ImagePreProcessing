import warnings
import logging
import skimage.io
import numpy as np
from os import path, getcwd
from joblib import Parallel, delayed, cpu_count

warnings.filterwarnings("ignore")

logger = logging.getLogger('StackToMaxSum.py')
hdlr = logging.FileHandler(path.join(getcwd(), 'StackToMaxSum.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

def project_single_site(base_dir, fname_stub, well_name, timeline_name,
                        field,
                        action_name, input_channel_name,
                        output_channel_names, z_planes,
                        input_dir, output_dir):

    logger.info('Processing channel %s, well %s, site %d',
                input_channel_name, well_name, field)
    l_name = 'L01'
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


# Define parameters
# -----------------

base_dir = path.join(
    path.expanduser('~'), 'pelkmans-sc-storage',
    '20170807-Kim2-NascentRNA-Inhibitors'
)
input_dir = 'ACQ01'
output_dir = 'MAXSUM'

fname_stub = '20170807-Kim2-NascentRNA-Inhibitors-DAPI-EU-Beads-SE_'
well_name_list = (
    ['B' + str(i).zfill(2) for i in range(2, 12)] +
    ['C' + str(i).zfill(2) for i in range(2, 12)] +
    ['D' + str(i).zfill(2) for i in range(2, 4)]
)

timeline_name = 'T0001'
action_name = 'A03'
z_planes = 16
n_fields = 48

n_cores = cpu_count()

# Map input channel C03 to C03 (max), C04 (sum)
input_channel_name = 'C03'
output_channel_names = ['C03', 'C04']

for well_name in well_name_list:

    # Process sites in parallel
    Parallel(n_jobs=n_cores)(
        delayed(project_single_site)
        (
            base_dir, fname_stub,
            well_name, timeline_name,
            i, action_name, input_channel_name,
            output_channel_names, z_planes,
            input_dir, output_dir
        ) for i in range(1, n_fields + 1)
    )

    # Map input channel C04 to C05 (max), C06 (sum)
    input_channel_name = 'C04'
    output_channel_names = ['C05', 'C06']

    # Process sites in parallel
    Parallel(n_jobs=n_cores)(
        delayed(project_single_site)
        (
            base_dir, fname_stub,
            well_name, timeline_name,
            i, action_name, input_channel_name,
            output_channel_names, z_planes,
            input_dir, output_dir
        ) for i in range(1, n_fields + 1)
    )
