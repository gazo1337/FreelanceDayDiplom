from rest_framework import serializers
from .models import User, Employer, Executor

class UserSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'login', 'password', 'role', 'date', 'organization', 'description']
        extra_kwargs = {
            'password': {'write_only': True},
            'organization': {'required': False},
            'description': {'required': False}
        }
    
    def create(self, validated_data):
        organization = validated_data.pop('organization', '')
        description = validated_data.pop('description', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            login=validated_data['login'],
            password=validated_data['password'],
            role=validated_data['role'],
        )
        user.organization = organization
        user.description = description
        user.save()
        return user

class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ['name', 'organization', 'description']

class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = ['name', 'description', 'level', 'loyalty', 'rating', 'completed_orders']