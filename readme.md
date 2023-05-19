# MOTDEC - MTD Controller

-----------------------------------------

## :page_with_curl: What is MOTDEC?


MOTDEC is a Moving Target Defense (MTD) controller. It orchestrates and enforces MTD operations on 5G and beyond Telco Cloud networks based on the NFV architecture.
MOTDEC operates 2 types of MTD operations:

- Hard MTD actions: reinstantiation and migration of virtual network functions (VNFs) and network services (NSs) using the network slice manager Katana, the NFV orchestrator OSM, and the Virtual Infrastructure Manager (VIM) OpenStack.
- Soft MTD operations: it changes the topology of the network and the traffic path of the various communications using the SDNC ONOS and TopoFuzzer.

## :clipboard: Features

- Integration of MOTDEC in a Telco Cloud environment that uses OpenStack, OSM, Katana
- REST API interface to enforce MTD operations of the detected running VNFs in the network
- Reinstantiate and migrate VNFs using their authenticated image for malware infection mitigation, proactively (periodically for prevention against undetected infections) and reactively (event-based triggered MTD operation)
- Monitor the network traffic using the MMT monitoring probes and control communication flows
- Integration of OptSFC, allowing to automate MTD operations using optimized strategies learned with Machine Learning (ML).

## :hammer_and_pick: Quick Start

**REQUIREMENTS:**
- Operating System: Ubuntu 18.04
- Python3.8 (```sudo apt install python3.8```)
- Python3-pip (```sudo apt install python3-pip```)
- Django 4.1.3 and other Python modules (```pip install -r requirements.txt```)
- You have a running Katana network slice manager and Topofuzzer in your Telco Cloud testbed


## Deploy MOTDEC

1. change the file `motdec/settings.py` to put the IP and port of Topofuzzer and the MMT probe in the correspondent fields `ALLOWED_HOSTS`, `TOPOFUZZER_IP`, `TOPOFUZZER_PORT`, and `MMT_PORT` (default port is 27017).
2. also in `motdec/settings.py`, add the public IP of your hosting machine to `ALLOWED_HOSTS`.
3. start the _sqlite3_ DB with `python3 manage.py makemigrations` and `python3 manage.py migrate`.
4. create an admin user with the command ```python manage.py createsuperuser```.
5. start the server with the command ````python manage.py runserver 0:8000````, which starts the MOTDEC REST API interface.

**Run MOTDEC's services**

6. start MOTDEC's four services (i.e., Katana and OSM based life cycle management, MMT traffic monitoring, threat and risk assessment, and the MTD orchestration) with the command ````sudo python manage.py main --katana-hostname <slicem_ip>```` where _\<slicem_ip\>_ is the IP or the hostname of the external network slice manager -> For now only Katana is compatible.
