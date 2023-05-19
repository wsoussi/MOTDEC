from django.core.management.base import BaseCommand
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()

import time
import json
from datetime import datetime, timedelta
from django.utils import timezone

from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state, Attack_alert
import mtdcontroller.management.commands.motdec_test_utils as motdec_test_utils
from mtdcontroller.systemiclient import systemicli
from .mtd_hard_actions import restart_ns_v1, restart_ns_v2, migrate_ns
from flask import Flask, json
from colorama import Fore, Style


time_laps = 15


# enforce MTD restart after 2 alerts and migrate after 4
def trigger_MTD_1():
    alert_list = []
    # loop until you find the attack alert
    count = 0
    while len(alert_list) < 2:
        if count % 5 == 0:
            print(Fore.GREEN + "No attacks detected" + Style.RESET_ALL)
        # check if you received 2 alerts
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(seconds=time_laps)
            attack_alerts = Attack_alert.objects.filter(created_at__gte=(time_threshold))
            for alert in attack_alerts:
                if alert not in alert_list:
                    alert_list.append(alert)
                    print(Fore.RED + "Attack alert received: " + str(attack_alerts) + Style.RESET_ALL)
        except Attack_alert.DoesNotExist:
            attack_alerts = None
        time.sleep(2)
        count += 1
    # perform MTD restart action
    nsi = NSi.objects.all()[0]
    slicem = SliceM.objects.all()[0]
    ns = nsi.nss_list.get(name="ns_with_systemic")
    restart_ns_v2(slicem, nsi, ns)
    print(Fore.GREEN + "MOTDEC triggered: True, mtd action: hard_reinstantiate ; timestamp: " + str(datetime.now(timezone.utc)) + Style.RESET_ALL)
    alert_list = []
    count = 0
    # loop until you find the attack alert
    while len(alert_list) < 2:
        if count % 5 == 0:
            print(Fore.GREEN + "No attacks detected" + Style.RESET_ALL)
        # check if you received 2 alerts
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(seconds=time_laps)
            attack_alerts = Attack_alert.objects.filter(created_at__gte=(time_threshold))
            for alert in attack_alerts:
                if alert not in alert_list:
                    alert_list.append(alert)
                    print(Fore.RED + "Attack alert received: " + str(attack_alerts) + Style.RESET_ALL)
        except Attack_alert.DoesNotExist:
            attack_alerts = None
        time.sleep(2)
        count += 1
    # perform MTD migration action
    nsi = NSi.objects.all()[0]
    slicem = SliceM.objects.all()[0]
    ns = nsi.nss_list.get(name= "ns_with_systemic")
    location = VNF.objects.filter(ns_parent= ns)[0].vim.location
    locations = []
    vims = VIM.objects.all()
    for vim in vims:
        locations.append(vim.location)
    locations.remove(location)
    if locations:
        res = migrate_ns(slicem, nsi, ns, locations[0])
        print(Fore.GREEN + "MOTDEC triggered: True, mtd action: hard_migrate ; timestamp: " +  str(datetime.now(timezone.utc)) + Style.RESET_ALL)
    else:
        print(json.dumps({"error": 401, "detail": "migration impossible: there is only one location available"}))

def tmp():
    nsi = NSi.objects.all()[0]
    slicem = SliceM.objects.all()[0]
    count = 2
    while count > 0:
        count -= 1
        start = datetime.now()
        print("called MTD restart at " + str(start))
        ns = nsi.nss_list.get(name="ns_with_systemic")
        restart_ns_v2(slicem, nsi, ns)
        end = datetime.now()
        elapsed = end - start
        print("finished MTD restart at " + str(end) + " time elapsed is "+ str(elapsed))
        time.sleep(60)
        # perform MTD migration action
        ns = nsi.nss_list.get(name="ns_with_systemic")
        location = VNF.objects.filter(ns_parent=ns)[0].vim.location
        locations = []
        vims = VIM.objects.all()
        for vim in vims:
            locations.append(vim.location)
        locations.remove(location)
        if locations:
            start = datetime.now()
            print("called MTD migrate at " + str(start))
            res = migrate_ns(slicem, nsi, ns, locations[0])
            end = datetime.now()
            elapsed = end - start
            print("finished MTD migrate at " + str(end) + " time elapsed is " + str(elapsed))
        time.sleep(60)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # receive 'ping' request from UE
        trigger_MTD_1()
        # used to change the image of cirros vnfs to taget_iperf image
        # tmp()