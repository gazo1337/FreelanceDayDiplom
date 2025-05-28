from apps.task.enums.TaskStatus import TaskStatus, TaskStatusIn
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
from apps.task.serializers import TaskSerializer
from rest_framework.permissions import IsAuthenticated
from collections import namedtuple
import requests
import psycopg2

conn = psycopg2.connect(dbname='proj', user='postgres', 
                        password='postgres', host='localhost')
cursor = conn.cursor()

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
    ],
    request_body=TaskSerializer.TaskSerializer,
    responses={201: "Успех"}
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def create_task(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    user_id = None
    user_role = None
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        )
    response = requests.get(f"http://127.0.0.1:8000/adminPayment/getBalance/?id={user_id}&role={user_role}")
    balance = None
    if response.status_code == 200:
        balance = response.json()
    else:
         return JsonResponse({"error": "Внешний API недоступен"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    serializer = TaskSerializer.TaskSerializer(data=request.data)
    if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    val = serializer.validated_data
    if float(balance['balance'] < float(val['cost'])):
         return JsonResponse({"error": "Сумма на вашем счёте меньше, чем указанная стоимость задачи"}, status=status.HTTP_400_BAD_REQUEST)
    cursor.execute(
        """
        select task_id
        from task
        order by task_id desc limit 1
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
        insert into task
        values(%s, %s, %s, %s, %s, %s)
        """,
        [
            last_id,
            user_id,
            val['description'],
            val['complexity'],
            val['cost'],
            val['name']
        ]
    )
    conn.commit()
    cursor.execute(
        """
        insert into task_status
        values(%s, %s, %s, %s, %s, %s)
        """,
        [
            last_id,
            "CREATED",
            None,
            val['create_dttm'],
            val['create_dttm'],
            None
        ]
    )
    conn.commit()
    response = requests.post(f"http://127.0.0.1:8000/adminPayment/createCard/", json={
         "owner": last_id,
         "role": "task",
         "modify_dttm": str(val['create_dttm'])
    })
    if response.status_code != 200:
         return JsonResponse({"error": "Внешний API недоступен"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JsonResponse({"id": last_id})


@swagger_auto_schema(
    method='put',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'taskID',
            openapi.IN_QUERY,
            description="ID задачи для изменения статуса",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'taskStatus',
            openapi.IN_QUERY,
            description="Числовое значение статуса задачи",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'modifyDt',
            openapi.IN_QUERY,
            description="Дата изменения статуса",
            type=openapi.TYPE_INTEGER
        ),
    ],
    responses={201: "Успех"}
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def push_task(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
        
        print(f"Decoded token: user_id={user_id}, role={user_role}")  # Debug
        
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        ) 
    taskID = request.query_params.get('taskID')
    taskStatus = request.query_params.get('taskStatus')
    if int(taskStatus) not in TaskStatus:
         return JsonResponse(
            {"error": f"Указан некорректный статус задачи"},
            status=401
        )
    cursor.execute(
        "SELECT task_status FROM task_status WHERE task_id = %s ",
        (taskID,)
    )
    record = cursor.fetchone()
    if record is None:
        return Response("Задача по данному идентификатору не найдена", status=status.HTTP_404_NOT_FOUND)
    if TaskStatus[str(record[0])].value != int(taskStatus) - 1:
         return JsonResponse(
            {"error": f"Невозможно перевести задачу из статуса {str(record[0])} в статус {TaskStatusIn[int(taskStatus)]}"},
            status=401
        )
    cursor.execute(
         "UPDATE task_status SET task_status = %s WHERE task_id = '%s'",
         [TaskStatusIn[int(taskStatus)], int(taskID)]
    )
    conn.commit()
    return Response("Переведено")


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
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_tasks(request):
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
    
    if user_role != "executor":
         return JsonResponse(
              {"error": "Для вашей роли данный метод недоступен"},
              status=404
         )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT t.task_id, " \
         "t.task_name, " \
         "t.task_desc, " \
         "t.cost " \
         "FROM task t " \
         "JOIN task_status ts " \
         "ON t.task_id = ts.task_id " \
         "WHERE ts.task_status = 'CREATED'"\
         "order by t.task_id desc")

            columns = [col[0] for col in cursor.description]

            data = []
            for row in cursor.fetchall():
                data.append(dict(zip(columns, row)))
                
            return JsonResponse({
                'status': 'success',
                'count': len(data),
                'results': data
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'taskId', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_STRING
        ),
    ]
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def task(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    taskId = request.query_params.get('taskId')
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
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT t.task_id, " \
                "t.task_name, " \
                "t.task_desc, " \
                "t.cost, " \
                "t.task_initiator, " \
                "t.complexity, " \
                "ts.task_status, " \
                "ts.executor_id, " \
                "ts.create_dttm " \
                "FROM task t " \
                "JOIN task_status ts " \
                "ON t.task_id = ts.task_id " \
                "WHERE t.task_id = %s",
                (taskId,))

            columns = [col[0] for col in cursor.description]

            data = []
            for row in cursor.fetchall():
                data.append(dict(zip(columns, row)))
                
            return JsonResponse({
                'status': 'success',
                'count': len(data),
                'results': data
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'taskId', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'create', openapi.IN_QUERY,
            description="Дата отклика",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={201: "Успех"}
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['POST'])
def vote(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    user_id = None
    user_role = None
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
        
        print(f"Decoded token: user_id={user_id}, role={user_role}")  # Debug
        
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        )
    taskId = request.query_params.get('taskId')  
    create_dttm = request.query_params.get('create')    
    cursor.execute(
        """
        insert into task_votes
        values(%s, %s, %s, %s)
        """,
        [
            taskId,
            user_id,
            create_dttm,
            False
        ]
    )
    conn.commit()
    return Response("Отклик отправлен!")


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'taskId', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_STRING
        ),
    ]
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def getVotes(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    taskId = request.query_params.get('taskId')
    token = auth_header.split(' ')[0]
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
        
        print(f"Decoded token: user_id={user_id}, role={user_role}")  # Debug
        
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        ) 
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * " \
                "FROM task_votes tv " \
                "WHERE tv.task_id = %s",
                (taskId,))

            columns = [col[0] for col in cursor.description]

            data = []
            for row in cursor.fetchall():
                data.append(dict(zip(columns, row)))
                
            return JsonResponse({
                'status': 'success',
                'count': len(data),
                'results': data 
            })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@swagger_auto_schema(   
    method='put',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'taskId', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'userId', openapi.IN_QUERY,
            description="ID исполнителя",
            type=openapi.TYPE_STRING
        ),
    ],
    responses={201: "Успех"}
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['PUT'])
def setExecutor(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = auth_header.split(' ')[0]
    user_id = None
    user_role = None
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        )
    taskId = request.query_params.get('taskId')
    userId = request.query_params.get('userId')
    cursor.execute(
        """
        update task_status
        set executor_id = %s
        where task_id = %s
        """,
        [
            userId,
            taskId
        ]
    )
    conn.commit()
    return Response("Исполнитель назначен успешно!")


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'Authorization', openapi.IN_HEADER,
            description="Access Token",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'taskId', openapi.IN_QUERY,
            description="ID задачи",
            type=openapi.TYPE_STRING
        ),
    ]
)
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def ifVote(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    taskId = request.query_params.get('taskId')
    token = auth_header.split(' ')[0]
    try:
        decoded = AccessToken(token)
        user_id = decoded['user_id']
        user_role = decoded['role']
        
        print(f"Decoded token: user_id={user_id}, role={user_role}")  # Debug
        
    except (InvalidToken, TokenError) as e:
        return JsonResponse(
            {"error": f"Invalid token: {str(e)}"},
            status=401
        ) 
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * " \
                "FROM task_votes tv " \
                "WHERE tv.task_id = %s "
                "and tv.executor_id = %s",
                (taskId, user_id,))

            record = cursor.fetchone()
            if record is not None:
                return JsonResponse({'status': 'error', 'message': "Уже откликнулись"}, status=400)
            else:
                return Response("Ещё не откликались!")
                
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

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
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_ex_tasks(request):
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
    
    if user_role != "executor":
         return JsonResponse(
              {"error": "Для вашей роли данный метод недоступен"},
              status=404
         )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT t.task_id, " \
         "t.task_name, " \
         "t.task_desc, " \
         "t.cost " \
         "FROM task t " \
         "JOIN task_status ts " \
         "ON t.task_id = ts.task_id " \
         "join task_votes tv " \
         "on t.task_id = tv.task_id " \
         "WHERE (ts.task_status = 'CREATED' " \
         "and tv.executor_id = %s) " \
         "or (ts.task_status != 'ENDED' " \
         "and ts.executor_id = %s) "\
         "order by t.task_id desc",
         (user_id, user_id,))

            columns = [col[0] for col in cursor.description]

            data = []
            for row in cursor.fetchall():
                data.append(dict(zip(columns, row)))
                
            return JsonResponse({
                'status': 'success',
                'count': len(data),
                'results': data
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    
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
@authentication_classes([JWTAuthentication]) 
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def get_emp_tasks(request):
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
    
    if user_role != "employer":
         return JsonResponse(
              {"error": "Для вашей роли данный метод недоступен"},
              status=404
         )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT t.task_id, " \
         "t.task_name, " \
         "t.task_desc, " \
         "t.cost " \
         "FROM task t " \
         "JOIN task_status ts " \
         "ON t.task_id = ts.task_id " \
         "WHERE ts.task_status != 'ENDED' " \
         "and t.task_initiator = %s " \
         "order by t.task_id desc",
         (user_id,))

            columns = [col[0] for col in cursor.description]

            data = []
            for row in cursor.fetchall():
                data.append(dict(zip(columns, row)))
                
            return JsonResponse({
                'status': 'success',
                'count': len(data),
                'results': data
            })    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    