import time
import json, yaml
import asyncio
import copy
from django.core.management.base import BaseCommand


from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state
from .mtd_hard_actions import restart_ns_v1, restart_ns_v2, migrate_ns

def test_mtd_restart(stdout, slicem):
    nsi = NSi.objects.all()[0]
    ns = nsi.nss_list.get(name= "ns_with_systemic")
    res = restart_ns_v2(slicem, nsi, ns)
    print(res)


def test_mtd_migrate(stdout, slicem):
    time.sleep(10)
    nsi = NSi.objects.all()[0]
    ns = nsi.nss_list.get(name= "ns_with_systemic")
    location = VNF.objects.filter(ns_parent= ns)[0].vim.location
    print("the location is " + location)
    locations = []
    vims = VIM.objects.all()
    for vim in vims:
        locations.append(vim.location)
    print("available locations are: " + str(locations))
    locations.remove(location)
    if locations:
        res = migrate_ns(slicem, nsi, ns, locations[0])
    else:
        stdout("migration impossible: there is only one location available")