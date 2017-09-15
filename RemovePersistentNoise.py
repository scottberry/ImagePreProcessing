import os
import numpy as np
import tifffile as tiff
from scipy import misc
from random import sample

STACK_dir = os.path.join(
    os.path.expanduser('~'), 'shares', 'pelkmans-sc-storage',
    'FXm', '20170823_Beads_FXm', 'STACKS'
)

n_sites = 160
threshold = 150
well_name = '3A'
fname_stub = '20170823_Kim2_FXm_beads_3A1_w2sdcDAPImRFPxm-filter_s'

selected_sites = sample(range(1, n_sites + 1), 1)

out_name = 'persistent_noise_' + well_name + '.png'
out_path = os.path.join(STACK_dir, out_name)

initial = True
for site in selected_sites:
    beads = tiff.imread(
        os.path.join(
            STACK_dir,
            well_name,
            fname_stub + str(site) + '.stk'
        )
    )
    n_z = beads.shape[2]
    beads_threshold = np.sum(beads3D > threshold, axis=2)
    noise_mask = beads_threshold > (n_z / 3.0)

    if initial:
        cumulative_mask = noise_mask
        initial = False
    else:
        cumulative_mask = cumulative_mask + noise_mask

misc.imsave(name=out_path,arr=cumulative_mask)
