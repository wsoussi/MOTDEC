import datetime
import os, re
from django.core.management.base import BaseCommand, CommandError
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()
from django.utils import timezone
from mtdcontroller.models import VDU, VDU_state, Attack_surface
from datetime import timedelta
from asgiref.sync import sync_to_async
import time
import requests
import numpy as np
import json
from json.decoder import JSONDecodeError
from mtdcontroller.cvss_calculator import cvss_calc
import asyncio

from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.protocols.gmpv214 import AliveTest
import xmltodict

# openVAS credentials
username = 'admin'
password = 'admin'

# vulnerability type enumerated based on cvedetails.com strings
exec_code   = 'ec'
sql_inj     = 'sql'
xss         = 'xss'
dir_traveral= 'dirt'
gain_privilg= 'priv'
gain_info   = 'info'
overflow    = 'overflow'
denial_of_service   = 'dos'
local_file_inclusion= 'fileinc'

VULN_TYPE = {'recon': [], 'apt': [exec_code], 'data_leak': [sql_inj, xss, dir_traveral, gain_info, gain_privilg, local_file_inclusion], 'DoS': [denial_of_service, overflow] }

vuln_scan_frequancy_hours = 24 # we scan the network once a day

iana_tcp_ports_id = '33d0cd82-57c6-11e1-8ed1-406186ea4fc5'  # this is to be used for the parameter port_list_id
full_and_fast = 'daba56c8-73ec-11df-a475-002264764cea' # this is the id of the scan config "Full and fast"
openvas_scanner = '08b69003-5fc2-4037-a479-93b440211c73' # this is the id of the scanner "OpenVAS"


# Define DJANGO calls that should be done in a syncrous way
@sync_to_async
def get_vdus():
    try:
        vdus = VDU.objects.all()
    except VDU.DoesNotExist:
        vdus = []
    return list(vdus)


@sync_to_async
def get_last_vdu_state(vdu):
    try:
        vdu_last_state = VDU_state.objects.filter(resource_record=vdu.record()).latest('timestamp')
    except VDU_state.DoesNotExist:
        vdu_last_state = None
    return vdu_last_state


@sync_to_async
def get_last_24_hour_scan(vdu_last_state, now):
    one_day_before = now - timedelta(hours=24)
    try:
        res = Attack_surface.objects.filter(vdu_state= vdu_last_state, timestamp__range=(one_day_before, now))
    except Attack_surface.DoesNotExist:
        res = None
    return list(res)


@sync_to_async
def save_attack_surface(vdu_last_state, now, scan_id, number_vuln_ports, attack_type_metrics):
    attack_surface = Attack_surface(vdu_state=vdu_last_state, timestamp=now, scan_result_id=scan_id, nb_vulnerable_ports=number_vuln_ports, cvss_metrics=json.dumps(attack_type_metrics))
    attack_surface.save()


def connect_to_openvas(stdout):
    connection = TLSConnection(timeout=60, hostname='localhost', port=9390, password=None)
    with Gmp(connection=connection) as gmp:
        response = gmp.get_version()
        if str(response).find('status="200" status_text="OK"') != -1:  # if the connection is successful
            response = gmp.authenticate(username, password)
            if str(response).find('status="200" status_text="OK"') == -1:  # if the connection is not successful
                stdout.error("Connection to OpenVAS was not successful")
                print("Connection to OpenVAS was not successful")
                return None
            else:
                return gmp


def cve_groups(stdout, cve_id):
    with open('cve_types.json', 'r+') as cve_types_file:
        try:
            cve_types = json.load(cve_types_file)
        except JSONDecodeError:
            cve_types = {}
        if cve_id not in cve_types:
            # get category from cvedetails.com
            response = requests.get('https://www.cvedetails.com/cve-details.php?t=1&cve_id=' + cve_id)
            vuln_types = []
            for vuln_type in re.findall('<span class="vt_(.*?)">', str(response.content)):
                vuln_types.append(vuln_type)
            cve_types[cve_id] = vuln_types
            cve_types_file.seek(0)
            json.dump(cve_types, cve_types_file)
    cve_types = cve_types[cve_id]
    # get MOTDEC attack classification from vulnerability type
    attack_group = set()
    for cve_type in cve_types:
        if cve_type in VULN_TYPE['apt']:
            attack_group.add('apt')
        elif cve_type in VULN_TYPE['data_leak']:
            attack_group.add('data_leak')
        elif cve_type in VULN_TYPE['DoS']:
            attack_group.add('DoS')
    return attack_group


