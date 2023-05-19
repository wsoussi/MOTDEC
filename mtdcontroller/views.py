# from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import UserSerializer, GroupSerializer, VIMSerializer, SliceMSerializer, NFVO2VIMSerializer, Attack_alertSerializer, Attack_surfaceSerializer, MTD_actionSerializer
from .katanaclient import katanacli
from .models import SliceM, VIM, RelationNFVO2VIM, Attack_alert, Attack_surface, MTD_action
import logging

""""
    REST API
"""
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class VIMViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows VIMs to be viewed or edited.
    """
    queryset = VIM.objects.all()
    serializer_class = VIMSerializer
    permission_classes = [permissions.IsAuthenticated]

class SliceMViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows network slices to be viewed or edited.
    """
    queryset = SliceM.objects.all()
    serializer_class = SliceMSerializer
    permission_classes = [permissions.IsAuthenticated]

class NFVO2VIMViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows NFVOs-to-VIM relations to be viewed or edited.
    """
    queryset = RelationNFVO2VIM.objects.all()
    serializer_class = NFVO2VIMSerializer
    permission_classes = [permissions.IsAuthenticated]

class Attack_alertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows attack alerts to be viewed or edited.
    """
    queryset = Attack_alert.objects.all()
    serializer_class = Attack_alertSerializer
    permission_classes = [permissions.IsAuthenticated]

class Attack_surfaceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows attack surfaces to be viewed or edited.
    """
    queryset = Attack_surface.objects.all()
    serializer_class = Attack_surfaceSerializer
    permission_classes = [permissions.IsAuthenticated]

class MTD_actionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows mtd actions to be viewed or edited.
    """
    queryset = MTD_action.objects.all()
    serializer_class = MTD_actionSerializer
    permission_classes = [permissions.IsAuthenticated]