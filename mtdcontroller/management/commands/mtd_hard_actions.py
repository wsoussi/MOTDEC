import time
import json, yaml
import asyncio
import copy
import requests
import platform    # For getting the operating system name
import subprocess  # For executing a shell command

from datetime import datetime
from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state
from mtdcontroller.katanaclient import katanacli
from django.conf import settings

import osmclient
from osmclient import client as osm_cli
from .monitoring import sync_with_slicem


def ping(host):
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    # Building the command. Ex: "ping -c 1 vnfhost"
    command = ['ping', param, '1', host]
    return subprocess.call(command) == 0


def chrono(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        chrono = "{:.7f}".format(end - start)
        print(chrono, "seconds")
    return wrapper


@chrono
def restart_ns_v1(slicem, nsi, ns):
    # RESTART INSTANCE
    # query katana to get the location of the ns service
    location = VNF.objects.filter(ns_parent= ns)[0].vim.location
    # define API payload
    payload = {"domain": "NFV", "action": "RestartNS", "details": {"ns_id": ns.resource_id_at_slicem, "location": location}}
    # perform restart action
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    print("result of restartNS: " + str(action) + "; timestamp: " +  str(datetime.now(timezone.utc)))
    # sync database
    log_channel = None
    asyncio.run(sync_with_slicem(log_channel, slicem))
    return action


@chrono
def restart_ns_v2(slicem, nsi, ns):
    # START NEW INSTANCE
    # query katana to get the name, nsd_id and the location of the ns service
    name = str(ns.name)
    nsd_id = str(ns.nsd_id)
    old_vnfs = VNF.objects.filter(ns_parent= ns)
    old_public_ip = old_vnfs[0].public_ipv4
    old_private_ip = old_vnfs[0].real_ipv4
    location = old_vnfs[0].vim.location
    old_ns_id = str(ns.resource_id_at_slicem)
    old_ns_id_at_nfvo = str(ns.resource_id_at_nfvo)
    # define API payload
    if location == "inspire5gedge":
        location = "Inspire5GEdge"
    payload = {"domain": "NFV", "action": "AddNS",
               "details": {"nsd_id": nsd_id, "location": location, "ns_name": name}}
    if location == "Inspire5GEdge":
        location = "inspire5gedge"
    # perform addNS POST
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    print("MTD restart action: added new " + name + "NS instance to network slice " + str(nsi.resource_id_at_slicem))
    # update DB instance of the new NS
    # ---  get the new ns_id_at_slicem
    found = False
    while not found:
        time.sleep(2)
        slice_info = asyncio.run(katanacli.slice_inspect(slicem.slicem_ip, nsi.resource_id_at_slicem))
        for new_ns_id_at_slicem, nss_info in slice_info['ns_inst_info'].items():
            for location, ns_info in nss_info.items():
                if ns_info['ns-name'] == name and new_ns_id_at_slicem != old_ns_id and ns_info['status'] == "Started": # ns_info['nfvo_inst_ns'] != old_ns_id_at_nfvo
                    new_ns_id = new_ns_id_at_slicem
                    new_id_at_nfvo = ns_info['nfvo_inst_ns']
                    new_ip = ns_info['vnfr'][0]['mgmt_ip']
                    print("found the new ns with ns_id: " +str(new_ns_id)+ " ; id at nfvo: " + str(new_id_at_nfvo)+ " ; ns_status: " + str(ns_info['status']))
                    found = True
                    break
            else:
                continue  # if the inner loop does not break
            break  # outer loop as well otherwise
    new_ns = copy.deepcopy(ns)
    new_ns.resource_id_at_slicem = new_ns_id
    new_ns.resource_id_at_nfvo = new_id_at_nfvo
    new_ns.primary_ip = new_ip
    new_ns.save()

    # KEEP CHECKING IF THE NEW INSTANCE IS READY (for 2 minutes)
    # get resource usage data from OSM
    user = 'admin'
    password = 'admin'
    project = 'admin'
    kwargs = {}
    if user is not None:
        kwargs['user'] = user
    if password is not None:
        kwargs['password'] = password
    if project is not None:
        kwargs['project'] = project
    nfvo = new_ns.nfvo
    osm_client = osm_cli.Client(host=nfvo.nfvo_ip, sol005=True, **kwargs)

    # we keep checking every 2 seconds if the ns is running for 2 minutes
    counter = 0
    running = False
    while not running:
        try:
            ns_in_nfvo = osm_client.ns.get(new_id_at_nfvo)
        except osmclient.common.exceptions.NotFound:  # NS not in OSM
            ns_in_nfvo = None
        if ns_in_nfvo:
            if ns_in_nfvo['operational-status'] == 'running':
                running = True
            else:
                running = False
        if not running:
            time.sleep(1)
    new_ns.is_running = running
    new_ns.save()

    # Before stopping the old instance check if the new one is pingable
    print("ping checking started at " + str(datetime.now()))
    while not ping(new_ns.primary_ip):
        continue
    print("ping checking ended at " + str(datetime.now()))
    time.sleep(1)
    # ping the Systemic app to see if the app is reachable
    not_running = True
    print("APP REST checking started at " + str(datetime.now()))
    while not_running:
        s = requests.Session()
        url = "http://" + new_ns.primary_ip + ":8080/ingest"
        payload = {}
        headers = {}
        try:
            response = s.request("GET", url, timeout=0.5, headers=headers, data=payload)
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

        if response and response.status_code == 200:
            not_running = False
    print("REST API checking ended at " + str(datetime.now()))

    # UPDATE TOPOFUZZER before deleting the old instance
    print("Start updating TopoFuzzer IP mapping at " + str(datetime.now()))
    # change public IP to private IP map
    payload = json.dumps({'new_ip': new_ns.primary_ip})
    url = "http://" + settings.TOPOFUZZER_IP + ":8000/api/mappings/" + old_public_ip.replace(".", "_")
    headers = {'Content-Type': 'application/json'}
    res = requests.request("PUT", url, headers=headers, data=payload)
    # do the other way around (private IP to public IP)
    # delete old row
    url = "http://" + settings.TOPOFUZZER_IP + ":8000/api/mappings/" + old_private_ip.replace(".", "-")
    res2 = requests.request("DELETE", url, headers=None, data=None)
    # add new row
    payload = json.dumps({new_ns.primary_ip.replace(".", "-"): old_public_ip})
    url = "http://" + settings.TOPOFUZZER_IP + ":8000/api/mappings/"
    headers = {'Content-Type': 'application/json'}
    res3 = requests.request("POST", url, headers=headers, data=payload)
    if "Successfully updated" not in res.text and "Successfully updated" not in res2.text and  "Successfully updated" not in res3.text:
        print("error in updating TopoFuzzer IP mapping")
        exit(1)
    print("updated TopoFuzzer IP mapping at " + str(datetime.now()))
    time.sleep(3)

    # STOP OLD RUNNING NS
    print("MTD restart action: the new ns is running: " + str(running))
    payload = {"domain": "NFV", "action": "StopNS",
               "details": {"ns_id": old_ns_id, "location": location}}
    # run the stop 4 times as one time only stops the instance in OSM but does not delete it
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    time.sleep(0.1)
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    # sync database
    log_channel = None
    asyncio.run(sync_with_slicem(log_channel, slicem))


@chrono
def migrate_ns(slicem, nsi, ns, new_location):
    # START NEW INSTANCE
    # query katana to get the name, nsd_id and the location of the ns service
    name = str(ns.name)
    nsd_id = str(ns.nsd_id)
    old_vnfs = VNF.objects.filter(ns_parent= ns)
    location = old_vnfs[0].vim.location
    old_public_ip = old_vnfs[0].public_ipv4
    old_private_ip = old_vnfs[0].real_ipv4
    old_location = location
    old_ns_id = str(ns.resource_id_at_slicem)
    # define API payload
    if new_location == "inspire5gedge":
        new_location = "Inspire5GEdge"
    payload = {"domain": "NFV", "action": "AddNS",
               "details": {"nsd_id": nsd_id, "location": new_location, "ns_name": name}}
    if new_location == "Inspire5GEdge":
        new_location \
            = "inspire5gedge"
    # perform addNS POST
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    print(str(json.dumps(payload)))
    print("MTD migrate action: added new " + name + "NS instance to network slice " + str(nsi.resource_id_at_slicem) + "in the location at the " + new_location)
    # update DB instance of the new NS
    # ---  get the new ns_id_at_slicem
    found = False
    while not found:
        time.sleep(2)
        slice_info = asyncio.run(katanacli.slice_inspect(slicem.slicem_ip, nsi.resource_id_at_slicem))
        for new_ns_id_at_slicem, nss_info in slice_info['ns_inst_info'].items():
            for location, ns_info in nss_info.items():
                if ns_info['ns-name'] == name and new_ns_id_at_slicem != old_ns_id and ns_info['status'] == "Started": # ns_info['nfvo_inst_ns'] != old_ns_id_at_nfvo
                    new_ns_id = new_ns_id_at_slicem
                    new_id_at_nfvo = ns_info['nfvo_inst_ns']
                    new_ip = ns_info['vnfr'][0]['mgmt_ip']
                    print("found the new ns with ns_id: " +str(new_ns_id)+ " ; id at nfvo: " + str(new_id_at_nfvo)+ " ; ns_status: " + str(ns_info['status']))
                    found = True
                    break
            else:
                continue  # if the inner loop does not break
            break  # outer loop as well otherwise
    new_ns = copy.deepcopy(ns)
    new_ns.resource_id_at_slicem = new_ns_id
    new_ns.resource_id_at_nfvo = new_id_at_nfvo
    new_ns.primary_ip = new_ip
    new_ns.save()

    # KEEP CHECKING IF THE NEW INSTANCE IS READY (for 2 minutes)
    # get resource usage data from OSM
    user = 'admin'
    password = 'admin'
    project = 'admin'
    kwargs = {}
    if user is not None:
        kwargs['user'] = user
    if password is not None:
        kwargs['password'] = password
    if project is not None:
        kwargs['project'] = project
    nfvo = new_ns.nfvo
    osm_client = osm_cli.Client(host=nfvo.nfvo_ip, sol005=True, **kwargs)

    counter = 0
    running = False
    while not running:
        try:
            ns_in_nfvo = osm_client.ns.get(new_id_at_nfvo)
        except osmclient.common.exceptions.NotFound:  # NS not in OSM
            ns_in_nfvo = None
        if ns_in_nfvo:
            if ns_in_nfvo['operational-status'] == 'running':
                running = True
            else:
                running = False
        if not running:
            time.sleep(1)
    new_ns.is_running = running
    new_ns.save()
    print("MTD migrate action: the new ns is running: " + str(running))

    # before stopping the old instance check if the new one is pingable
    print("ping checking started at " + str(datetime.now()))
    while not ping(new_ns.primary_ip):
        continue
    print("ping checking ended at " + str(datetime.now()))
    time.sleep(1)
    # ping the Systemic app to see if the app is reachable
    print("APP REST checking started at " + str(datetime.now()))
    not_running = True
    while not_running:
        s = requests.Session()
        url = "http://" + new_ns.primary_ip + ":8080/ingest"
        payload = {}
        headers = {}
        try:
            response = s.request("GET", url, timeout=0.5, headers=headers, data=payload)
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

        if response and response.status_code == 200:
            not_running = False
    print("REST API checking ended at " + str(datetime.now()))

    # UPDATE TOPOFUZZER before deleting the old instance
    print("Start updating TopoFuzzer IP mapping at " + str(datetime.now()))
    # change public IP to private IP map
    payload = json.dumps({'new_ip': new_ns.primary_ip})
    url = "http://" + settings.TOPOFUZZER_IP + ":8000/api/mappings/" + old_public_ip.replace(".", "_")
    headers = {'Content-Type': 'application/json'}
    res = requests.request("PUT", url, headers=headers, data=payload)
    # do the other way around (private IP to public IP)
    # delete old row
    url = "http://" + settings.TOPOFUZZER_IP + ":8000/api/mappings/" + old_private_ip.replace(".", "-")
    res2 = requests.request("DELETE", url, headers=None, data=None)
    # add new row
    payload = json.dumps({new_ns.primary_ip.replace(".", "-"): old_public_ip})
    url = "http://" + settings.TOPOFUZZER_IP + ":8000/api/mappings/"
    headers = {'Content-Type': 'application/json'}
    res3 = requests.request("POST", url, headers=headers, data=payload)
    if "Successfully updated" not in res.text and "Successfully updated" not in res2.text and "Successfully updated" not in res3.text:
        print("error in updating TopoFuzzer IP mapping")
        exit(1)
    print("updated TopoFuzzer IP mapping at " + str(datetime.now()))
    time.sleep(3)

    # STOP OLD RUNNING NS
    payload = {"domain": "NFV", "action": "StopNS",
               "details": {"ns_id": old_ns_id, "location": old_location}}
    print(str(json.dumps(payload)))
    # run the stop 4 times as one time only stops the instance in OSM but does not delete it
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    time.sleep(0.1)
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    time.sleep(0.1)
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    action = asyncio.run(katanacli.slice_modify(nsi.resource_id_at_slicem, slicem.slicem_ip, payload))
    # sync database
    log_channel = None
    asyncio.run(sync_with_slicem(log_channel, slicem))