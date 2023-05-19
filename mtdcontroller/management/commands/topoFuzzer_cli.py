import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()
from mtdcontroller.models import VNF
import requests
import json
import time


def update_mapping(topofuzzer_ip, topofuzzer_port, vnf_record, private_ip):
    # add TopoFuzzer IP mapping
    url = "http://" + topofuzzer_ip + ":" + str(topofuzzer_port) + "/api/mappings/"
    payload = json.dumps({
        vnf_record.replace(".", "-"): private_ip
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    if "successfully set to" not in response.text:
        print("error in updating TopoFuzzer IP mapping")
        print(response.text)
        exit(1)


def get_map(topofuzzer_ip, topofuzzer_port):
    url = "http://" + topofuzzer_ip + ":" + str(topofuzzer_port) + "/api/mappings/"
    payload = ""
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    res = json.loads(response.text)
    return res["items"]


def api_assign_public_ip(topofuzzer_ip, topofuzzer_port):
    url = "http://" + topofuzzer_ip + ":" + str(topofuzzer_port) + "/api/host_alloc/"
    payload = ""
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code != 200:
        print("error: " + str(response))
        exit(1)
    # add mininet ip to MOTDEC DB
    items = get_map(topofuzzer_ip, topofuzzer_port)
    print("items are " + str(items))
    for key, public_ip in items.items():
        if key.count('-') == 3:
            real_ip = key.replace('-', '.')
            # get VNF by real IP
            vnf = VNF.objects.get(real_ipv4= real_ip)
            vnf.public_ipv4 = public_ip
            vnf.save()
            print("vnf " + str(vnf.id) + " has public ip " + str(vnf.public_ipv4))


def topoFuzzer_update(stdout, topofuzzer_ip, topofuzzer_port):
    current_vnfs = {}
    while True:
        # get list of VNFs and check against old VNFs
        new_current_vnfs = VNF.objects.all()
        update = False
        for vnf in new_current_vnfs:
            if vnf.id not in current_vnfs:
                update = True
                current_vnfs[vnf.id] = vnf.real_ipv4
                # send IPs of new VNFs
                update_mapping(topofuzzer_ip, topofuzzer_port, str(vnf.record()), vnf.real_ipv4)
            # check for each existing VNF if the IP is the same as the old one, if not update IP
            elif current_vnfs[vnf.id] != vnf.real_ipv4:
                current_vnfs[vnf.id] = vnf.real_ipv4
                # send IPs
                update_mapping(topofuzzer_ip, topofuzzer_port, str(vnf.record()), vnf.real_ipv4)
        if update:
            api_assign_public_ip(topofuzzer_ip, topofuzzer_port)
        time.sleep(0.1)