import os
import json
import statistics

import matplotlib.pyplot as plt

def plot_results(file):
    elapsed_list = []
    elapsed_migrate_core = []
    elapsed_migrate_edge = []
    elapsed_restart_core = []
    elapsed_restart_edge = []

    with open(file, 'r') as f:
        # get json object from every line
        lines = f.readlines()
        prev_migrate_location = None
        old_time = None
        for line in lines:
            json_obj = json.loads(line)
            minu = float(json_obj['total_elapsed'].split(':')[1])
            sec = float(json_obj['total_elapsed'].split(':')[2])
            tot_min = round(minu + (sec/60), 4)
            # group values in the lists
            if json_obj['mtd_type'] == "migrate":
                # convert in minutes the time elapsed string
                if json_obj['migrate_to'] == "core":
                    elapsed_migrate_core.append(tot_min)
                else:
                    elapsed_migrate_edge.append(tot_min)
                elapsed_list.append(tot_min)
                if prev_migrate_location is None and old_time is not None:
                    if json_obj['migrate_to'] == "core":
                        elapsed_restart_edge.append(old_time)
                    else:
                        elapsed_restart_core.append(old_time)
                prev_migrate_location = json_obj["migrate_to"]
            else:
                if prev_migrate_location == "core":
                    elapsed_restart_core.append(tot_min)
                elif prev_migrate_location == "inspire5gedge":
                    elapsed_restart_edge.append(tot_min)
                else:
                    old_time = tot_min
                elapsed_list.append(tot_min)

    # plot the three lists
    fig, ax = plt.subplots()
    ax.plot(elapsed_list, label='total elapsed')
    ax.plot(elapsed_migrate_core, label='migrate core')
    ax.plot(elapsed_migrate_edge, label='migrate edge')
    ax.set_xlabel("Iterations")
    ax.set_ylabel("Time (minutes)")
    ax.legend()
    # reduce labels in the y axis
    ax.tick_params(axis='y', which='both', labelsize=8)
    # save plot in a pdf file
    plt.savefig(file+'_plot.pdf')
    print("total_mtd_hard", min(elapsed_list), max(elapsed_list), statistics.mean(elapsed_list), statistics.stdev(elapsed_list))
    print("migrate_core", min(elapsed_migrate_core), max(elapsed_migrate_core), statistics.mean(elapsed_migrate_core), statistics.stdev(elapsed_migrate_core))
    print("migrate_edge", min(elapsed_migrate_edge), max(elapsed_migrate_edge), statistics.mean(elapsed_migrate_edge), statistics.stdev(elapsed_migrate_edge))
    print("restart_core", min(elapsed_restart_core), max(elapsed_restart_core), statistics.mean(elapsed_restart_core), statistics.stdev(elapsed_restart_core))
    print("restart_edge", min(elapsed_restart_edge), max(elapsed_restart_edge), statistics.mean(elapsed_restart_edge), statistics.stdev(elapsed_restart_edge))


def parse_file_into_json(file):
    # open file
    with open(file) as f:
        # read file
        data = f.read()
        # for every line  in file
        mtd_action_item = {}
        for line in data.split('\n'):
            if line:
                # if line starts with "called MTD"
                if line.startswith('called MTD '):
                    mtd_action_item = {}
                    if "restart" in line:
                        mtd_action_item['mtd_type'] = "restart"
                    else:
                        mtd_action_item['mtd_type'] = "migrate"
                    # get suffix after ' at ' in the line
                    mtd_action_item['mtd_start'] = line.split(' at ')[1]
                if "the location at the " in line:
                    mtd_action_item['migrate_to'] = line.split('the location at the ')[1]
                if "ping checking started at" in line:
                    mtd_action_item['ping_start'] = line.split(' at ')[1]
                if "ping checking ended at" in line:
                    mtd_action_item['ping_end'] = line.split(' at ')[1]
                if "APP REST checking started at" in line:
                    mtd_action_item['app_check_start'] = line.split(' at ')[1]
                if "REST API checking ended at" in line:
                    mtd_action_item['app_check_end'] = line.split(' at ')[1]
                if "updated TopoFuzzer IP mapping at" in line:
                    mtd_action_item['topo_fuzz_ip_map'] = line.split(' at ')[1]
                if "finished MTD " in line:
                    # get the string between ' at ' and ' time elapsed is '
                    mtd_action_item['total_elapsed'] = line.split(' time elapsed is ')[1]
                    mtd_action_item['mtd_end'] = line.split(' at ')[1].split(' time elapsed is ')[0]
                    # add mtd_action_item to a json file
                    json_file_name = file.split('.')[0]+'.json'
                    with open(json_file_name, 'a') as f:
                        f.write(json.dumps(mtd_action_item) + '\n')
                        f.close()
                        mtd_action_item = {}


if __name__ == '__main__':
    file1 = "mtd_1vnf_1ue.txt"
    file2 = "mtd_1vnf_10ue.txt"
    json1 = "mtd_1vnf_1ue.json"
    json2 = "mtd_1vnf_10ue.json"
    # parse_file_into_json(file2)
    plot_results(json1)