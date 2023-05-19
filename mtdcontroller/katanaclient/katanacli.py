import requests
import json
import yaml
import asyncio

""""
    Convert cmd_cli code from the bottom link into Python API calls
    https://github.com/medianetlab/katana-slice_manager/tree/master/katana-cli/cli/commands
"""

# VNF requests

async def nfvo_ls(katana_hostname, katana_port=8000):
    """
        List nfvos
        """

    url = "http://{0}:{1}/api/nfvo".format(str(katana_hostname), str(katana_port))
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nfvo_inspect(katana_hostname, id, katana_port=8000):
    """
    Display detailed information of NFVO
    """
    url = "http://{0}:{1}/api/nfvo/{2}".format(str(katana_hostname), str(katana_port), str(id))
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        if not json_data:
            return "Error: No such nfvo: {0}".format(str(id))
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:".format(str(err))


async def nfvo_add(file, katana_hostname, katana_port=8000):
    """
    Add new NFVO
    """
    try:
        stream = open(file, mode="r")
    except FileNotFoundError:
        return f"File {file} not found"

    with stream:
        data = yaml.safe_load(stream)

    url = "http://{0}:{1}/api/nfvo".format(str(katana_hostname), str(katana_port))
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()
        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nfvo_rm(vnfo_id, katana_hostname, katana_port=8000):
    """
    Remove NFVO
    """
    url = "http://{0}:{1}/api/nfvo/{2}".format(str(katana_hostname), str(katana_port), str(vnfo_id))
    r = None
    try:
        r = requests.delete(url, timeout=30)
        r.raise_for_status()
        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nfvo_update(file, vnfo_id, katana_hostname, katana_port=8000):
    """
    Update NFVO
    """
    try:
        stream = open(file, mode="r")
    except FileNotFoundError:
        return f"File {file} not found"

    with stream:
        data = yaml.safe_load(stream)

    url = "http://{0}:{1}/api/nfvo/{2}".format(str(katana_hostname), str(katana_port), str(vnfo_id))
    r = None
    try:
        r = requests.put(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()

        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


# SLICE requests
async def slice_ls(katana_hostname, katana_port=8000):
    """
    List slices
    """

    url = "http://{0}:{1}/api/slice".format(str(katana_hostname), str(katana_port))
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        return json_data

    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def slice_inspect(katana_hostname, uuid, katana_port=8000):
    """
    Display detailed information of slice
    """
    url = "http://{0}:{1}/api/slice/{2}".format(str(katana_hostname), str(katana_port), (uuid))
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        if not json_data:
            return "Error: No such slice: {}".format(uuid)
        return json_data

    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def slice_add(file, katana_hostname, katana_port=8000):
    """
    Add new slice
    """
    try:
        stream = open(file, mode="r")
    except FileNotFoundError:
        return f"File {file} not found"

    with stream:
        data = yaml.safe_load(stream)

    url = "http://{0}:{1}/api/slice".format(str(katana_hostname), str(katana_port))
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()

        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def slice_rm(id_list, katana_hostname,force = False, katana_port=8000):
    """
    Remove slices
    """
    for _id in id_list:

        force_arg = "?force=true" if force else ""

        url = "http://{0}:{1}/api/slice/{2}{3}".format(str(katana_hostname), str(katana_port), _id, force_arg)
        r = None
        try:
            r = requests.delete(url, timeout=30)
            r.raise_for_status()
            return r.content
        except requests.exceptions.HTTPError as errh:
            return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
        except requests.exceptions.ConnectionError as errc:
            return "Error Connecting:{0}".format(str(errc))
        except requests.exceptions.Timeout as errt:
            return "Timeout Error:{0}".format(str(errt))
        except requests.exceptions.RequestException as err:
            return "Error:{0}".format(str(err))


async def slice_modify(id, katana_hostname, payload=None, file=None, katana_port=8000):
    """
    Update slice
    """
    if payload:
        data = payload
    elif file:
        try:
            stream = open(file, mode="r")
        except FileNotFoundError:
            return f"File {file} not found"

        with stream:
            data = yaml.safe_load(stream)
    else:
        return "Error: the function needs either a payload or a file input"

    url = "http://{0}:{1}/api/slice/{2}/modify".format(str(katana_hostname), str(katana_port), id)
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()

        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def gst_ls(katana_hostname, katana_port=8000):
    """
    List GSTs
    """
    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/gst"
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))

    async def gst_inspect(katana_hostname, id, katana_port=8000):
        """
        Display detailed information of GST
        """
        url = "http://"+katana_hostname+":"+str(katana_port)+"/api/gst/" + id
        r = None
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            json_data = json.loads(r.content)
            if not json_data:
                return "Error: No such GST: {}".format(id)
            return json_data
        except requests.exceptions.HTTPError as errh:
            return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
        except requests.exceptions.ConnectionError as errc:
            return "Error Connecting:{0}".format(str(errc))
        except requests.exceptions.Timeout as errt:
            return "Timeout Error:{0}".format(str(errt))
        except requests.exceptions.RequestException as err:
            return "Error:{0}".format(str(err))


