import requests
import json
import yaml

def integrity_check(systemic_ip):
    url = "http://{0}:8080/integrity".format(str(systemic_ip))
    payload = {}
    headers = {}
    try:
        response = requests.get(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        json_data = json.loads(response.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(response.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


def tamper(systemic_ip):
    url = "http://{0}:8080/attack/1".format(str(systemic_ip))
    payload = {}
    headers = {}
    try:
        response = requests.get(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        html_data = response.content
        return html_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(response.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))


def ingest(systemic_ip):
    url = "http://{0}:8080/ingest".format(str(systemic_ip))
    payload = {}
    headers = {}
    try:
        response = requests.get(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        json_data = json.loads(response.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(response.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))

def interface(systemic_ip):
    url = "http://{0}:8080/".format(str(systemic_ip))
    payload = {}
    headers = {}
    try:
        response = requests.get(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        json_data = json.loads(response.content)
        return json_data
    except requests.exceptions.HTTPError as errh:
        return "Http Error:{0}\n{1}".format(str(errh), str(response.content))
    except requests.exceptions.ConnectionError as errc:
        return "Error Connecting:{0}".format(str(errc))
    except requests.exceptions.Timeout as errt:
        return "Timeout Error:{0}".format(str(errt))
    except requests.exceptions.RequestException as err:
        return "Error:{0}".format(str(err))