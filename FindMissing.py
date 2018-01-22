import os.path
from shutil import copy

n_sites = 54
wells = ['C10', 'C11', 'D10', 'D11', 'E10', 'E11', 'F10', 'F11']
channels = ['A01Z01C01', 'A02Z01C02', 'A02Z01C03']

fnames = ['20170615-Kim2-NascentRNA-Volume-PCNA_' + well +
          '_T0001F' + str(site).zfill(3) + 'L01' + channel + '.tif'
          for well in wells
          for site in range(1, n_sites + 1)
          for channel in channels]

actual_files = [f for f in os.listdir('.') if os.path.isfile(f)]

#print(actual_files[1])
#print(fnames[1])

setdiff = set(fnames) - set(actual_files)
C01 = [s for s in setdiff if 'A01Z01C01' in s]
C02 = [s for s in setdiff if 'A02Z01C02' in s]
C03 = [s for s in setdiff if 'A02Z01C03' in s]

print(C01)
print(C02)
print(C03)

#for s in C01:
#    copy('20170615-Kim2-NascentRNA-Volume-PCNA_C10_T0001F001L01A01Z01C01.tif', #s)
#
#for s in C02:
#    copy('20170615-Kim2-NascentRNA-Volume-PCNA_C10_T0001F001L01A02Z01C02.tif', #s)
#
#for s in C03:
#    copy('20170615-Kim2-NascentRNA-Volume-PCNA_C10_T0001F001L01A02Z01C03.tif', #s)
#