@sync_to_async
def start_scan(stdout, gmp, resource):
    response = gmp.authenticate(username, password)
    if str(response).find('status="200" status_text="OK"') == -1:  # if the connection is not successful
        gmp = connect_to_openvas(stdout)
        if not gmp:  # authentication failed
            stdout.error("Authentication to OpenVAS failed")
            print("Authentication to OpenVAS failed")
            return -1
    # tasks = gmp.get_tasks()  # get all openvas tasks
    # tasks = xmltodict.parse(tasks)  # convert xml to dict
    # tasks['get_tasks_response']['task'][0]['name']  # example of getting the first task's name
    # target = gmp.create_target('edge_vim', hosts=['10.161.0.101'],
    #                            alive_test=AliveTest('ICMP Ping'),
    #                            port_list_id='33d0cd82-57c6-11e1-8ed1-406186ea4fc5')

    target_id = resource.openvas_target_id
    if target_id:
        target_in_openvas = gmp.get_target(target_id=target_id)
    else:
        target_in_openvas = None
    # if there is no target or if it is not in OpenVAS then create it
    if not target_id or str(target_in_openvas).find('status_text="Failed to find target') != -1:
        # The resource name is not unique based on OSM conventions
        # We add to the OSM name the MOTDEC resource ID. If MOTDEC performs MTD the obj in MOTDEC is the same
        target = gmp.create_target(resource.name+ '_resource-' +str(resource.id), hosts=[resource.real_ipv4],
                                   alive_test=AliveTest('ICMP Ping'),
                                   port_list_id=iana_tcp_ports_id)
        if str(target).find('status_text="OK, resource created') != -1:
            target_id = re.search('OK, resource created" id="(.*)"/>',str(target)).group(1)
            resource.openvas_target_id = target_id
            resource.save()
        # if the target already exists get it
        elif str(target).find('status_text="Target exists already"') != -1:
            targets = gmp.get_targets()
            targets = xmltodict.parse(targets)
            for t in targets["get_targets_response"]["target"]:
                if t["name"] == resource.name + '_resource-' + str(resource.id):
                    target_id = t["@id"]
                    resource.openvas_target_id = target_id
                    resource.save()
                    target = gmp.get_target(t["@id"])
                    if not str(target).find('"200" status_text="OK') != -1:
                        stdout.error(
                            "Found existing OpenVAS target but couldn't get it for the resource " + resource.name + '_resource-' + str(
                                resource.id))
                        print("Found create OpenVAS target but couldn't get it target for the resource " + resource.name + '_resource-' + str(
                            resource.id))
                        return -1
        else:
            stdout.error("Couldn't create OpenVAS target for the resource " + resource.name+ '_resource-' +str(resource.id))
            print("Couldn't create OpenVAS target for the resource " + resource.name+ '_resource-' +str(resource.id))
            return -1
    # check that the ip address is the same as in the resource, if not update OpenVAS target
    target = gmp.get_target(target_id)
    target = xmltodict.parse(target)
    if not target['get_targets_response']['target']['hosts'] == resource.real_ipv4:
        res = gmp.modify_target(target_id, hosts=[resource.real_ipv4])
        if str(res).find("Target is in use") != -1:
            # delete tasks with old ip to be able to modify the target
            tasks = gmp.get_tasks()
            tasks = xmltodict.parse(tasks)
            for t in tasks['get_tasks_response']['task']:
                if t['name'] == target['get_targets_response']['target']['name']:
                    task = t
                    break
            res = gmp.delete_task(task['@id'])
            if not str(res).find('"200" status_text="OK"') != -1:
                stdout.error("error in deleting tasks of resource " + resource.name + " in order to change its IP")
                print("error in deleting tasks of resource " + resource.name + " in order to change its IP")
                return -1
        res = ""
        res = gmp.modify_target(target_id, hosts=[resource.real_ipv4])
        if not str(res).find('"200" status_text="OK"') != -1:
            stdout.error("error in updating the IP of resource " + resource.name)
            print("error in updating the IP of resource " + resource.name)

    # Look for its scan task, if there is no task create it
    scan_task_id = resource.openvas_task_id
    if scan_task_id:
        task_in_openvas = gmp.get_task(task_id=scan_task_id)
    else:
        task_in_openvas = None
    if not scan_task_id or str(task_in_openvas).find('status_text="Failed to find task') != -1:
        # create the task
        scan_task = gmp.create_task(resource.name+ '_resource-' +str(resource.id), config_id=full_and_fast, target_id=target_id,
                                    scanner_id= openvas_scanner)
        if scan_task.find('status_text="OK, resource created') != -1:
            scan_task_id = re.search('OK, resource created" id="(.*)"/>',str(scan_task)).group(1)
            resource.openvas_task_id = scan_task_id
            resource.save()
        else:
            stdout.error("Couldn't create OpenVAS task to scan the target " + resource.name+ '_resource-' +str(resource.id))
            print("Couldn't create OpenVAS task to scan the target " + resource.name+ '_resource-' +str(resource.id))
            return -1

    # Start scanning
    started_task = gmp.start_task(scan_task_id)
    if started_task.find('status_text="OK, request submitted"') != -1:
        new_scan_id = re.search('<report_id>(.*)</report_id></start_task_response>', str(started_task)).group(1)
        return new_scan_id
    else:
        stdout.error("Couldn't start scanner in OpenVAS for the target " + resource.name)
        print("Couldn't start scanner in OpenVAS for the target " + resource.name)
        return -1


