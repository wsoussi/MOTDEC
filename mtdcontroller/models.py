import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class VIM(models.Model):
    OPENSTACK = 'Openstack'
    OPENVIM = 'OpenVIM'
    AZURE = 'Azure'
    VMWARE = 'VMware'
    CloudEnv = [
        (OPENSTACK, 'Openstack'),
        (OPENVIM, 'OpenVIM'),
        (AZURE, 'Azure'),
        (VMWARE, 'VMware')
    ]
    environment = models.CharField(choices=CloudEnv, max_length=len(max(CloudEnv[0], key=len)))
    location = models.CharField(max_length = 100)
    cores = models.IntegerField(validators=[MinValueValidator(2)])
    # memory in MB
    memory_mb = models.IntegerField(validators=[MinValueValidator(2048)])
    # disk space in GB
    disk_gb = models.IntegerField(validators=[MinValueValidator(20)])
    vim_ip =models.GenericIPAddressField()
    vim_port = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10000)])
    vim_url = models.CharField(max_length = 100)
    def __str__(self):
        return "VIM " + str(self.id) + " at location: " +str(self.location)+ "; ip:" + str(self.vim_ip) + "; VIM type:" + str(self.environment)

    def record(self):
        return "VIM " + str(self.id)

# slice manager model
class SliceM(models.Model):
    KATANA = 'Katana'
    OSM = 'OSM'
    SONATA = 'Sonata'
    ONAP = 'Onap'
    # authentication key to access the Slice Manager API
    authKey = models.BinaryField(max_length=16, validators=[MinLengthValidator(16)])
    vims = models.ManyToManyField(VIM, through='RelationSliceM2VIM')
    slicem_ip = models.GenericIPAddressField()
    slicem_port = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(65355)])
    KATANA = 'Katana'
    slicem_type = [
        (KATANA, 'Katana'),
        (OSM, 'Osm')
    ]
    type = models.CharField(choices=slicem_type, max_length=len(max(slicem_type[0], key=len)))

    def __str__(self):
        return "SLICEM " + str(self.id) + " of type: "+str(self.type)+"; ip:" + str(self.slicem_ip)

    def record(self):
        return "SliceM " + str(self.id)


class NFVO(models.Model):
    OSM = 'osm'
    SONATA = 'sonata'
    # authentication key to access the NFVO API
    NFVOType = [
        (OSM, 'osm'),
        (SONATA, 'sonata')
    ]
    type = models.CharField(choices=NFVOType, max_length=len(max(NFVOType[1], key=len)))
    name = models.CharField(max_length=50)
    authKey = models.BinaryField(max_length=16, validators=[MinLengthValidator(16)])
    vims_list = models.ManyToManyField(VIM, through='RelationNFVO2VIM')
    nfvo_ip = models.GenericIPAddressField()
    slicem = models.ForeignKey(SliceM, on_delete=models.DO_NOTHING)
    nfvo_id_at_slicem = models.CharField(max_length=100)
    nfvo_id2_at_slicem = models.CharField(max_length=100)

    def __str__(self):
        return "NFVO " + str(self.id) + " ip:" + str(self.nfvo_ip)

    def record(self):
        return "NFVO " + str(self.id)


class RelationNFVO2VIM(models.Model):
    nfvo = models.ForeignKey(NFVO, on_delete=models.RESTRICT)
    vim = models.ForeignKey(VIM, on_delete=models.RESTRICT)
    vim_id_at_nfvo = models.CharField(max_length=100, primary_key= True)


class RelationSliceM2VIM(models.Model):
    slicem = models.ForeignKey(SliceM, on_delete=models.RESTRICT)
    vim = models.ForeignKey(VIM, on_delete=models.RESTRICT)
    vim_id_at_slicem = models.CharField(max_length=100, primary_key= True)
    vim_id2_at_slicem = models.CharField(max_length=100)


#================================================================================================

