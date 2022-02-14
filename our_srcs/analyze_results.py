import sys
import os
from matplotlib import pyplot as plt
import pandas
import re

RESULT_REGEX = "\(\d\d:\d\d:\d\d\) CRITICAL: Result: bytes_sent=(?P<bytes_sent>\d+),total_time=(?P<total_time>[\d]+.?[\d]*) \(params (?P<HB>[a-zA-Z]* [a-zA-Z]*), (?P<N>\d*), (?P<id>\d*), (?P<sz>\d*)\)"

SET_PARAMS = {"N": 8, "id": 6, "sz": 2**16}
PARAMS = ['N', 'id', 'sz']


def get_result_line(line):
    return "CRITICAL" in line


def update_dict_by_param(full_dict, result_dict, param):
    if result_dict['HB'] not in full_dict:
        full_dict[result_dict['HB']] = {}
    full_dict[result_dict['HB']][result_dict[param]] = result_dict['total_time']

def get_lines(log_file):
    all_lines = []
    if os.path.isfile(log_file):
        with open(log_file, 'r') as f:
            all_lines += f.readlines()
    elif os.path.isdir(log_file):
        log_files = os.listdir(log_file)
        for file_name in log_files:
            cur_full_file = '\\'.join([log_file, file_name])
            if os.path.isfile(cur_full_file):
                with open(cur_full_file, 'r') as f:
                    all_lines += f.readlines()
    else:
        assert False, f"what is {log_file}??"
    return all_lines

def extract_data(log_file):
    data_by_nodes = {}
    data_by_id = {}
    data_by_size = {}
    dicts_by_param = {'N': data_by_nodes, 'id': data_by_id, 'sz': data_by_size}

    all_lines = get_lines(log_file)

    for l in all_lines:
        regex_match = re.match(RESULT_REGEX, l)
        if regex_match is None:
            continue
        rd = regex_match.groupdict()
        for k in rd.keys():
            if k != 'HB':
                rd[k] = float(rd[k])

        for p in PARAMS:
            should_add_point = True
            # If all other params except this one are at the default state, add the point
            for q in PARAMS:
                if p != q and rd[q] != SET_PARAMS[q]:
                    should_add_point = False
                    print(f"{p}:{rd[p]}, {q}:{rd[q]}")
                    break

            if should_add_point:
                update_dict_by_param(dicts_by_param[p], rd, p)
    print(dicts_by_param)
    return dicts_by_param


def analyze_data(pds):
    ax = {}
    fig, (ax['N'], ax['id'], ax['sz']) = plt.subplots(1, 3, sharey=True)
    for p in pds.keys():
        for hb in pds[p]:
            print(f"Plotting by honeybadger {hb}")
            ax[p].plot(pds[p][hb].keys(), pds[p][hb].values())
        ax[p].set_title(p)
        ax[p].legend(pds[p].keys())
    ax['sz'].set_xscale('log')
    plt.show()


def main():
    assert len(sys.argv) == 2, "Give log file parameter please"
    pbs = extract_data(sys.argv[1])
    analyze_data(pbs)


main()


