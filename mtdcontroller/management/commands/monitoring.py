import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_django_project.settings')
import django
django.setup()
from django.utils import timezone
from asgiref.sync import sync_to_async

import ipaddress
from urllib.parse import urlparse
import gc
import asyncio
import json

from mtdcontroller.models import SliceM, VIM, NFVO, VDU, Interface, RelationSliceM2VIM, RelationNFVO2VIM, NSi, NS, VNF, VIM_state, NS_state, NSi_state, VNF_state, VDU_state
from mtdcontroller.katanaclient import katanacli
import osmclient
from osmclient import client as osm_cli
# from osmclient.common.exceptions import ClientException

""""
    get data from Katana slice manager and OSM about the running resources starting from network slices
    and vertically descending till VNFs and VDUs. The functions is automatically called every 'monitoring_frequency'
    seconds (we consider 1 second for communication with the data sources and data analysis)
"""

@sync_to_async
def save_django_instance(django_instance):
    django_instance.save()

@sync_to_async
def get_vim(slicem, vim_id):
    try:
        res = VIM.objects.get(relationslicem2vim__slicem=slicem, relationslicem2vim__vim_id_at_slicem= vim_id)
    except VIM.DoesNotExist:
        res = None
    return res

async def add_update_VIMs(log_channel, slicem, vim_list):
    vims_info = {}
    for avim in vim_list:
        vim_info = asyncio.create_task(katanacli.vim_inspect(slicem.slicem_ip, avim['_id']))
        # is the VIM already in MOTDEC?
        vim = await get_vim(slicem, avim['_id'])
        # get vim info from async 'inspect' call
        vim_info = await vim_info
        parsed_url = urlparse(vim_info['auth_url'])
        if not vim:  # vim not in MOTDEC, ADD it to DB
            if vim_info['type'] == 'openstack':
                vim_type = VIM.OPENSTACK
            elif vim_info['type'] == 'openvim':
                vim_type = VIM.OPENVIM
            elif vim_info['type'] == 'azure':
                vim_type = VIM.AZURE
            elif vim_info['type'] == 'vmware':
                vim_type = VIM.VMWARE
            vim = VIM(slicem=slicem, environment=vim_type, location=vim_info['location'],
                      cores=vim_info['resources']['vcpus'], memory_mb=vim_info['resources']['memory_mb'],
                      disk_gb=vim_info['resources']['local_gb'], vim_ip=parsed_url.netloc.split(':')[0], vim_port=parsed_url.port, vim_url=vim_info['auth_url'])
            await save_django_instance(vim)
            add_relation = RelationSliceM2VIM(slicem=slicem, vim=vim, vim_id_at_slicem=avim['_id'],
                                              vim_id2_at_slicem=avim['vim_id'])
            await save_django_instance(add_relation)
        else: # UPDATE the existing VIM
            vim.location = vim_info['location']
            vim.cores = vim_info['resources']['vcpus']
            vim.memory_mb = vim_info['resources']['memory_mb']
            vim.disk_gb = vim_info['resources']['local_gb']
            vim.vim_ip = parsed_url.netloc.split(':')[0]
            vim.vim_port = parsed_url.port
            vim.vim_url = vim_info['auth_url']
            await save_django_instance(vim)
        vims_info[vim_info['_id']] = vim_info
    return vims_info

@sync_to_async
def get_nfvo(slicem, nfvo_id):
    return NFVO.objects.get(slicem=slicem, nfvo_id_at_slicem= nfvo_id)

async def add_update_NFVOs(log_channel, slicem, nfvo_list):
    nfvos_info = {}
    for nfvo_o in nfvo_list:
        nfvo_info = asyncio.create_task(katanacli.nfvo_inspect(slicem.slicem_ip, id=nfvo_o['_id']))
        try:
            nfvo = await get_nfvo(slicem, nfvo_o['_id'])
        except NFVO.DoesNotExist:
            nfvo = None
        nfvo_info = await nfvo_info
        if not nfvo:  # ADD the NFVO in MOTDEC
            if nfvo_o['type'] == 'OSM':
                nfvo_type = NFVO.OSM
            else:
                nfvo_type = NFVO.SONATA
            nfvo = NFVO(type=nfvo_type, slicem=slicem, nfvo_id_at_slicem=nfvo_o['_id'], name=nfvo_info['name'],
                        nfvo_ip=nfvo_info['nfvoip'], nfvo_id2_at_slicem=nfvo_o['nfvo_id'])
            await save_django_instance(nfvo)
        else:
            nfvo.nfvo_ip = nfvo_info['nfvoip']
            await save_django_instance(nfvo)
        nfvos_info[nfvo_info['_id']] = nfvo_info
    return nfvos_info

