from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from apps.administration.serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from collections import namedtuple
import psycopg2

conn = psycopg2.connect(dbname='adm', user='postgres', 
                        password='postgres', host='localhost')
cursor = conn.cursor()

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
            'login': decoded['login'],
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
    userLogin = request.query_params.get('login')
    userPass = request.query_params.get('password') 
    cursor.execute(
        "SELECT * FROM user_login WHERE login = %s AND password = %s",
        [userLogin, userPass]
    )
    record = cursor.fetchone()
    if record is None:
        return Response("Неверный логин или пароль", status=status.HTTP_404_NOT_FOUND)
    User = namedtuple('User', ['id', 'login', 'password', 'role', 'date'])
    user = User(
        id=record[2], 
        login=record[0],
        password=record[1],
        role=record[3],
        date=record[4]
    )
    
    payload = {
        'user_id': record[2],
        'login': record[0],
        'role': record[3],
    }

    refresh = RefreshToken()
    refresh.payload.update(payload)
    access = refresh.access_token
    access.payload.update(payload)

    user_data = {
        'id': user.id,
        'login': user.login,
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
    request_body=UserSerializer.UserSerializer,
    responses={201: "Успех"}
)
@api_view(['POST'])
def register(request):
    serializer = UserSerializer.UserSerializer(data=request.data)
    if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    val = serializer.validated_data
    cursor.execute(
        """
        select *
        from user_login
        where login = %s
        """,
        (val['login'],)
    )
    result = cursor.fetchone()
    if result is not None:
        return JsonResponse(
            {"error": f"Пользователь с данным логином уже существует!"},
            status=401
        )
    cursor.execute(
        """
        select user_id
        from user_login
        order by user_id desc limit 1
        """
    )
    result = cursor.fetchone()
    last_id = int(result[0]) + 1 if result else 1
    
    cursor.execute(
        """
        insert into user_login
        values(%s, %s, %s, %s, %s)
        """,
        [
            val['login'],
            val['password'],
            last_id,
            val['role'],
            val['date']
        ]
    )
    conn.commit()
    if val['role'] == 'executor':
        cursor.execute(
            """
            insert into executor
            values(%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                last_id,
                val['name'],
                val.get('description', ''),
                0,
                0,
                0,
                0,
                val['date']
            ]
        )
        conn.commit()
    else:
        cursor.execute(
            """
            insert into employer
            values(%s, %s, %s, %s, %s)
            """,
            [
                last_id,
                val['name'],
                val['organization'],
                val.get('description', ''),
                val['date']
            ]
        )
        conn.commit()
    return JsonResponse({"id": last_id}, status=status.HTTP_201_CREATED)


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
    userId = request.query_params.get('id')
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        )
    cursor.execute(
        "SELECT * FROM user_login WHERE user_id = %s",
        [userId]
    )
    record = cursor.fetchone()
    if record is None:
        return Response("Неверный идентификатор пользователя", status=status.HTTP_404_NOT_FOUND)
    userData = [{
        "id": record[2],
        "login": record[0],
        "role": record[3],
        "date": record[4]
    }]
    return Response(userData)


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
    userId = request.query_params.get('id')
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        )
    cursor.execute(
        "SELECT ul.login, " \
        "ul.create_dttm, " \
        "e.name, " \
        "e.organization, " \
        "e.description " \
        "FROM user_login ul " \
        "JOIN employer e " \
        "ON ul.user_id = e.user_id " \
        "WHERE ul.user_id = %s",
        [userId]
    )
    record = cursor.fetchone()
    if record is None:
        return Response("Неверный идентификатор пользователя", status=status.HTTP_404_NOT_FOUND)
    userData = [{
        "login": record[0],
        "date": record[1],
        "name": record[2],
        "oranization": record[3],
        "description": record[4]
    }]
    return Response(userData)


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
    userId = request.query_params.get('id')
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        )
    cursor.execute(
        "SELECT ul.login, " \
        "ul.create_dttm, " \
        "e.name, " \
        "e.description, " \
        "e.level, " \
        "e.loality " \
        "FROM user_login ul " \
        "JOIN executor e " \
        "ON ul.user_id = e.user_id " \
        "WHERE ul.user_id = %s",
        (userId,)
    )
    record = cursor.fetchone()
    if record is None:
        return Response("Неверный идентификатор пользователя", status=status.HTTP_404_NOT_FOUND)
    userData = [{
        "login": record[0],
        "date": record[1],
        "name": record[2],
        "description": record[3],
        "level": record[4],
        "loyality": record[5],
    }]
    return Response(userData)