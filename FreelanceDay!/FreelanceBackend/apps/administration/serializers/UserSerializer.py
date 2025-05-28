from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)
    role = serializers.CharField(max_length=20)
    date = serializers.DateField()
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    organization = serializers.CharField(required=False)
