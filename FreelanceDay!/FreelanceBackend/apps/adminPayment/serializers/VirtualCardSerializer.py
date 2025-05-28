from rest_framework import serializers

class VirtualCardSerializer(serializers.Serializer):
    owner = serializers.IntegerField()
    role = serializers.CharField()
    modify_dttm = serializers.DateField()