async def nsid_ls(katana_hostname, katana_port=8000):
    """
    List Slice Descriptors
    """
    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/base_slice_des"
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nsid_inspect(katana_hostname, id, katana_port=8000):
    """
    Display detailed information of Slice Descriptor
    """
    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/base_slice_des/" + id
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        if not json_data:
            return "Error: No such Slice Descriptor: {}".format(id)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nsid_add(katana_hostname, file, katana_port=8000):
    """
    Add new Base Slice Descriptor
    """
    try:
        stream = open(file, mode="r")
    except FileNotFoundError:
        return f"File {file} not found"
    with stream:
        data = yaml.safe_load(stream)

    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/base_slice_des"
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()

        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nsid_rm(katana_hostname, id, katana_port=8000):
    """
    Remove a Base Slice Descriptor
    """
    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/base_slice_des/" + id
    r = None
    try:
        r = requests.delete(url, timeout=30)
        r.raise_for_status()
        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def nsid_update(katana_hostname, file, id, katana_port=8000):
    """
    Update Base Slice Descriptor
    """
    with open(file, "r") as stream:
        data = yaml.safe_load(stream)

    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/base_slice_des/" + id
    r = None
    try:
        r = requests.put(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()

        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def vim_ls(katana_hostname, katana_port = 8000):
    """
    List vims
    """

    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/vim"
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))

async def vim_inspect(katana_hostname, id, katana_port = 8000):
    """
    Display detailed information of VIM
    """
    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/vim/" + str(id)
    r = None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        json_data = json.loads(r.content)
        # indent=2 "beautifies" json
        if not json_data:
            return("Error: No such vim: {}".format(id))
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def vim_add(katana_hostname, file, katana_port = 8000):
    """
    Add new VIM
    """
    try:
        stream = open(file, mode="r")
    except FileNotFoundError:
        return f"File {file} not found"
    with stream:
        data = yaml.safe_load(stream)

    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/vim"
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()
        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def vim_rm(katana_hostname, katana_port = 8000):
    """
    Remove VIM
    """
    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/vim/" + id
    r = None
    try:
        r = requests.delete(url, timeout=30)
        r.raise_for_status()
        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


async def vim_update(katana_hostname, file, id, katana_port = 8000):
    """
    Update VIM
    """
    try:
        stream = open(file, mode="r")
    except FileNotFoundError:
        return f"File {file} not found"
    with stream:
        data = yaml.safe_load(stream)

    url = "http://"+katana_hostname+":"+str(katana_port)+"/api/vim/" + id
    r = None
    try:
        r = requests.put(url, json=json.loads(json.dumps(data)), timeout=30)
        r.raise_for_status()
        return r.content
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(r.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))
