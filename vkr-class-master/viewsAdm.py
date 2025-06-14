from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from .models import User, Employer, Executor
from .serializers import UserSerializer, EmployerSerializer, ExecutorSerializer

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'X-Refresh-Token', openapi.IN_HEADER,
            description="Refresh Token",
            type=openapi.TYPE_STRING
        ),
    ]
)
@api_view(['GET'])
def refresh_token(request):
    refresh_token = request.META.get('HTTP_X_REFRESH_TOKEN')
        
    if not refresh_token:
        return Response(
            {"error": "Refresh token is required in X-Refresh-Token header"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)
            
        return Response({
            'access': new_access_token
        })
            
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
    ]
)
@api_view(['GET'])
def debug_token(request):
    token = request.META.get('HTTP_AUTHORIZATION', '').split('Bearer ')[-1]
    try:
        decoded = AccessToken(token)
        return Response({
            'user_id': decoded['user_id'],
            'login': decoded['username'],
            'role': decoded['role'],
            'is_valid': True
        })
    except Exception as e:
        return Response({'error': str(e)}, status=401)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'login',
            openapi.IN_QUERY,
            description="Логин для поиска",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'password',
            openapi.IN_QUERY,
            description="Пароль для поиска",
            type=openapi.TYPE_STRING
        ),
    ]
)
@api_view(['GET'])
def login(request):
    login = request.query_params.get('login')
    password = request.query_params.get('password')
    
    user = User.objects.filter(login=login).first()
    
    if user is None or not user.check_password(password):
        return Response("Неверный логин или пароль", status=status.HTTP_404_NOT_FOUND)
    
    payload = {
        'user_id': user.id,
        'login': user.login,
        'role': user.role,
    }

    refresh = RefreshToken()
    refresh.payload.update(payload)
    access = refresh.access_token
    access.payload.update(payload)

    user_data = {
        'id': user.id,
        'login': user.username,
        'role': user.role,
        'date': user.date
    }
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': user_data
    })

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'refresh_token', openapi.IN_HEADER,
            description="Refresh Token",
            type=openapi.TYPE_STRING
        ),
    ]
)
@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist() 
        
        return Response({'status': 'success'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@swagger_auto_schema(
    method='post',
    request_body=UserSerializer,
    responses={201: "Успех"}
)
@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(login=serializer.validated_data['login']).exists():
        return JsonResponse(
            {"error": "Пользователь с данным логином уже существует!"},
            status=401
        )
    
    user = serializer.save()

    if user.role == 'executor':
        Executor.objects.create(
            user=user,
            name=serializer.validated_data.get('username', ''),
            description=serializer.validated_data.get('description', '')
        )
    else:
        Employer.objects.create(
            user=user,
            name=serializer.validated_data.get('username', ''),
            organization=serializer.validated_data.get('organization', ''),
            description=serializer.validated_data.get('description', '')
        )
    
    return JsonResponse({"id": user.id}, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'id', openapi.IN_QUERY,
            description="ID пользователя",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
    ]
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def getUserById(request):
    user_id = request.query_params.get('id')
    user = get_object_or_404(User, id=user_id)
    
    user_data = {
        "id": user.id,
        "login": user.username,
        "role": user.role,
        "date": user.date
    }
    
    return Response([user_data])

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'id', openapi.IN_QUERY,
            description="ID пользователя",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
    ]
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def getEmployer(request):
    user_id = request.query_params.get('id')
    employer = get_object_or_404(Employer, user_id=user_id)
    serializer = EmployerSerializer(employer)
    
    response_data = {
        "login": employer.user.username,
        "date": employer.user.date,
        **serializer.data
    }
    
    return Response([response_data])

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'id', openapi.IN_QUERY,
            description="ID пользователя",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
    ]
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def getExecutor(request):
    user_id = request.query_params.get('id')
    executor = get_object_or_404(Executor, user_id=user_id)
    serializer = ExecutorSerializer(executor)
    
    response_data = {
        "login": executor.user.username,
        "date": executor.user.date,
        **serializer.data
    }
    
    return Response([response_data])