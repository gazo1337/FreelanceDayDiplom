from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    initiator = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(max_length=200)
    complexity = serializers.IntegerField()
    cost = serializers.FloatField()
    create_dttm = serializers.DateField()