from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    task_name = serializers.CharField()
    task_desc = serializers.CharField(max_length=200)
    complexity = serializers.IntegerField()
    cost = serializers.FloatField()
    create_dttm = serializers.DateField()