# abstract model for VNFs, NSs, and NSis
class Resource_abstract(models.Model):
    slicem = models.ForeignKey(SliceM, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    resource_id_at_slicem = models.CharField(max_length=100)
    openvas_target_id = models.CharField(max_length=100, blank=True)
    openvas_task_id = models.CharField(max_length=100, blank=True)
    class Meta:
        abstract = True


class Resource(Resource_abstract):
    def __str__(self):
        return "Resource " + str(self.id)


class NS(Resource):
    nss_list = models.ManyToManyField('self', symmetrical=False, blank=True)
    primary_ip = models.GenericIPAddressField()
    nfvo = models.ForeignKey(NFVO, on_delete=models.CASCADE)
    resource_id_at_nfvo = models.CharField(max_length=100)
    is_running = models.BooleanField()
    nsd_id = models.CharField(max_length=100)
    def __str__(self):
        return "NS " + str(self.name) + " ip:" + str(self.primary_ip)

    def record(self):
        return "NS " + str(self.id)


class VNF(Resource):
    ns_parent = models.ForeignKey(NS, on_delete=models.CASCADE)
    vim = models.ForeignKey(VIM, on_delete=models.CASCADE)
    nfvo = models.ForeignKey(NFVO, on_delete=models.CASCADE)
    resource_id_at_nfvo = models.CharField(max_length=100)
    member_vnf_index_ref = models.CharField(max_length=50)
    real_ipv4 = models.GenericIPAddressField(protocol='ipv4', null=True)
    real_ipv6 = models.GenericIPAddressField(protocol='ipv6', null=True)
    public_ipv4 = models.GenericIPAddressField(protocol='ipv4', null=True)
    req_cores = models.IntegerField()
    # memory in MB
    req_memory_mb = models.IntegerField()
    # disk space in GB
    req_disk_gb = models.IntegerField()
    # req_bandwidth = models.IntegerField
    # req_latency = models.FloatField

    class Meta(Resource.Meta):
        db_table = 'vnf_table'

    def __str__(self):
        return "VNF " + str(self.id) + " ip:" + str(self.real_ipv4) + ";" + str(self.real_ipv6)

    def record(self):
        return "VNF " + str(self.id)



class VDU(Resource):
    vnf_parent = models.ForeignKey(VNF, on_delete=models.CASCADE)
    id_at_nfvo = models.CharField(max_length=100)
    image_name = models.CharField(max_length=100)
    real_ipv4 = models.GenericIPAddressField(protocol='ipv4', null=True)
    real_ipv6 = models.GenericIPAddressField(protocol='ipv6', null=True)
    req_cores = models.IntegerField()
    req_memory_mb = models.IntegerField()
    req_disk_gb = models.IntegerField()
    is_running = models.BooleanField()

    def clean(self):
        if self.real_ipv6 is None and self.real_ipv4 is None:
            raise ValidationError("An IP address of the VNF (either IPv4 or IPv6) has to be inserted")

    def record(self):
        return "VDU " + str(self.id)


class Interface(models.Model):
    vdu = models.ForeignKey(VDU, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    external_conn_point = models.CharField(max_length=100)
    mgmt_vnf = models.BooleanField()
    ns_vld_id = models.CharField(max_length=100)
    ip = models.GenericIPAddressField()
    mac = models.CharField(max_length=100)

    def __str__(self):
        return "Interface " + str(self.id) + " ip:" + str(self.name)

    def record(self):
        return "Interface " + str(self.id)


class NSi(Resource):
    nss_list = models.ManyToManyField(NS)
    nfvos_list = models.ManyToManyField(NFVO)
    is_running = models.BooleanField()
    def __str__(self):
        return "NSi " + str(self.id)

    def record(self):
        return "NSi " + str(self.id)


#================================================================================================
''' 
    OPTSFC STATE OBJECTS
'''

class VIM_state(models.Model):
    vim_record = models.CharField(max_length=150)
    timestamp = models.DateTimeField()
    remaining_cores = models.IntegerField(validators=[MinValueValidator(0)])
    remaining_memory_mb = models.IntegerField(validators=[MinValueValidator(0)])
    remaining_disk_gb = models.IntegerField(validators=[MinValueValidator(0)])
    # TODO add remaining bandwidth
    # TODO add remaining I/O per sec.
    # TODO add avg. latency
    ORDINARY = 'ordinary'
    SUSPICIOUS = 'suspicious'
    UNDER_ATTACK = 'attack'
    STATE = [
        (ORDINARY, 'ordinary'),
        (SUSPICIOUS, 'suspicious'),
        (UNDER_ATTACK, 'attack')
    ]
    state = models.CharField(choices=STATE, max_length=len(max(STATE[1], key=len)))
    def __str__(self):
        return "State of the VIM " + str(self.id) + " at " + str(self.timestamp)


class Resource_state(models.Model):
    resource_record = models.CharField(max_length=150)
    timestamp = models.DateTimeField()

    ORDINARY = 'ordinary'
    SUSPICIOUS = 'suspicious'
    UNDER_ATTACK = 'attack'
    STATE = [
        (ORDINARY, 'ordinary'),
        (SUSPICIOUS, 'suspicious'),
        (UNDER_ATTACK, 'attack')
    ]
    state = models.CharField(choices=STATE, max_length=len(max(STATE[1], key=len)))
    vims_records = models.CharField(max_length=10000) # this is a JSON string serializing a list of vim_records

    def recently_published(self, hours_ago):
        return self.date >= timezone.now() - datetime.timedelta(hours=hours_ago)

    def __str__(self):
        return "State of the resource " + str(self.id) #+ " VIMs: " + str(self.vims.all())


class NS_state(Resource_state):
    # virtual_mgmt_ipv4 = models.GenericIPAddressField(protocol='ipv4')
    # virtual_mgmt_ipv6 = models.GenericIPAddressField(protocol='ipv6')
    nsi_parents_list = models.CharField(max_length=100000) # this is a JSON string serializing a list of parent NSis (max ~ 1000)
    sub_ns_list = models.CharField(max_length=100000) # this is a JSON string serializing a list of sub-NSs (max ~ 1000)
    sub_vnf_list = models.CharField(max_length=100000) # this is a JSON string serializing a list of sub-VNFs (max ~ 1000)
    is_running = models.BooleanField()


class VNF_state(Resource_state):
    # virtual_ipv4 = models.GenericIPAddressField(protocol='ipv4')
    # virtual_ipv6 = models.GenericIPAddressField(protocol='ipv6')
    ns_parent_record = models.CharField(max_length=150)
    cores = models.IntegerField(validators=[MinValueValidator(0)])
    memory_mb = models.IntegerField(validators=[MinValueValidator(0)])
    disk_gb = models.IntegerField(validators=[MinValueValidator(0)])
    sub_vdu_list = models.CharField(max_length=100000) # this is a JSON string serializing a list of sub-NSs (max ~ 1000)
    # TODO number of UEs connections
    # TODO bandwidth used
    # TODO i/o frequency
    # TODO latency


class VDU_state(Resource_state):
    vnf_parent_record = models.CharField(max_length=150)
    # virtual_ipv6 = models.GenericIPAddressField(protocol='ipv6')
    # virtual_ipv4 = models.GenericIPAddressField(protocol='ipv4')
    req_cores = models.IntegerField(validators=[MinValueValidator(0)])
    req_memory_mb = models.IntegerField(validators=[MinValueValidator(0)])
    req_disk_gb = models.IntegerField(validators=[MinValueValidator(0)])
    is_running = models.BooleanField()


class NSi_state(Resource_state):
    sub_ns_list = models.CharField(max_length=1000000) # this is a JSON string serializing a list of sub-NSs (max ~ 10'000)
    is_running = models.BooleanField()


#================================================================================================

class Attack_alert(models.Model):
    TAMPERING = 'tampering'
    DDOS = 'ddos'
    GENERIC = 'generic'
    Attack_type = [
        (TAMPERING, 'tampering'),
        (DDOS, 'ddos'),
        (GENERIC, 'generic')
    ]
    type = models.CharField(choices=Attack_type, max_length=len(max(Attack_type[0], key=len)))
    description = models.CharField(max_length = 300)
    systemic_id = models.CharField(max_length = 100)
    created_at = models.DateTimeField()
    pid = models.IntegerField(validators=[MinValueValidator(0)])
    tid = models.IntegerField(validators=[MinValueValidator(0)])
    signature = models.CharField(max_length = 100)
    def __str__(self):
        return "Attack alert " + str(self.id) + " type:" + str(self.type) + "; systemic_id:" + str(self.systemic_id) + "; created at:" + str(self.created_at) + "; pid:" + str(self.pid) + "; tid:" + str(self.tid) + "; signature:" + str(self.signature)


class Attack_surface(models.Model):
    vdu_state = models.ForeignKey(VDU_state, on_delete=models.RESTRICT)
    timestamp = models.DateTimeField()
    # last_scan
    # the id of the OpenVAS report scan
    scan_result_id = models.CharField(max_length=100)
    # number of ports with vulnerable services
    nb_vulnerable_ports = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(65355)])
    # the computed min., max., avg. and std. dev. of CVSS scores grouped by attack type
    # cvss:={"apt": [[avg, min, max, std. dev.], [avg, min, max, std. dev.]], "data_leak": [[avg, min, max, std. dev.][avg, min, max, std. dev.]]
    #         "DoS":[[avg, min, max, std. dev.], [avg, min, max, std. dev.]]}
    cvss_metrics = models.CharField(max_length=10000) # this is a JSON string serializing a list of vim_records
    # set primary key timestamp and vdu_state
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['vdu_state', 'timestamp'], name='unique_vdu_state_timestamp_set'
            )
        ]


class MTD_action(models.Model):
    DO_NOTHING = 'nomtd'
    PORT_HOP = 'port_hop'
    RESTART = 'restart'
    MIGRATE = 'migrate'
    MTD_actions = [
        (DO_NOTHING, 'nomtd'),
        (PORT_HOP, 'port_hop'),
        (RESTART, 'restart'),
        (MIGRATE, 'migrate')
    ]
    mtd_action = models.CharField(choices=MTD_actions, max_length=100)
    # the resource_overhead, network_overhead, and qos_overhead can be put as a relational table between MTD_action and the resource
    # resource_overhead = models.FloatField()
    # _overhead = models.FloatField()
    # qos_overhead = models.FloatField()

