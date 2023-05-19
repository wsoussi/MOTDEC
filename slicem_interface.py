import yaml
import json

# Here we have all the functions where MOTDEC interacts with the slice manager (temporarely  OSM)
def get_nsdName_from_nsName(osm_client, ns_name):
    resp = osm_client.ns.get(ns_name)
    nsd_name = resp["deploymentStatus"]["scenario_name"]
    return nsd_name

def get_vimID_from_nsName(osm_client, ns_name):
    resp = osm_client.ns.get("pingpong_ns")
    vim_id = resp["datacenter"]
    return vim_id


# move a NS to another VIM
def osm_move_ns(osm_client, ns_name, vim_account):
    nsdName = get_nsdName_from_nsName(osm_client, ns_name)
    resp = osm_client.ns.create(nsd_name = nsdName, nsr_name = ns_name, account = vim_account)
    print(yaml.safe_dump(resp))
    osm_client.ns.delete(ns_name)
    resp = osm_client.ns.list()
    print(yaml.safe_dump(resp))

# restart NS service to change the real IP and MAC addresses but stay in the same VIM datacenter
def osm_restart_ns(osm_client, ns_name):
    nsdName = get_nsdName_from_nsName(osm_client, ns_name)
    vim_id = get_vimID_from_nsName(osm_client, ns_name)
    resp = osm_client.ns.create(nsd_name = nsdName, nsr_name = ns_name, account = vim_id)
    print(yaml.safe_dump(resp))
    osm_client.ns.delete(ns_name)
    resp = osm_client.ns.list()
    print(yaml.safe_dump(resp))

def osm_deploy_motdec_ns(osm_client, vim_account):
    # if topoFuzzer descriptor not in OSM add it
    if "topoFuzzer" not in yaml.safe_dump(osm_client.vnfd.list()):
        osm_client.vnfd.create("topology_fuzzer/topoFuzzer_vnfd.yaml")
        i = 0
        while "topoFuzzer" not in yaml.safe_dump(osm_client.vnfd.list()):
            if i == 1000:
                print("VNFD topoFuzzer failed to be added")
                break;
            i+= 1;
    if "motdec" not in yaml.safe_dump(osm_client.nsd.list()):
        osm_client.nsd.create("topology_fuzzer/motdec_nsd.yaml")
        i = 0
        while "motdec" not in yaml.safe_dump(osm_client.nsd.list()):
            if i == 1000:
                print("NSD motdec failed to be added")
                break;
            i+= 1;
    resp = osm_client.ns.create(nsd_name = "motdec", nsr_name = "topoFuzzer", account = vim_account)
    print(yaml.safe_dump(resp))

# get running resources data
def getRunningResources(osm_client, auth_token):
    # get the reources from OSM
    vnf_list = json.loads(osm_client.get_vnf_instances(token=auth_token["id"]))
    vnf_list = json.loads(vnf_list["data"])
    print(vnf_list)
    ns_list = json.loads(osm_client.get_ns_instances(token=auth_token["id"]))
    ns_list = json.loads(ns_list["data"])
    print(json.dumps(vnf_list) + json.dumps(ns_list))
