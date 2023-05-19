from django.core.management.base import BaseCommand
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()
from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state, Attack_alert

from mtdcontroller.systemiclient import systemicli
from flask import Flask, json

HOST = "10.161.1.124"  # Standard loopback interface address (localhost)
PORT = 8800  # Port to listen on


api = Flask(__name__)


@api.route('/ingest', methods=['GET'])
# for each ping received send an /ingest to Sytemic
def ingest():
    # for each ping received send an /ingest to Sytemic
    # ---- get tages NS
    tages_ns = NS.objects.get(name="ns_with_systemic")
    print(str(tages_ns.primary_ip))
    # ---- send the integrity request
    response = systemicli.ingest(tages_ns.primary_ip)
    return response


@api.route('/ip', methods=['GET'])
# for each ping received send an /ingest to Sytemic
def ip():
    tages_ns = NS.objects.get(name="ns_with_systemic")
    old_vnfs = VNF.objects.filter(ns_parent=tages_ns)
    location = old_vnfs[0].vim.location
    response = {"systemic ip" : tages_ns.primary_ip, "location": location}
    return response


@api.route('/ingest_big', methods=['GET'])
# for each ping received send an /ingest to Sytemic
def ingest_big():
    # for each ping received send an /ingest to Sytemic
    # ---- get tages NS
    tages_ns = NS.objects.get(name="ns_with_systemic")
    print(str(tages_ns.primary_ip))
    # ---- send the integrity request
    response = systemicli.ingest(tages_ns.primary_ip)
    response["systemic ip"] = tages_ns.primary_ip
    response["big"] = "ciao" * 1000000
    return response


class Command(BaseCommand):
    def handle(self, *args, **options):
        # receive 'ping' request from UE
        api.run(host="10.161.1.124") # port is 5000

