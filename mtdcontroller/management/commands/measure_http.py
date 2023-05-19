import json
import requests
from statistics import mean
import time
from colorama import Fore, Style
from datetime import datetime, timedelta
import pytz
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse

cycle_time = 1

glob_latency = []
glob_throughput = []

def request_tcp_loop(vnf_ip):
    global glob_latency, glob_throughput
    s = requests.Session()
    # set interface




    latency_list = []
    throughput_list = []
    # send /ingest requests to metrics server
    p_tot = 0
    p_loss = 0
    start = time.time()
    tot_mean_latency = 0
    max_latency = 0
    p_loss_rate = 0
    while True:
        # group measurements into avg cycles
        end = time.time()
        if (end-start) > cycle_time:
            start = end
            mean_latency = mean(latency_list)
            mean_throughput = mean(throughput_list)
            tot_mean_latency += mean_latency
            latency_color = ""
            ploss_color = ""
            if mean_latency > 0.13 and mean_latency < 0.25:
                latency_color = Fore.YELLOW
            elif mean_latency >= 0.25:
                latency_color = Fore.RED
            if p_loss_rate > 0:
                ploss_color = Fore.RED
            with open('metrics_scenario.json', 'a') as outfile:
                json_obj = { str(datetime.now(pytz.timezone("UTC"))) : [mean_latency, mean_throughput, max_latency, p_loss_rate]}
                json.dump(json_obj, outfile)
                outfile.write('\n')
            print(latency_color + str(datetime.now(pytz.timezone("UTC"))) + "," + str(mean_latency) + Style.RESET_ALL + "," + str(mean(throughput_list)) + "," + str(max_latency) + ","+ ploss_color + str(p_loss_rate) + Style.RESET_ALL)
            latency_list = []
            throughput_list = []
            p_tot = 0
            p_loss = 0
            p_loss_rate = 0
        else:
            url = "http://"+vnf_ip+":8080/ingest"
            payload = {}
            headers = {}
            try:
                response = s.request("GET", url, timeout=0.9, headers=headers, data=payload)
                latency = response.elapsed.total_seconds()
                latency_list.append(latency)
                if p_loss_rate:
                    throughput_list.append((536 / latency) * (1/math.sqrt(p_loss_rate))) # Mathis equation:(MSS in bytes/RTT) * [1/sqrt(p_loss] MSS=Maximum Segment Size= 356 bytes
                else:
                    throughput_list.append(12008 / latency) # 12k8Bytes is the Linux Wmax
                max_latency = max(latency, max_latency)
                p_tot += 1
            except requests.exceptions.HTTPError:
                response = None
            except requests.exceptions.ConnectionError:
                response = None
            except requests.exceptions.Timeout:
                response = None
            except requests.exceptions.RequestException:
                response = None
            except requests.exceptions.ReadTimeout:
                response = None

            if not response or response.status_code != 200:
                # packet loss
                p_tot += 1
                p_loss += 1
                latency = 0.9
                latency_list.append(latency)
                if p_loss:
                    p_loss_rate = (p_loss / max(p_tot, 1))
                if p_loss_rate:
                    throughput_list.append((536 / latency) * (1/math.sqrt(p_loss_rate))) # Mathis equation:(MSS in bytes/RTT) * [1/sqrt(p_loss] MSS=Maximum Segment Size= 356 bytes
                else:
                    throughput_list.append(12008 / latency) # 12k8Bytes is the Linux Wmax
                max_latency = max(latency, max_latency)


def request_udp_loop(vnf_ip):
    global glob_latency, glob_throughput
    s = requests.Session()
    latency_list = []
    throughput_list = []
    # send /ingest requests to metrics server
    p_tot = 0
    p_loss = 0
    start = time.time()
    tot_mean_latency = 0
    max_latency = 0
    p_loss_rate = 0
    while True:
        # group measurements into avg cycles
        end = time.time()
        if (end-start) > cycle_time:
            start = end
            mean_latency = mean(latency_list)
            mean_throughput = mean(throughput_list)
            tot_mean_latency += mean_latency
            latency_color = ""
            ploss_color = ""
            if mean_latency > 0.13 and mean_latency < 0.25:
                latency_color = Fore.YELLOW
            elif mean_latency >= 0.25:
                latency_color = Fore.RED
            if p_loss_rate > 0:
                ploss_color = Fore.RED
            with open('metrics_scenario.json', 'a') as outfile:
                json_obj = { str(datetime.now(pytz.timezone("UTC"))) : [mean_latency, mean_throughput, max_latency, p_loss_rate]}
                json.dump(json_obj, outfile)
                outfile.write('\n')
            print(latency_color + str(datetime.now(pytz.timezone("UTC"))) + "," + str(mean_latency) + Style.RESET_ALL + "," + str(mean(throughput_list)) + "," + str(max_latency) + ","+ ploss_color + str(p_loss_rate) + Style.RESET_ALL)
            latency_list = []
            throughput_list = []
            p_tot = 0
            p_loss = 0
            p_loss_rate = 0
        else:
            url = "http://"+vnf_ip+":8080/ingest"
            payload = {}
            headers = {}
            try:
                response = s.request("GET", url, timeout=0.9, headers=headers, data=payload)
                latency = response.elapsed.total_seconds()
                latency_list.append(latency)
                if p_loss_rate:
                    throughput_list.append((536 / latency) * (1/math.sqrt(p_loss_rate))) # Mathis equation:(MSS in bytes/RTT) * [1/sqrt(p_loss] MSS=Maximum Segment Size= 356 bytes
                else:
                    throughput_list.append(12008 / latency) # 12k8Bytes is the Linux Wmax
                max_latency = max(latency, max_latency)
                p_tot += 1
            except requests.exceptions.HTTPError:
                response = None
            except requests.exceptions.ConnectionError:
                response = None
            except requests.exceptions.Timeout:
                response = None
            except requests.exceptions.RequestException:
                response = None
            except requests.exceptions.ReadTimeout:
                response = None

            if not response or response.status_code != 200:
                # packet loss
                p_tot += 1
                p_loss += 1
                latency = 0.9
                latency_list.append(latency)
                if p_loss:
                    p_loss_rate = (p_loss / max(p_tot, 1))
                if p_loss_rate:
                    throughput_list.append((536 / latency) * (1/math.sqrt(p_loss_rate))) # Mathis equation:(MSS in bytes/RTT) * [1/sqrt(p_loss] MSS=Maximum Segment Size= 356 bytes
                else:
                    throughput_list.append(12008 / latency) # 12k8Bytes is the Linux Wmax
                max_latency = max(latency, max_latency)