async def add_and_update_new_VIMs_NFVOs(log_channel, slicem, vim_list, nfvo_list):
    # add/update NFVOs
    task_add_update_VIMs = asyncio.create_task(add_update_VIMs(log_channel, slicem, vim_list))
    # add/update VIMs
    task_add_update_NFVOs = asyncio.create_task(add_update_NFVOs(log_channel, slicem, nfvo_list))
    vims_info = await task_add_update_VIMs
    nfvos_info = await task_add_update_NFVOs
    return vims_info, nfvos_info

@sync_to_async
def add_and_update_new_resources(log_channel, slice_info, slicem, net_slice):
    for key, ns in slice_info['ns_inst_info'].items():
        for location, nss in ns.items():
            if nss['status'] == "Started":
                # get name
                name = nss['ns-name']
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
                nfvo = NFVO.objects.get(nfvo_id2_at_slicem=nss['nfvo-id'])
                osm_client = osm_cli.Client(host=nfvo.nfvo_ip, sol005=True, **kwargs)
                vnfs_in_nfvo = osm_client.vnf.list()
                vnfds_in_nfvo = osm_client.vnfd.list()
                # log_channel.write(json.dumps(nss_in_nfvo, indent=4), ending='')
                try:
                    ns_in_nfvo = osm_client.ns.get(nss['nfvo_inst_ns'])
                    net_service = NS.objects.filter(slicem=slicem, name=name).latest('id')
                except NS.DoesNotExist: # add NS if not in database
                    net_service = None
                except osmclient.common.exceptions.NotFound: # NS not in OSM (NS restarted or migrated with MTD, or it was terminated or something happened)
                    ns_in_nfvo = None
                if ns_in_nfvo:
                    if not net_service:
                        net_service = NS(slicem=slicem, nfvo=nfvo, name=nss['ns-name'], nsd_id = nss['nsd-id'], resource_id_at_slicem=key,
                                         resource_id_at_nfvo=nss['nfvo_inst_ns'], primary_ip=nss['vnfr'][0]['mgmt_ip'])
                    if ns_in_nfvo['operational-status'] == 'running':
                        net_service.is_running = True
                    else:
                        net_service.is_running = False
                    net_service.resource_id_at_slicem = key
                    net_service.resource_id_at_nfvo = nss['nfvo_inst_ns']
                    net_service.primary_ip = nss['vnfr'][0]['mgmt_ip']
                    net_service.save()

                    # add/update VNF
                    for vnf_o in nss['vnfr']:
                        # match vnf in katana json with OSM vnf list
                        vdus_list = []
                        interfaces_list = []
                        for vnf_in_nfvo in vnfs_in_nfvo:
                            if vnf_in_nfvo['ip-address'] == vnf_o['mgmt_ip']:
                                vnf_id_at_nfvo = vnf_in_nfvo['id']
                                for vnfd in vnfds_in_nfvo:
                                    if vnfd['_id'] == vnf_in_nfvo['vnfd-id']:
                                        # sum resources from each VDU of the VNF
                                        sum_mem = 0
                                        sum_disk = 0
                                        sum_cpu = 0
                                        try:
                                            vnf = VNF.objects.get(ns_parent=net_service,
                                                                  member_vnf_index_ref=vnf_in_nfvo[
                                                                      'member-vnf-index-ref'])
                                        except VNF.DoesNotExist:
                                            vnf = None
                                        if not vnf:
                                            vnf = VNF(slicem=slicem, nfvo=nfvo, name=vnf_o['vnf_name'],
                                                      ns_parent=net_service,
                                                      resource_id_at_nfvo=vnf_id_at_nfvo,
                                                      vim=RelationNFVO2VIM.objects.get(nfvo=nfvo,
                                                                                       vim_id_at_nfvo=
                                                                                       vnf_in_nfvo[
                                                                                           'vim-account-id']).vim,
                                                      member_vnf_index_ref=vnf_in_nfvo[
                                                          'member-vnf-index-ref'],
                                                      req_memory_mb=sum_mem,
                                                      req_disk_gb=sum_disk, req_cores=sum_cpu)
                                            vnf.save()
                                        # update/add VDU
                                        for vdu_osm in vnfd['vdu']:
                                            try:
                                                vdu = VDU.objects.get(id_at_nfvo=vdu_osm['id'], vnf_parent=vnf)
                                            except VDU.DoesNotExist:
                                                vdu = None
                                            if not vdu:
                                                vdu = VDU(slicem=slicem, vnf_parent = vnf, name=vdu_osm['name'], resource_id_at_slicem='', id_at_nfvo=vdu_osm['id'], image_name=vdu_osm['image'])
                                            vdu.req_cores = int(vdu_osm['vm-flavor']['vcpu-count'])
                                            vdu.req_memory_mb = int(vdu_osm['vm-flavor']['memory-mb'])
                                            vdu.req_disk_gb = int(vdu_osm['vm-flavor']['storage-gb'])
                                            for vdur in vnf_in_nfvo['vdur']:
                                                if vdu_osm['id'] == vdur['vdu-id-ref']:
                                                    if vdur['status'] == 'ACTIVE':
                                                        vdu.is_running = True
                                                    else:
                                                        vdu.is_running = False
                                                    ip_type = ipaddress.ip_address(vdur['ip-address']).version
                                                    if ip_type == 4:
                                                        vdu.real_ipv4 = vdur['ip-address']
                                                    else:
                                                        vdu.real_ipv6 = vdur['íp-address']
                                                    # add interfaces of the vdu
                                                    for interf in vdur['interfaces']:
                                                        interface = Interface(vdu=vdu, name=interf['name'], external_conn_point=interf['external-connection-point-ref'], mgmt_vnf=interf['mgmt-vnf'], ns_vld_id=interf['ns-vld-id'], ip=interf['ip-address'], mac=interf['mac-address'])
                                                        interfaces_list.append(interface)
                                            vdu.save()
                                            # do the sum for the VNF attributes
                                            sum_cpu += vdu.req_cores
                                            sum_mem += vdu.req_memory_mb
                                            sum_disk += vdu.req_disk_gb
                                            vdus_list.append(vdu)
                                        ip_type = ipaddress.ip_address(vnf_o['mgmt_ip']).version
                        # update vnf
                        vnf.vim = RelationNFVO2VIM.objects.get(nfvo=nfvo, vim_id_at_nfvo=vnf_in_nfvo['vim-account-id']).vim
                        vnf.member_vnf_index_ref = vnf_in_nfvo['member-vnf-index-ref']
                        if ip_type == 4:
                            vnf.real_ipv4=vnf_o['mgmt_ip']
                        else:
                            vnf.real_ipv6=vnf_o['mgmt_ip']
                        vnf.req_memory_mb = sum_mem
                        vnf.req_disk_gb = sum_disk
                        vnf.req_cores = sum_cpu
                        vnf.save()
                    # save interfaces
                    for interf in interfaces_list:
                        interf.save()
                # link the NS to its network slice
                net_slice.nss_list.add(net_service)

