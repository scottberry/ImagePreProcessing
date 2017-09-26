import os
import logging
import sys
import cv2
import numpy as np
import tifffile as tiff
import pandas as pd
from jtmodules import smooth, threshold_manual, fill, filter, label, register_objects, segment_secondary, generate_volume_image, measure_volume_image
from random import sample

## TODO Illumination Correction
## Check prepare_batch_measure_illcor_stats
## and batch_measure_illcor_stats (in iBRAIN)

log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(filename)s %(funcName)s %(levelname)s: %(message)s',
    level=logging.DEBUG, datefmt='%I:%M:%S',stream=sys.stdout)

# Define segmentation modules
def _segmentPrimary(dapi):
    dapiSmooth = smooth.main(dapi, 'gaussian', 5)
    nucleiMask = threshold_manual.main(
        image=dapiSmooth.smoothed_image,
        threshold=150,
        plot=False
    )
    nucleiFilledMask = fill.main(nucleiMask.mask)
    nucleiFilledMaskFiltered = filter.main(
        mask=nucleiFilledMask.filled_mask,
        feature='area',
        lower_threshold=1400,
        upper_threshold=None,
        plot=False
    )
    nuclei = label.main(mask=nucleiFilledMaskFiltered.filtered_mask)
    nucleiReg = register_objects.main(nuclei.label_image)
    return nucleiReg


def _segmentSecondary(nuclei, celltrace):
    celltraceSmooth = smooth.main(celltrace, 'bilateral', 7)
    cells = segment_secondary.main(
        nuclei.objects,
        celltraceSmooth.smoothed_image,
        contrast_threshold=5,
        min_threshold=130,
        max_threshold=150
    )
    return cells


if __name__ == "__main__":

    base_dir = os.path.join(
        os.path.expanduser('~'), 'pelkmans-sc-storage',
        'FXm', '20170823_Beads_FXm'
    )

    log.debug('base_dir: %s', base_dir)
    STACK_dir = os.path.join(base_dir, 'STACKS')
    VOLUME_IMAGE_dir = os.path.join(base_dir, 'VOLUME_IMAGE')
    MIP_dir = os.path.join(base_dir, 'MIP')
    SEGMENTATION_dir = os.path.join(base_dir, 'SEGMENTATION')

    n_sites = 120
    well_name = '4B'
    fname_stub = '20170823_Kim2_FXm_beads_4B2_w2'
    input_channel = 'sdcDAPImRFPxm-filter_s'

    noisy_pixels_path = os.path.join(
        STACK_dir,
        'persistent_noise_' + well_name + '_50.png'
    )

    #selected_sites = sample(range(1, n_sites + 1), 2)
    #selected_sites = [60]
    selected_sites = range(1,n_sites + 1)

    for site in selected_sites:
        MIP_stub = ('20170823_Kim2_FXm_beads_' + str(well_name) +
                    '_A01_T0001F' + str(site).zfill(3) + 'L01A01Z01')

        dapi_name = MIP_stub + 'C01.png'
        se_name = MIP_stub + 'C03.png'
        vol_name = MIP_stub + 'C04.tif'
        nuclei_name = MIP_stub + '_nuclei.png'
        cells_name = MIP_stub + '_cells.png'

        dapi_path = os.path.join(MIP_dir, well_name, dapi_name)
        se_path = os.path.join(MIP_dir, well_name, se_name)
        vol_path = os.path.join(VOLUME_IMAGE_dir, well_name, vol_name)
        nuclei_path = os.path.join(SEGMENTATION_dir, well_name, nuclei_name)
        cells_path = os.path.join(SEGMENTATION_dir, well_name, cells_name)

        vol0_25_meas_name = MIP_stub + '_meas_0_25um.csv'
        vol0_47_meas_name = MIP_stub + '_meas_0_47um.csv'

        vol0_25_meas_path = os.path.join(
            VOLUME_IMAGE_dir, well_name, vol0_25_meas_name
        )
        vol0_47_meas_path = os.path.join(
            VOLUME_IMAGE_dir, well_name, vol0_47_meas_name
        )

        if os.path.isfile(dapi_path):
            log.debug('loading DAPI: %s', dapi_path)
            dapi2D = cv2.imread(dapi_path, -1)
        else:
            log.error('%s does not exist', dapi_path)
            sys.exit(1)

        if os.path.isfile(se_path):
            log.debug('loading SE: %s', se_path)
            se2D = cv2.imread(se_path, -1)
        else:
            log.error('%s does not exist', se_path)
            sys.exit(1)

        log.debug('segmenting cells')
        nuclei = _segmentPrimary(dapi2D)
        cells = _segmentSecondary(nuclei, se2D)

        cv2.imwrite(
            filename=nuclei_path,
            img=nuclei.objects.astype(np.uint16)
        )
        cv2.imwrite(
            filename=cells_path,
            img=cells.secondary_label_image.astype(np.uint16)
        )

        beads_path = os.path.join(
            STACK_dir, well_name,
            fname_stub + input_channel + str(site) + '.stk'
        )
        beads = tiff.imread(beads_path)

        # convert beads to conventional x,y,z ordering and make contiguous
        beads3D = np.swapaxes(beads, 0, 1)
        beads3D = np.ascontiguousarray(np.swapaxes(beads3D, 1, 2))

        if os.path.isfile(noisy_pixels_path):
            log.debug('loading noisy pixels: %s', noisy_pixels_path)
            noisy_pixels = cv2.imread(noisy_pixels_path, -1)
        else:
            log.error('%s does not exist', noisy_pixels_path)
            sys.exit(1)

        log.debug('filtering noisy pixels')
        beads3D[noisy_pixels > 30] = 110

        log.debug('computing volume image')
        gvi = generate_volume_image.main(
            image=beads3D[:,:,0:45],
            mask=cells.secondary_label_image,
            threshold=25,
            mean_size=6,
            min_size=9,
            filter_type='log_2d',
            minimum_bead_intensity=150,
            z_step=0.250,
            pixel_size=0.1625,
            alpha=140,
            plot=False
        )

        log.debug('writing volume image: %s', vol_path)
        tiff.imsave(file=vol_path, data=gvi.volume_image.astype(np.uint16))

        log.debug('measuring volume image with step-size 0.25: %s', vol0_25_meas_path)
        mvi = measure_volume_image.main(
            extract_objects=cells.secondary_label_image.astype(np.uint16),
            assign_objects=cells.secondary_label_image.astype(np.uint16),
            intensity_image=gvi.volume_image.astype(np.uint16),
            pixel_size=0.1625,
            z_step=0.25,
            surface_area=False,
            plot=False)
        mvi.measurements[0].to_csv(vol0_25_meas_path)

        log.debug('measuring volume image with step-size 0.47: %s', vol0_47_meas_path)
        mvi = measure_volume_image.main(
            extract_objects=cells.secondary_label_image.astype(np.uint16),
            assign_objects=cells.secondary_label_image.astype(np.uint16),
            intensity_image=gvi.volume_image.astype(np.uint16),
            pixel_size=0.1625,
            z_step=0.47,
            surface_area=False,
            plot=False)
        mvi.measurements[0].to_csv(vol0_47_meas_path)

