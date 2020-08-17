from rest_framework import serializers
from auction.models import *


class OneTimeBidSerializer(serializers.Serializer):
    auction = serializers.IntegerField()
    bid = serializers.IntegerField()