@sync_to_async
def remove_old_VIMs_NFVOs(vim_list, nfvo_list):
    # delete vims that are no longer in their related slice manager
    vims_in_motdec = VIM.objects.all()
    for vim in vims_in_motdec:
        # get the slice managers using the vim
        slicems = SliceM.objects.filter(vims=vim)
        is_in_a_slicem = False
        # if a slice manager is still using the vim don't delete it
        for slicem in slicems:
            vim_id_at_slicem = RelationSliceM2VIM.objects.get(vim=vim, slicem=slicem).vim_id_at_slicem
            # if vim not in slicem remove it from MOTDEC
            if next((True for v in vim_list if v['_id'] == vim_id_at_slicem), False):
                is_in_a_slicem = True
        if not is_in_a_slicem:
            vim.delete()
    # delete nfvos that are no longer in the related slice manager
    nfvos_in_motdec = NFVO.objects.all()
    for nfvo in nfvos_in_motdec:
        slicem = nfvo.slicem
        if not next((True for nfv_o in nfvo_list if nfv_o['_id'] == nfvo.nfvo_id_at_slicem), False):
            nfvo.delete()

@sync_to_async
def remove_old_resources(slices, slices_info):
    # remove unexistent network slices (this doesn't remove sub-NSs and VNFs)
    net_slices = NSi.objects.all()
    for net_slice in net_slices:
        # if net_slice not in katana remove it
        if not next((True for s in slices if s['_id'] == net_slice.resource_id_at_slicem), False):
            net_slice.delete()
    """
    Cascade effect removes NSs and VNFs when nfvo is removed.
    Removing NSs that are not running anymore is done looping over all slice managers in MOTDEC
    """
    # get slice managers
    slicems = SliceM.objects.all()
    for slicem in slicems:
        active_nss_ids = []
        # get active NSs of the slicem
        for slice_info in slices_info:
            for active_ns_id, active_ns in slice_info['ns_inst_info'].items():
                for location, active_ns_info in active_ns.items():
                    if active_ns_info['status'] == "Started":
                        active_nss_ids.append(active_ns_id)
        # delete MOTDEC NSs that are not active
        nss = NS.objects.filter(slicem=slicem)
        for ns in nss:
            if ns.resource_id_at_slicem not in active_nss_ids:
                ns.delete()