def is_scan_finished(stdout, gmp, scan_id):
    # authenticate to gmp
    response = gmp.authenticate(username, password)
    if str(response).find('status="200" status_text="OK"') == -1:  # if the connection is not successful
        gmp = connect_to_openvas(stdout)
    if not gmp:  # authentication failed
        stdout.error("Authentication to OpenVAS failed")
        return -1

    scan = gmp.get_report(scan_id)
    if str(scan).find('status="200" status_text="OK"') != -1:
        scan = xmltodict.parse(scan)
        status = scan['get_reports_response']['report']['report']['scan_run_status']
        if status == 'Running' or status == 'Requested' or status == 'Queued':
            return False
        elif status == 'Done':
            return True
        else:
            stdout.error("Scan "+ scan_id +" Couldn't complete. Status is: " + str(status))
            return -1
    else:
        stdout.error("Couldn't find the scan with id " + scan_id)
        return -1

async def finalize_attack_surface(stdout, vdu_last_state, gmp, scan_id):
    # authenticate to gmp
    response = gmp.authenticate(username, password)
    if str(response).find('status="200" status_text="OK"') == -1:  # if the connection is not successful
        stdout.error("Couldn't authenticate to OpenVAS")
        return -1
    if not gmp:  # authentication failed
        stdout.error("Authentication to OpenVAS failed")
        return -1

    # get report from scan id
    scan = gmp.get_report(scan_id, ignore_pagination=True)
    if str(scan).find('status="200" status_text="OK"') != -1:
        scan = xmltodict.parse(scan)
    else:
        stdout.error("Couldn't find the report with id " + scan_id)
        return -1
    # get CVEs
    if 'result' in scan['get_reports_response']['report']['report']['results']:
        results_list = scan['get_reports_response']['report']['report']['results']['result']
    else:
        results_list = []

    cves_list = []
    for res in results_list:
        if res['threat'] != 'Log' and float(res['severity']) != 0:
            cves_list.append(res)
    valid_cves_list = []
    for cve in cves_list:
        has_cve = False
        for ref in cve['nvt']['refs']['ref']:
            if ref['@type'] == 'cve':
                cve['cve_id'] = ref['@id']
                # get CVSS from CVEs
                cve_details = gmp.get_cve(cve['cve_id'])
                # if CVE details not in OpenVAS delete from cves_list
                if cve_details:
                    has_cve = True
                    cve_details = xmltodict.parse(cve_details)
                    cve['cvss_vector'] = cve_details['get_info_response']['info'][0]['cve']['cvss_vector']
                    if cve['cvss_vector']:
                        valid_cves_list.append(cve)
                    break


    # group CVEs CVSS scores by attack type and get set of vulnerable ports
    attack_type_metrics = {'vuln_ports': {}, 'apt': {'cvss_base': [0], 'cvss_exploitability': [0]}, 'data_leak': {'cvss_base': [0], 'cvss_exploitability': [0]}, 'DoS': {'cvss_base': [0], 'cvss_exploitability': [0]}, 'undefined': {'cvss_base': [0], 'cvss_exploitability': [0]}}
    for cve in valid_cves_list:
        # group cve by port
        if cve['port'] not in attack_type_metrics['vuln_ports']:
            attack_type_metrics['vuln_ports'][cve['port']] = 1
        else:
            attack_type_metrics['vuln_ports'][cve['port']] += 1
        # find attack_type from cvedetails.com
        cve['attack_types'] = cve_groups(stdout, cve['cve_id'])
        if not cve['attack_types']:
            cve['attack_types'] = {'undefined'}
        if 'CVSS:3' in cve['cvss_vector']:
            cvss_base =cve['severity']
            cvss_exploitability = cvss_calc.exploitability_score(cve['cvss_vector'])
        else: # if CVSS is v2 convert the CVSS vector and compute a v3 base score
            cvss_base, cvss_exploitability = cvss_calc.scores(cve['cvss_vector'])
        # group CVSS scores
        for attack_type in cve['attack_types']:
            attack_type_metrics[attack_type]['cvss_base'].append(float(cvss_base))
            attack_type_metrics[attack_type]['cvss_exploitability'].append(float(cvss_exploitability))
    # compute attack surface metrics
    for attack_type, dict in attack_type_metrics.items():
        if attack_type != 'vuln_ports':
            if len(dict['cvss_base']) > 1:
                dict['cvss_base'].pop(0)
                attack_type_metrics[attack_type]['std_dev_base'] = np.std(dict['cvss_base'])
                attack_type_metrics[attack_type]['min_base'] = min(dict['cvss_base'])
                attack_type_metrics[attack_type]['max_base'] = max(dict['cvss_base'])
                attack_type_metrics[attack_type]['avg_base'] = sum(dict['cvss_base'])/max(len(dict['cvss_base']) - 1, 1)
            else:
                dict['cvss_base'].pop(0)
                attack_type_metrics[attack_type]['std_dev_base'] = 0
                attack_type_metrics[attack_type]['min_base'] = 0
                attack_type_metrics[attack_type]['max_base'] = 0
                attack_type_metrics[attack_type]['avg_base'] = 0

            if len(dict['cvss_exploitability']) > 1:
                dict['cvss_exploitability'].pop(0)
                attack_type_metrics[attack_type]['std_dev_exploitability'] = np.std(dict['cvss_exploitability'])
                attack_type_metrics[attack_type]['min_exploitability'] = min(dict['cvss_exploitability'])
                attack_type_metrics[attack_type]['max_exploitability'] = max(dict['cvss_exploitability'])
                attack_type_metrics[attack_type]['avg_exploitability'] = sum(dict['cvss_exploitability'])/len(dict['cvss_exploitability'])
            else:
                dict['cvss_exploitability'].pop(0)
                attack_type_metrics[attack_type]['std_dev_exploitability'] = 0
                attack_type_metrics[attack_type]['min_exploitability'] = 0
                attack_type_metrics[attack_type]['max_exploitability'] = 0
                attack_type_metrics[attack_type]['avg_exploitability'] = 0
    # Save it in MOTDEC
    now = timezone.now()
    await save_attack_surface(vdu_last_state, now, scan_id, len(attack_type_metrics['vuln_ports']), json.dumps(attack_type_metrics))


