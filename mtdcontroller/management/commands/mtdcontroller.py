from django.core.management.base import BaseCommand
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()

import time
import asyncio
from threading import Thread

from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state
from .monitoring import sync_with_slicem
import mtdcontroller.management.commands.motdec_test_utils as motdec_test_utils

monitoring_frequency = 10


def MOTDEC_thread(stdout, slicem): #TEST MTD HARD ACTIONS
    while True:
        time.sleep(2)

        
    motdec_test_utils.test_mtd_migrate(stdout, slicem)