@sync_to_async
def get_slice(slicem, slice_id):
    return NSi.objects.get(slicem=slicem, resource_id_at_slicem=slice_id)

@sync_to_async
def get_nfvo2(slicem, nfvo_id):
    return NFVO.objects.get(slicem=slicem, nfvo_id2_at_slicem=nfvo_id)

@sync_to_async
def get_vim2(slicem, vim_id2):
    return VIM.objects.get(relationslicem2vim__slicem=slicem, relationslicem2vim__vim_id2_at_slicem= vim_id2)

@sync_to_async
def django_add_nfvo_to_slice(slice, nfvo):
    slice.nfvos_list.add(nfvo)

def vim_state_changed(vim_state, old_state):
    if old_state.remaining_cores == vim_state.remaining_cores and old_state.remaining_memory_mb == vim_state.remaining_memory_mb and old_state.remaining_disk_gb == vim_state.remaining_disk_gb and \
            old_state.state == vim_state.state:
        return False
    return True

def vdu_state_changed(vdu_state, old_state):
    if old_state.vnf_parent_record == vdu_state.vnf_parent_record and set(json.loads(old_state.vims_records)) == set(json.loads(vdu_state.vims_records)) and old_state.req_cores == vdu_state.req_cores and old_state.req_memory_mb == vdu_state.req_memory_mb and \
            old_state.req_disk_gb == vdu_state.req_disk_gb and old_state.is_running == vdu_state.is_running:
        return False
    return True

def vnf_state_changed(vnf_state, old_state, last_timestamp):
    if set(json.loads(old_state.vims_records)) == set(json.loads(vnf_state.vims_records)) and old_state.cores == vnf_state.cores and old_state.memory_mb == vnf_state.memory_mb and old_state.disk_gb == vnf_state.disk_gb and \
            old_state.ns_parent_record == vnf_state.ns_parent_record:
        # if there is a vdu that has the last timestamp and is linked to the vnf state then the vdu changed, ergo the vnf changed
        related_vdu_states_with_last_timestamp = set(VDU_state.objects.filter(vnf_parent_record=vnf_state.resource_record, timestamp = last_timestamp))
        if not related_vdu_states_with_last_timestamp:
            # check if set of child_vdus is the same
            old_child_vdus = set(json.loads(old_state.sub_vdu_list))
            new_child_vdus = set(json.loads(vnf_state.sub_vdu_list))
            if old_child_vdus == new_child_vdus:
                return False
    return True

def ns_state_changed(ns_state, old_state, last_timestamp):
    if old_state.state != ns_state.state or old_state.is_running != ns_state.is_running:
        return True
    #check that the VIM list is the same
    old_vims = set(json.loads(old_state.vims_records))
    current_vims = set(json.loads(ns_state.vims_records))
    if current_vims != old_vims:
        return True
    # check sub-NSs list is the same
    old_subns = set(json.loads(old_state.sub_ns_list))
    current_subns = set(json.loads(ns_state.sub_ns_list))
    if current_subns != old_subns:
        return True
    # if there is a vnf that has the last timestamp and is linked to the ns state then the vnf changed, ergo the ns changed
    related_vnf_states_with_last_timestamp = set(VNF_state.objects.filter(ns_parent_record=ns_state.resource_record, timestamp=last_timestamp))
    if related_vnf_states_with_last_timestamp:
        return True
    # if nsi_parents record list is not the same then there has been a change
    old_nsi_parents = set(json.loads(old_state.nsi_parents_list))
    new_nsi_parents = set(json.loads(ns_state.nsi_parents_list))
    if old_nsi_parents != new_nsi_parents:
        return True
    # check if sub-vnfs list changed
    old_sub_vnf = set(json.loads(old_state.sub_vnf_list))
    new_sub_vnf = set(json.loads(ns_state.sub_vnf_list))
    if old_sub_vnf != new_sub_vnf:
        return True
    # nothing changed
    return False

