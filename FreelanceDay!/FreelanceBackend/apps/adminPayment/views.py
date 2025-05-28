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
from apps.adminPayment.serializers import VirtualCardSerializer
from rest_framework.permissions import IsAuthenticated
from collections import namedtuple
import psycopg2

conn = psycopg2.connect(dbname='ap', user='postgres', 
                        password='postgres', host='localhost')
cursor = conn.cursor()

@swagger_auto_schema(
    method='post',
    request_body=VirtualCardSerializer.VirtualCardSerializer,
    responses={201: "Успех"}
)
@api_view(['POST'])
def create_card(request):
    serializer = VirtualCardSerializer.VirtualCardSerializer(data=request.data)
    if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    val = serializer.validated_data
    cursor.execute(
        """
        select card_id
        from payment_acc
        order by card_id desc limit 1
        """
    )
    result = cursor.fetchone()
    last_id = None
    if result is None:
          last_id = 0
    else:
        last_id = int(result[0]) + 1
    cursor.execute(
        """
        insert into payment_acc
        values(0.00, %s, %s, %s, %s)
        """,
        [
            val['modify_dttm'],
            last_id,
            val['owner'],
            val['role']
        ]
    )
    conn.commit()
    return Response("Виртуальный счёт создан!")


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'id', openapi.IN_QUERY,
            description="ID пользователя",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'role', openapi.IN_QUERY,
            description="Роль пользователя",
            type=openapi.TYPE_STRING
        ),
    ]
)
@api_view(['GET'])
def getBalance(request):
    userId = request.query_params.get('id')
    userRole = request.query_params.get('role')
    cursor.execute(
        "SELECT balance FROM payment_acc WHERE owner_id = %s and role = %s",
        [userId, userRole]
    )
    record = cursor.fetchone()
    if record is None:
        return Response("Виртуальный счёт не найден", status=status.HTTP_404_NOT_FOUND)
    return JsonResponse({"balance": record[0]})


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'id', openapi.IN_QUERY,
            description="ID заказчика",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'count', openapi.IN_QUERY,
            description="Сумма",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date', openapi.IN_QUERY,
            description="Дата операции",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def toEmloyer(request):
    emId = request.query_params.get('id')
    count = request.query_params.get('count')
    date = request.query_params.get('date')
    cursor.execute(
        """
        select payment_id
        from payment_operations
        order by payment_id desc limit 1
        """
    )
    result = cursor.fetchone()
    last_id = None
    if result is None:
          last_id = 0
    else:
        last_id = int(result[0]) + 1
    cursor.execute(
        """
        update payment_acc
        set balance = balance + %s
        where owner_id = %s
        and role = 'employer'
        """,
        [
            count,
            emId
        ]
    )
    conn.commit()
    cursor.execute(
        """
        insert into payment_operations
        values(%s, %s, %s, %s, null, null)
        """,
        [
            last_id,
            emId,
            count,
            date
        ]
    )
    conn.commit()
    return Response("Операция проведена успешно, счёт пополнен!")


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'EmployerID', openapi.IN_QUERY,
            description="ID заказчика",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'TaskID', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'count', openapi.IN_QUERY,
            description="Сумма",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date', openapi.IN_QUERY,
            description="Дата операции",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def toTask(request):
    emId = request.query_params.get('EmployerID')
    tId = request.query_params.get('TaskID')
    count = request.query_params.get('count')
    date = request.query_params.get('date')
    cursor.execute(
        """
        select payment_id
        from payment_operations
        order by payment_id desc limit 1
        """
    )
    result = cursor.fetchone()
    last_id = None
    if result is None:
          last_id = 0
    else:
        last_id = int(result[0]) + 1
    cursor.execute(
        """
        update payment_acc
        set balance = balance - %s
        where owner_id = %s
        and role = 'employer'
        """,
        [
            count,
            emId
        ]
    )
    conn.commit()
    cursor.execute(
        """
        update payment_acc
        set balance = balance + %s
        where owner_id = %s
        and role = 'task'
        """,
        [
            count,  
            emId
        ]
    )
    conn.commit()
    cursor.execute(
        """
        insert into payment_operations
        values(%s, %s, %s, %s, %s, %s)
        """,
        [
            last_id,
            tId,
            count,
            date,
            emId,
            tId
        ]
    )
    conn.commit()
    return Response("Операция проведена успешно, счёт пополнен!")


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'ExecutorID', openapi.IN_QUERY,
            description="ID исполнителя",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'TaskID', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'count', openapi.IN_QUERY,
            description="Сумма",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date', openapi.IN_QUERY,
            description="Дата операции",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def toExecutor(request):
    exId = request.query_params.get('ExecutorID')
    tId = request.query_params.get('TaskID')
    count = request.query_params.get('count')
    date = request.query_params.get('date')
    cursor.execute(
        """
        select payment_id
        from payment_operations
        order by payment_id desc limit 1
        """
    )
    result = cursor.fetchone()
    last_id = None
    if result is None:
          last_id = 0
    else:
        last_id = int(result[0]) + 1
    cursor.execute(
        """
        update payment_acc
        set balance = balance - %s
        where owner_id = %s
        and role = 'task'
        """,
        [
            count,
            tId
        ]
    )
    conn.commit()
    cursor.execute(
        """
        update payment_acc
        set balance = balance + %s
        where owner_id = %s
        and role = 'executor'
        """,
        [
            count,  
            exId
        ]
    )
    conn.commit()
    cursor.execute(
        """
        insert into payment_operations
        values(%s, %s, %s, %s, %s, %s)
        """,
        [
            last_id,
            exId,
            count,
            date,
            tId,
            tId
        ]
    )
    conn.commit()
    return Response("Операция проведена успешно, счёт пополнен!")


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'TaskID', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'count', openapi.IN_QUERY,
            description="Сумма",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date', openapi.IN_QUERY,
            description="Дата операции",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def fromExecutor(request):
    exId = request.query_params.get('ExecutorID')
    count = request.query_params.get('count')
    date = request.query_params.get('date')
    cursor.execute(
        """
        select payment_id
        from payment_operations
        order by payment_id desc limit 1
        """
    )
    result = cursor.fetchone()
    last_id = None
    if result is None:
          last_id = 0
    else:
        last_id = int(result[0]) + 1
    cursor.execute(
        """
        update payment_acc
        set balance = balance - %s
        where owner_id = %s
        and role = 'executor'
        """,
        [
            count,  
            exId
        ]
    )
    conn.commit()
    cursor.execute(
        """
        insert into payment_operations
        values(%s, %s, %s, %s, %s, %s)
        """,
        [
            last_id,
            0,
            count,
            date,
            exId,
            0
        ]
    )
    conn.commit()
    return Response("Операция проведена успешно, счёт пополнен!")


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'id', openapi.IN_QUERY,
            description="ID пользователя",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'role', openapi.IN_QUERY,
            description="Роль пользователя",
            type=openapi.TYPE_STRING
        ),
    ]
)
@api_view(['GET'])
def getOperations(request):
    userId = request.query_params.get('id')
    userRole = request.query_params.get('role')
    cursor.execute(
        "SELECT * FROM payment_operations " \
        "WHERE (reciever_id = %s and task_id != %s) "
        "or (initiator = %s and task_id != %s)"
        "order by payment_id desc",
        [userId, userId, userId, userId, ]
    )
    columns = [col[0] for col in cursor.description]
    if columns is None:
         return JsonResponse({
        'status': 'none'
    }, status=status.HTTP_404_NOT_FOUND)
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
        
    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'results': data
    })