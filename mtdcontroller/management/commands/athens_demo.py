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
from .mtd_hard_actions import restart_ns_v2, migrate_ns
from flask import Flask, json, request
from colorama import Fore, Style

time_laps = 15

api = Flask(__name__)


@api.route('/integrity_check', methods=['GET'])
# send /integrity to Sytemic
def check_vnf_integrity():
    # get tages NS
    ns = NS.objects.get(name="ns_with_systemic")
    # send the integrity request
    res = systemicli.integrity_check(ns.primary_ip)
    return res


@api.route('/', methods=['GET'])
def show_vnf():
    # get tages NS
    ns = NS.objects.get(name="ns_with_systemic")
    # send the integrity request
    res = systemicli.interface(ns.primary_ip)
    return res


@api.route('/tamper', methods=['GET'])
# tamper the VNF twice with a 20 seconds sleep inbetween
def trigger_tampering_attack():
    # get tages NS
    ns = NS.objects.get(name="ns_with_systemic")
    # trigger tampering attack
    res = systemicli.tamper(ns.primary_ip)
    print(Fore.RED + str(res) + Style.RESET_ALL)
    time.sleep(10)
    # trigger tampering attack
    res = systemicli.tamper(ns.primary_ip)
    print(Fore.RED + str(res) + Style.RESET_ALL)
    return res

@api.route('/enforce', methods=['POST'])
def enforce_OptSFC_decision():
    data = request.get_json()
    action = data["action"]
    # check action i within range otherwise ignore
    # determine ns
    if action < 8:
        if action <2:
            ns = NS.objects.get(name="ns_with_systemic")
        elif action < 4:
            ns = NS.objects.get(name="core_test_ns")
        elif action < 6:
            ns = NS.objects.get(name="extra_test_ns_core")
        else:
            ns = NS.objects.get(name="ns_with_systemic")
    else:
        return "can't enforce the action"

    #get the slicem
    slicem = SliceM.objects.first()
    nsi = NSi.objects.first()
    #determine action and do action
    if action % 2 == 0:
        # restart NS
        restart_ns_v2(slicem, nsi, ns)
    else:
        # migrate NS
        migrate_ns(slicem, nsi, ns)
    return "Success"


class Command(BaseCommand):
    def handle(self, *args, **options):
        # receive 'ping' request from UE
        api.run(host="10.161.1.124", port = 6161)