def nsi_state_changed(nsi_state, old_state, last_timestamp):
    if nsi_state.is_running != old_state.is_running:
        return True
    # if there is a vnf that has the last timestamp and is linked to the ns state then the vnf changed, ergo the ns changed
    related_ns_states_with_last_timestamp = set(NS_state.objects.filter(nsi_parents_list__icontains=nsi_state.resource_record, timestamp=last_timestamp))
    if related_ns_states_with_last_timestamp:
        return True
    # check that the list of sub-NSs is the same
    old_subns = set(json.loads(old_state.sub_ns_list))
    current_subns = set(json.loads(nsi_state.sub_ns_list))
    if current_subns != old_subns:
        return True
    # nothing changed
    return False

def remove_unchanged_states(last_timestamp):
    # delete the last resource state if this is equal to its previous one, which will save us space in the DB
    # check VIMs states
    last_states = VIM_state.objects.filter(timestamp=last_timestamp)
    len_last_states = len(last_states)
    len_all_states = VIM_state.objects.count()
    if len_all_states != len_last_states: # do not proceed if there was no state before
        before_that = VIM_state.objects.order_by('-timestamp')[len_last_states]
        before_that = VIM_state.objects.filter(timestamp = before_that.timestamp)
        for vim_state in last_states:
            old_state = before_that.get(vim_record=vim_state.vim_record)
            if old_state and not vim_state_changed(vim_state, old_state): # delete if no change made
                print("same vims_state for " + str(vim_state.vim_record))
                vim_state.delete()

    # check VDUs states
    last_states = VDU_state.objects.filter(timestamp=last_timestamp)
    len_last_states = len(last_states)
    len_all_states = VDU_state.objects.count()
    if len_all_states != len_last_states: # do not proceed if there was no state before
        before_that = VDU_state.objects.order_by('-timestamp')[len_last_states]
        before_that = VDU_state.objects.filter(timestamp = before_that.timestamp)
        for vdu_state in last_states:
            old_state = before_that.get(resource_record=vdu_state.resource_record)
            if old_state and not vdu_state_changed(vdu_state, old_state): # delete if no change made
                print("same vdu_state for " + str(vdu_state.resource_record))
                vdu_state.delete()

    # check VNFs states
    last_states = VNF_state.objects.filter(timestamp=last_timestamp)
    len_last_states = len(last_states)
    len_all_states = VNF_state.objects.count()
    if len_all_states != len_last_states: # do not proceed if there was no state before
        before_that = VNF_state.objects.order_by('-timestamp')[len_last_states]
        before_that = VNF_state.objects.filter(timestamp = before_that.timestamp)
        for vnf_state in last_states:
            old_state = before_that.get(resource_record=vnf_state.resource_record)
            if old_state and not vnf_state_changed(vnf_state, old_state, last_timestamp): # delete if no change made
                print("same vnf_state for " + str(vnf_state.resource_record))
                vnf_state.delete()

    # check NSs states
    last_states = NS_state.objects.filter(timestamp=last_timestamp)
    len_last_states = len(last_states)
    len_all_states = NS_state.objects.count()
    if len_all_states != len_last_states: # do not proceed if there was no state before
        before_that = NS_state.objects.order_by('-timestamp')[len_last_states]
        before_that = NS_state.objects.filter(timestamp=before_that.timestamp)
        for ns_state in last_states:
            old_state = before_that.get(resource_record=ns_state.resource_record)
            if old_state and not ns_state_changed(ns_state, old_state, last_timestamp):
                print("same ns_state for " + str(ns_state.resource_record))
                ns_state.delete()

    # check NSis states
    last_states = NSi_state.objects.filter(timestamp=last_timestamp)
    len_last_states = len(last_states)
    len_all_states = NSi_state.objects.count()
    if len_all_states != len_last_states: # do not proceed if there was no state before
        before_that = NSi_state.objects.order_by('-timestamp')[len_last_states]
        before_that = NSi_state.objects.filter(timestamp=before_that.timestamp)
        for nsi_state in last_states:
            old_state = before_that.get(resource_record=nsi_state.resource_record)
            if old_state and not nsi_state_changed(nsi_state, old_state, last_timestamp):
                print("same nsi_state for " + str(nsi_state.resource_record))
                nsi_state.delete()


