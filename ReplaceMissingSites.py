import os
import re
import csv

# PARAMETERS
# ----------

base_dir = '~/pelkmanslab-share1/Data/Users/Scott/20171201-Kim2-MicropatternFISH/TIFF/Y_custom'
vol_dir = os.path.join(os.path.expanduser(base_dir),'VOL')
fname_stub = '20171130-kim2-cytoo-scaling-FISH-customY_'

empty_file_dir = os.path.expanduser('~/pelkmanslab-share1/Data/Users/Scott/20171201-Kim2-MicropatternFISH/TIFF/')
empty_C04 = os.path.join(empty_file_dir,'empty_C04.tif')
empty_C05 = os.path.join(empty_file_dir,'empty_C05.tif')
empty_C06 = os.path.join(empty_file_dir,'empty_C06.tif')

rows = ['B','C','D','E','F','G']
cols = range(7,12)
sites = range(1,121)
channels = [4,5,6]

# CODE
# ----

regex = re.compile(r'[^_]+_(?P<w>[A-Z]\d{2})_T(?P<t>\d+)F(?P<s>\d+)L\d+A\d+Z(?P<z>\d+)C0(?P<c>\d)\.')

wells = [row + str(col).zfill(2) for row in rows for col in cols]

file_list = [fname_stub + well + '_T0001F' + str(site).zfill(3) + 'L01A02Z01C' + str(channel).zfill(2) + '.tif' for well in wells for site in sites for channel in channels]

non_extant = []
for file in file_list:
    path = os.path.join(os.path.expanduser(vol_dir), file)
    if not os.path.isfile(path):
        non_extant.append(file)


# save a list of sites that are missing
out_file_path = os.path.join(os.path.expanduser(base_dir), fname_stub + 'missing_files.csv')
with open(out_file_path, 'ab') as out_file:
    wr = csv.writer(out_file, quoting=csv.QUOTE_ALL)
    wr.writerow(['replaced_image', 'replacement_source'])
    for file in non_extant:
        captures = regex.search(file).groupdict()
        if captures.get('c') == str(4):
            wr.writerow([file, empty_C04])
        if captures.get('c') == str(5):
            wr.writerow([file, empty_C05])
        if captures.get('c') == str(6):
            wr.writerow([file, empty_C06])

# make hard links to a default empty image for these sites
for file in non_extant:
    path = os.path.join(os.path.expanduser(vol_dir), file)
    # extract well and site
    captures = regex.search(file).groupdict()
    print 'replacing missing well', captures.get('w'), 'site', captures.get('s'), 'channel', captures.get('c')
    if captures.get('c') == str(4):
        os.link(empty_C04, path)
    elif captures.get('c') == str(5):
        os.link(empty_C05, path)
    elif captures.get('c') == str(6):
        os.link(empty_C06, path)