async def vuln_monitoring_cycle(stdout):
    # for each VDU check if the attack surface model is updated, i.e.:
    #   1- if the VDU is old check that the last scan is older than 1 day
    #   2- if the VDU is new or reinstantiated redo the scan

    # connect to openvas
    gmp = connect_to_openvas(stdout)
    # authenticate to gmp
    response = gmp.authenticate(username, password)
    if str(response).find('status="200" status_text="OK"') == -1:  # if the connection is not successful
        stdout.error("Couldn't authenticate to OpenVAS")
        return -1
    if not gmp:  # authentication failed
        stdout.error("Authentication to OpenVAS failed")
        return -1

    # scan all vdus
    vdus = await get_vdus()
    running_scans_ids_list = []
    for vdu in vdus:
        # get last state of the vdu
        vdu_last_state = await get_last_vdu_state(vdu)
        # check the first state of the resource is created
        if vdu_last_state:
            now = timezone.now()
            vdu_last_attack_surface = await get_last_24_hour_scan(vdu_last_state, now)
            # there is no scan report or it is older than 24h -> start new scan
            if not vdu_last_attack_surface:
                scan_id = await start_scan(stdout, gmp, vdu)
                if scan_id == -1:
                    raise ValueError
                running_scans_ids_list.append( (vdu_last_state, scan_id) )

    attack_surf_reports = []
    while running_scans_ids_list: # while there are still some scans running
        for scan_task in running_scans_ids_list:
            vdu_last_state = scan_task[0]
            running_scan_id = scan_task[1]
            scan_finished = is_scan_finished(stdout, gmp, running_scan_id)
            if scan_finished:
                # attack_surf_reports.append(asyncio.create_task(finalize_attack_surface(stdout, vdu_last_state, gmp, running_scan_id)))
                await finalize_attack_surface(stdout, vdu_last_state, gmp, running_scan_id)
                running_scans_ids_list.remove(scan_task)
            elif scan_finished == -1:
                stdout.error("Failed to verify if the scan ended or not")
                raise ValueError
        await asyncio.sleep(30)  # sleep for 30 seconds between checks
    # attack_surf_reports = await asyncio.gather(*attack_surf_reports, return_exceptions=True)
    print(attack_surf_reports)


def start_vuln_monitoring(stdout, monitoring_frequency):
    # first, wait the time for MOTDEC to update the resource instances
    time.sleep(monitoring_frequency)
    while True:
        s = time.perf_counter()
        asyncio.run(vuln_monitoring_cycle(stdout))
        elapsed = time.perf_counter() - s
        time.sleep(vuln_scan_frequancy_hours * 3600) # an hour has 60*60=3600 seconds


class Command(BaseCommand):
    def handle(self, *args, **kwargsoptions):
        start_vuln_monitoring("", monitoring_frequency=10)