@sync_to_async
def add_resource_states(slicem, vims_info):
    datetime_now = timezone.now()
    # TODO add alert attack ingestion to change state into "attack"
    # add VIMs states
    vims = VIM.objects.all()
    for vim in vims:
        vim_id_at_slicem = RelationSliceM2VIM.objects.filter(slicem=slicem, vim=vim)[0].vim_id_at_slicem
        vim_info = vims_info[vim_id_at_slicem]
        vim_state = VIM_state(vim_record=vim.record(), timestamp=datetime_now)
        vim_state.timestamp = datetime_now
        vim_state.state = VIM_state.ORDINARY
        vim_state.remaining_cores = vim_info['resources']['vcpus'] - vim_info['resources']['vcpus_used']
        vim_state.remaining_memory_mb = vim_info['resources']['free_ram_mb']
        vim_state.remaining_disk_gb = vim.disk_gb - vim_info['resources']['local_gb_used']
        vim_state.save()
    del vims

    # add NSs states
    nss = NS.objects.all()
    for ns in nss:
        # create "empty" ns_state
        ns_state = NS_state(resource_record = ns.record(), timestamp=datetime_now, state=NS_state.ORDINARY)
        ns_state.is_running = ns.is_running
        ns_state.nsi_parents_list = json.dumps(list())
        # get VIMs of the NS
        ns_vnfs = ns.vnf_set.all()
        vims_records = set()
        sub_vnfs = set()
        for ns_vnf in ns_vnfs:
            sub_vnfs.add(ns_vnf.record())
            ns_vim = ns_vnf.vim
            # add current vim to ns_state
            vims_records.add(ns_vim.record())
        ns_state.sub_vnf_list = json.dumps(list(sub_vnfs))
        ns_state.vims_records = json.dumps(list(vims_records))
        sub_ns_records = set()
        for sub_ns in ns.nss_list.all():
            sub_ns_records.add(sub_ns.record())
        ns_state.sub_ns_list = json.dumps(list(sub_ns_records))
        ns_state.save()
    del nss

    # add VNFs states
    vnfs = VNF.objects.all()
    for vnf in vnfs:
        vnf_state = VNF_state(resource_record=vnf.record(), timestamp=datetime_now, state=VNF_state.ORDINARY)
        vnf_state.cores = vnf.req_cores
        vnf_state.memory_mb = vnf.req_memory_mb
        vnf_state.disk_gb = vnf.req_disk_gb
        vnf_state.ns_parent_record = vnf.ns_parent.record()
        vnf_state.vims_records = json.dumps( list(vnf.vim.record()) )
        vnf_state.save()
        vnf_vdu_record_list = set()
        # add VDUs states
        vdus_list = vnf.vdu_set.all()
        for vdu in vdus_list:
            vnf_vdu_record_list.add(vdu.record())
            vdu_state = VDU_state(resource_record=vdu.record(), vnf_parent_record=vnf.record(), timestamp=datetime_now)
            vdu_state.is_running = vdu.is_running
            vdu_state.state = VDU_state.ORDINARY
            vdu_state.req_cores = vdu.req_cores
            vdu_state.req_memory_mb = vdu.req_memory_mb
            vdu_state.req_disk_gb = vdu.req_disk_gb
            vdu_state.vims_records = json.dumps( list(vnf.vim.record()) )
            vdu_state.save()
        vnf_state.sub_vdu_list = json.dumps(list(vnf_vdu_record_list))
        vnf_state.save()
    del vnfs

    # add NSis states
    nsis = NSi.objects.all()
    for nsi in nsis:
        nsi_state = NSi_state(resource_record=nsi.record(), timestamp=datetime_now, state=NSi_state.ORDINARY, is_running=nsi.is_running)
        # add sub_NSs and unify their vims into one list
        sub_ns_records = set()
        vims_records = set()
        for ns in nsi.nss_list.all():
            # add sub_ns in nsi list
            sub_ns_records.add(ns.record())
            # also add nsi as parent in ns_state
            ns_state = NS_state.objects.filter(resource_record=ns.record(), timestamp=datetime_now)[0]
            ns_parents_nsi_list = set(json.loads(ns_state.nsi_parents_list))
            ns_parents_nsi_list.add(nsi.record())
            ns_state.nsi_parents_list = json.dumps(list(ns_parents_nsi_list))
            ns_state.save()
            # get vims of the sub_ns
            ns_vims_records = set(json.loads(ns_state.vims_records))
            vims_records.union(ns_vims_records)
        nsi_state.vims_records = json.dumps(list(vims_records))
        nsi_state.sub_ns_list = json.dumps(list(sub_ns_records))
        nsi_state.save()
    del nsis
    gc.collect()
    remove_unchanged_states(datetime_now)