def parse_scenario():
    # get scenario data
    alert1_date = datetime.strptime('2022-05-11 06:51:14.307170', '%Y-%m-%d %H:%M:%S.%f')
    alert2_date = datetime.strptime('2022-05-11 06:52:20.580959', '%Y-%m-%d %H:%M:%S.%f')
    alert3_date = datetime.strptime('2022-05-11 06:54:55.548202', '%Y-%m-%d %H:%M:%S.%f')
    alert4_date = datetime.strptime('2022-05-11 06:55:57.764097', '%Y-%m-%d %H:%M:%S.%f')
    mtd_restart_end = datetime.strptime('2022-05-11 06:53:52.710446', '%Y-%m-%d %H:%M:%S.%f')
    mtd_migrate_end = datetime.strptime('2022-05-11 06:57:18.673219', '%Y-%m-%d %H:%M:%S.%f')

    f = open('metrics_scenario.json')
    json_data = json.load(f)
    x_dates = []
    y_latency = []
    y_ploss = []
    avg_normal_latency = 0
    for timestamp, list in json_data.items():
        timestamp2 = timestamp.split('+')[0]
        # timestamp = timestamp.split(' ')[1]
        date_obj = datetime.strptime(timestamp2, '%Y-%m-%d %H:%M:%S.%f') # instead of '%Y-%m-%d %H:%M:%S.%f' to convert to int
        # date_int = date_obj.second * 1 + date_obj.minute * 60 + date_obj.hour * 3600
        x_dates.append(date_obj)
        y_latency.append(list[0])
        y_ploss.append(list[3])

    #PLOT LATENCY
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S.%f'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(5))
    plt.plot(x_dates, y_latency)
    plt.xlabel('time')
    plt.ylabel('Avg. latency / s')
    plt.title('Athens demo measurements')
    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.axvline(x=alert1_date, color='red', label='attack alert', ls='--',)
    plt.axvline(x=alert2_date, color='red', label='attack alert & mtd restart',ls=':', lw=2,)
    plt.axvline(x=mtd_restart_end, color='orange', label='mtd retart end',ls=':', lw=2,)
    plt.axvline(x=alert3_date, color='red', label='attack alert',  ls='--',)
    plt.axvline(x=alert4_date, color='red', label='attack alert & mtd migrate',ls=':', lw=2,)
    plt.axvline(x=mtd_migrate_end, color='orange', label='mtd migrate end',ls=':', lw=2,)
    # place legend outside
    plt.legend(bbox_to_anchor=(1.0, 1), loc='upper left', borderaxespad=0.)
    plt.show()

    #PLOT PACKET LOSS RATE
    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S.%f'))
    # plt.gca().xaxis.set_major_locator(mdates.DayLocator(5))
    # plt.plot(x_dates, y_ploss)
    # plt.xlabel('time')
    # plt.ylabel('Avg. packet loss rate per 5 sec.')
    # plt.title('Athens demo measurements')
    # plt.grid(True)
    # plt.gcf().autofmt_xdate()
    # plt.axvline(x=alert1_date, color='red', label='attack alert', ls='--',)
    # plt.axvline(x=alert2_date, color='red', label='attack alert & mtd restart',ls=':', lw=2,)
    # plt.axvline(x=mtd_restart_end, color='orange', label='mtd retart end',ls=':', lw=2,)
    # plt.axvline(x=alert3_date, color='red', label='attack alert',  ls='--',)
    # plt.axvline(x=alert4_date, color='red', label='attack alert & mtd migrate',ls=':', lw=2,)
    # plt.axvline(x=mtd_migrate_end, color='orange', label='mtd migrate end',ls=':', lw=2,)
    # # place legend outside
    # plt.legend(bbox_to_anchor=(1.0, 1), loc='upper left', borderaxespad=0.)
    # plt.show()



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Measure HTTP traffic.')
    parser.add_argument('--vnf-ip', dest='vnf_ip', type=str,
                        help='VNF IP address', action="store", required=True)
    # add a protocol parameter which can be either "TCP" or ""UDP
    parser.add_argument('--protocol', dest='protocol', type=str,
                        help='Protocol', action="store", default="TCP")
    args = parser.parse_args()
    if args.protocol == "TCP":
        request_tcp_loop(args.vnf_ip)
    elif args.protocol == "UDP":
        request_udp_loop(args.vnf_ip)
    else:
        print("The argument --protocol is either TCP or UDP")
    # parse_scenario()
