from django.shortcuts import render

# Create your views here.

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action



class EventAPIViewSet(ModelViewSet):
    @action(methods=["post"])
    def reserve(self,)
