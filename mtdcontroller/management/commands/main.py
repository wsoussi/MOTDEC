from django.core.management.base import BaseCommand
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()
import logging
import time
import asyncio
from threading import Thread
from django.conf import settings

from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state
from .monitoring import sync_with_slicem
from .vuln_mon import start_vuln_monitoring
from .topoFuzzer_cli import topoFuzzer_update
import mtdcontroller.management.commands.motdec_test_utils as motdec_test_utils

monitoring_frequency = 10


def Monitoring_thread(stdout, slicem):
    while True:

        s = time.perf_counter()
        asyncio.run(sync_with_slicem(stdout, slicem))
        elapsed = time.perf_counter() - s

        # stdout.write(f"{__file__} monitoring cycle executed in {elapsed:0.2f} seconds.", ending='')
        print(f"{__file__} monitoring cycle executed in {elapsed:0.2f} seconds.")
        # if the monitoring cycle took longer that the expected frequency start the
        # new cycle just after the current one ends
        time.sleep(max(0, monitoring_frequency - elapsed))


def TopoFuzzer_update_thread(stdout):
    time.sleep(10) # wait for the first monitoring cycle
    topoFuzzer_update(stdout, settings.TOPOFUZZER_IP, settings.TOPOFUZZER_PORT)

def Vulnerabilities_thread(stdout):
    time.sleep(10) # wait for the first monitoring cycle
    start_vuln_monitoring(stdout, monitoring_frequency)


def MOTDEC_thread(stdout, slicem): #TEST MTD HARD ACTIONS
    time.sleep(10) # wait for the first monitoring cycle
#     motdec_test_utils.test_mtd_migrate(stdout, slicem)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--katana-hostname', type=str, help='Katana CLI hostname or IP address', action="store", required=True)

        # Named (optional) arguments
        parser.add_argument('--osm-ip', type=str, help='OSM CLI IP address', action="store", required=False)
        parser.add_argument('--katana-port', type=int, help='Katana CLI port', required=False)

    def handle(self, *args, **options):
        if options['katana_port']:
            slicem_port = options['katana_port']
        else:
            slicem_port = 8000
        # if the slicem is not in DB add it
        try:
            slicem = SliceM.objects.get(slicem_ip=options['katana_hostname'])
        except SliceM.DoesNotExist:
            slicem = None
        if not slicem:
            slicem = SliceM(slicem_ip=options['katana_hostname'], slicem_port=slicem_port, type=SliceM.KATANA)
            slicem.save()

        # run the data gathering functions
        logger = logging.getLogger(__name__)
        ## start monitoring task in new thread
        mon_thread = Thread(target=Monitoring_thread, args=(logger, slicem))
        mon_thread.start()
        # start vulnerability scanning task in new thread
        vuln_thread = Thread(target=Vulnerabilities_thread, args=(logger, ))
        vuln_thread.start()
        # start TopoFuzzer mapping update
        topofuzzer_thread = Thread(target=TopoFuzzer_update_thread, args=(logger, ))
        topofuzzer_thread.start()
        ## start MOTDEC in new thread
        # motdec_thread = Thread(target=MOTDEC_thread, args=(logger, slicem))
        # motdec_thread.start()

        # wait for all threads
        mon_thread.join()
        vuln_thread.join()
        topofuzzer_thread.join()
        # motdec_thread.join()

