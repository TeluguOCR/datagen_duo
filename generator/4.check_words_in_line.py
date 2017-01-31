import os, sys
from collections import Counter
################### Check to see if all the lines have equal words as expected

img_dir = sys.argv[1]
file_list = sorted(os.listdir(img_dir))
csv_file = open(img_dir + 'words_in_line.csv', 'w')
to_delete = {}

for out_fname in file_list:
    if out_fname[-4:] != '.out':
        continue

    for line in open(img_dir + out_fname):
        if line.find("Words_in_Line") == 0:
            line = line.replace("Words_in_Line :", out_fname.replace('.out', ','))
            line = line.replace(" ", "")
            csv_file.write(line)
            line = line.rstrip()
            counts = Counter([int(i) for i in line.split(',')[1:-3]])
            if len(counts) != 1:
                print("NO ", out_fname, dict(counts))
                to_delete[out_fname] = counts
            # else:
            #     print("OK ", out_fname, counts, line.split(','))
            break
    else:
        print("FATAL: No 'Words_in_Line' in ", out_fname)

def do(*args, **kwargs):
    print(*args, **kwargs)
    # os.system(*args, **kwargs)

for fname in to_delete:
    do("rm {}{}*".format(img_dir, fname[:-3]))
    csv_file.write("\n{}: {}".format(fname, to_delete[fname]))

print(to_delete)
csv_file.close()