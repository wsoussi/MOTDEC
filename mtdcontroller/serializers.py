from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import SliceM, VIM, RelationNFVO2VIM, Attack_alert, Attack_surface, MTD_action


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class VIMSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VIM
        fields = ['environment', 'location', 'vim_ip', 'cores', 'memory_mb', 'disk_gb']

class SliceMSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SliceM
        fields = ['slicem_ip', 'slicem_port', 'slicem_type', 'auth_key', 'vim_list']

class NFVO2VIMSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RelationNFVO2VIM
        fields = ['nfvo', 'vim', 'vim_id_at_nfvo']

class Attack_alertSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attack_alert
        fields = ['type', 'description', 'systemic_id', 'created_at', 'pid', 'tid', 'signature']

class Attack_surfaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attack_surface
        fields = ['vdu_state', 'timestamp', 'scan_result_id', 'nb_vulnerable_ports', 'cvss_metrics']

class MTD_actionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MTD_action
        fields = ['mtd_action']