async def sync_with_slicem(log_channel, slicem):
    slices = await katanacli.slice_ls(slicem.slicem_ip)
    slices_info = []
    # get network slices info from katana
    for slice in slices:
        slices_info.append(asyncio.create_task(katanacli.slice_inspect(slicem.slicem_ip, slice['_id'])))    # get list of vims and nfvos from katana
    vim_list = asyncio.create_task(katanacli.vim_ls(slicem.slicem_ip))
    nfvo_list = asyncio.create_task(katanacli.nfvo_ls(slicem.slicem_ip))
    vim_list = await vim_list
    nfvo_list = await nfvo_list
    # add VIMs and NFVOs if not in database
    vims_info, nfvos_info = await add_and_update_new_VIMs_NFVOs(log_channel, slicem, vim_list, nfvo_list)

    # add slices if not in database
    slices_info = await asyncio.gather(*slices_info, return_exceptions=True)
    slices_info = list(filter(lambda slice_info: slice_info['status'] == "Running", slices_info))
    for i, slice_info in enumerate(slices_info):
        # add_slice if not in MOTDEC (but we still check its subcomponents as an existing slice may be updated)
        try:
            net_slice = await get_slice(slicem, slice_info['_id'])
        except NSi.DoesNotExist:
            net_slice = None
        if not net_slice:
            net_slice = NSi(slicem=slicem, resource_id_at_slicem=slice_info['_id'], name='slice'+slice_info['_id'][0:5])
        if slice_info['status'] == 'Running':
            net_slice.is_running = True
        else:
            net_slice.is_running = False
        await save_django_instance(net_slice)

        for vim_pseudo_id, vims in slice_info['vim_list'].items():
            for nfvo_id2, vim_id_at_nfvo in vims['nfvo_vim_account'].items():
                # add nfvo to the network slice
                nfvo = await get_nfvo2(slicem, nfvo_id2)
                await django_add_nfvo_to_slice(net_slice,nfvo)
                await save_django_instance(net_slice)

                # link VIM to the related nfvo
                vim = await get_vim(slicem, vim_pseudo_id)
                if vim is None: #the VIM account is a new one generated automatically by Katana, but related to a vim in vim_list
                    # if a vim's id in VIM_list is the prefix of the unknown VIM then add vim_id_at_nfvo relation
                    for v in vim_list:
                        if vim_pseudo_id.startswith(v['vim_id']):
                            vim = await get_vim2(slicem, v['vim_id'])
                            break
                if vim is not None:
                    add1 = RelationNFVO2VIM(nfvo=nfvo, vim=vim, vim_id_at_nfvo=vim_id_at_nfvo)
                    await save_django_instance(add1)

        # in this loop add NSs, VNFs, and VDUs
        await add_and_update_new_resources(log_channel, slice_info, slicem, net_slice)
        #TODO add virtual links


    """
    Now we remove the old instances that are not running anymore.
    It's important to do it after updating, as the instance might change a
    dependency used in the remove_old functions (e.g. VNFs are fetched by their NFVO
    for their removal, but MTD actions can change the NFVO of the VNFs).
    """
    await remove_old_VIMs_NFVOs(vim_list, nfvo_list)
    await remove_old_resources(slices, slices_info)
    await add_resource_states(slicem, vims_info)