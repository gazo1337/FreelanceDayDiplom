from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from .models import Task, TaskStatus, TaskVote
from .serializers import TaskSerializers
from apps.administration.models import User
import requests
from django.db import models
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import datetime

def check_balance(user_id, role, cost):
    try:
        response = requests.get(
            "http://127.0.0.1:8000/adminPayment/getBalance/",
            params={'id': user_id, 'role': role},
            timeout=5
        )
        response.raise_for_status()
        balance = float(response.json().get('balance', 0))
        if balance < float(cost):
            raise ValueError(f"Недостаточно средств на счете. Текущий баланс: {balance}, требуется: {cost}")
        return True
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Ошибка подключения к платежной системе: {str(e)}")
    except ValueError as e:
        raise
    except Exception as e:
        raise ConnectionError(f"Неизвестная ошибка при проверке баланса: {str(e)}")

def create_payment_card(task_id, create_dttm):
    try:
        response = requests.post(
            "http://127.0.0.1:8000/adminPayment/createCard/",
            json={
                "owner": task_id,
                "role": "task",
                "modify_dttm": str(create_dttm)
            },
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Ошибка создания платежной карты: {str(e)}")
    except Exception as e:
        raise ConnectionError(f"Неизвестная ошибка при создании карты: {str(e)}")

@swagger_auto_schema(
    method='post',
    operation_description="Создание новой задачи",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'task_name': openapi.Schema(type=openapi.TYPE_STRING, description="Название задачи"),
            'task_desc': openapi.Schema(type=openapi.TYPE_STRING, description="Описание задачи"),
            'cost': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Стоимость задачи"),
            'complexity': openapi.Schema(type=openapi.TYPE_STRING, description="Сложность задачи"),
            'create_dttm': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Дата создания"),
        },
        required=['task_name', 'task_desc', 'cost', 'create_dttm']
    ),
    responses={
        201: openapi.Response("Успешное создание", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID созданной задачи")}
        )),
        400: openapi.Response("Неверные данные", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
        )),
        403: openapi.Response("Доступ запрещен", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
        )),
        500: openapi.Response("Ошибка сервера", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}
        ))
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_task(request):
    try:
        if request.user.role != "employer":
            return JsonResponse(
                {"error": "Только пользователи с ролью 'employer' могут создавать задачи"}, 
                status=403
            )
            
        serializer = TaskSerializers.TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        check_balance(request.user.id, request.user.role, serializer.validated_data['cost'])
        task = Task.create_with_status(request.user.id, serializer.validated_data)
        create_payment_card(task.task_id, serializer.validated_data['create_dttm'])
        
        return JsonResponse({"id": task.task_id}, status=201)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except ConnectionError as e:
        return JsonResponse({"error": str(e)}, status=503)
    except Exception as e:
        print("Request data:", request.data) 
        print(str(e))
        return JsonResponse({"error": f"Ошибка при создании задачи: {str(e)}"}, status=500)

@swagger_auto_schema(
    method='put',
    operation_description="Изменение статуса задачи",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'taskID', 
            openapi.IN_QUERY, 
            description="ID задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'taskStatus', 
            openapi.IN_QUERY, 
            description="Новый статус задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'modifyDt', 
            openapi.IN_QUERY, 
            description="Дата изменения в формате YYYY-MM-DDTHH:MM:SS", 
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=True
        )
    ],
    responses={
        200: openapi.Response("Успешное изменение", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
        )),
        400: openapi.Response("Неверные данные", examples={
            "application/json": {"error": "Описание ошибки"}
        }),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Нет прав на изменение этой задачи"}
        }),
        404: openapi.Response("Задача не найдена", examples={
            "application/json": {"error": "Задача с указанным ID не найдена"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Внутренняя ошибка сервера"}
        })
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def push_task(request):
    try:
        task_id = request.query_params.get('taskID')
        new_status = request.query_params.get('taskStatus')
        modify_dt = request.query_params.get('modifyDt')

        if not all([task_id, new_status, modify_dt]):
            return JsonResponse(
                {"error": "Необходимо указать taskID, taskStatus и modifyDt"}, 
                status=400
            )

        try:
            datetime.fromisoformat(modify_dt)
        except ValueError:
            return JsonResponse(
                {"error": "Неверный формат даты. Используйте формат YYYY-MM-DDTHH:MM:SS"}, 
                status=400
            )

        task_status = get_object_or_404(TaskStatus, task_id=int(task_id)) 
        print("ok")
        
        task_status.update_status(int(new_status), modify_dt)
        print("ok")
        return JsonResponse(
            {"message": "Статус задачи успешно обновлен"}, 
            status=200
        )
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при обновлении статуса: {str(e)}"}, 
            status=400
        )

@swagger_auto_schema(
    method='get',
    operation_description="Получение списка доступных задач для исполнителя",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Список задач",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'task_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'task_desc': openapi.Schema(type=openapi.TYPE_STRING),
                                'cost': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        )
                    )
                }
            )
        ),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Доступ разрешен только исполнителям"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при получении списка задач"}
        })
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_tasks(request):
    try:
        if request.user.role != "executor":
            return JsonResponse(
                {"error": "Доступ разрешен только пользователям с ролью 'executor'"}, 
                status=403
            )
        
        tasks = Task.objects.filter(
            taskstatus__task_status='CREATED'
        ).values('task_id', 'task_name', 'task_desc', 'cost').order_by('-task_id')
        
        return JsonResponse({
            'status': 'success', 
            'count': len(tasks), 
            'results': list(tasks)
        })
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при получении списка задач: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='get',
    operation_description="Получение деталей задачи",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'taskId', 
            openapi.IN_QUERY, 
            description="ID задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Детали задачи",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'results': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'task_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'task_desc': openapi.Schema(type=openapi.TYPE_STRING),
                            'cost': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'task_initiator_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'complexity': openapi.Schema(type=openapi.TYPE_STRING),
                            'taskstatus__task_status': openapi.Schema(type=openapi.TYPE_STRING),
                            'taskstatus__executor_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'taskstatus__create_dttm': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                }
            )
        ),
        400: openapi.Response("Неверные данные", examples={
            "application/json": {"error": "Не указан ID задачи"}
        }),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Нет прав доступа к этой задаче"}
        }),
        404: openapi.Response("Задача не найдена", examples={
            "application/json": {"error": "Задача с указанным ID не найдена"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при получении данных задачи"}
        })
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def task(request):
    try:
        task_id = request.query_params.get('taskId')
        if not task_id:
            return JsonResponse(
                {"error": "Необходимо указать taskId в параметрах запроса"}, 
                status=400
            )

        task_data = Task.objects.filter(
            task_id=task_id
        ).select_related('taskstatus').values(
            'task_id', 'task_name', 'task_desc', 'cost', 'task_initiator_id', 
            'complexity', 'taskstatus__task_status', 'taskstatus__executor_id', 
            'taskstatus__create_dttm'
        ).first()
        
        if not task_data:
            return JsonResponse(
                {"error": f"Задача с ID {task_id} не найдена"}, 
                status=404
            )
            
        return JsonResponse({
            'status': 'success', 
            'results': task_data
        })
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при получении данных задачи: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='post',
    operation_description="Создание отклика на задачу",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'taskId', 
            openapi.IN_QUERY, 
            description="ID задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'create', 
            openapi.IN_QUERY, 
            description="Дата создания отклика в формате YYYY-MM-DDTHH:MM:SS", 
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=True
        )
    ],
    responses={
        201: openapi.Response("Успешное создание", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
        )),
        400: openapi.Response("Неверные данные", examples={
            "application/json": {"error": "Не указаны обязательные параметры"}
        }),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Только исполнители могут оставлять отклики"}
        }),
        409: openapi.Response("Конфликт", examples={
            "application/json": {"error": "Отклик на эту задачу уже существует"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при создании отклика"}
        })
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def vote(request):
    try:
        if request.user.role != "executor":
            return JsonResponse(
                {"error": "Только пользователи с ролью 'executor' могут оставлять отклики"}, 
                status=403
            )

        task_id = request.query_params.get('taskId')
        create_dttm = request.query_params.get('create')

        if not all([task_id, create_dttm]):
            return JsonResponse(
                {"error": "Необходимо указать taskId и create в параметрах запроса"}, 
                status=400
            )

        try:
            datetime.fromisoformat(create_dttm)
        except ValueError:
            return JsonResponse(
                {"error": "Неверный формат даты. Используйте формат YYYY-MM-DDTHH:MM:SS"}, 
                status=400
            )

        if TaskVote.objects.filter(task_id=task_id, executor_id=request.user.id).exists():
            return JsonResponse(
                {"error": "Вы уже оставляли отклик на эту задачу"}, 
                status=409
            )

        TaskVote.create_vote(task_id, request.user.id, create_dttm)
        return JsonResponse(
            {"message": "Отклик успешно создан"}, 
            status=201
        )
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при создании отклика: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='get',
    operation_description="Получение списка откликов на задачу",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'taskId', 
            openapi.IN_QUERY, 
            description="ID задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Список откликов",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'executor_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'create_dttm': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_selected': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        )
                    )
                }
            )
        ),
        400: openapi.Response("Неверные данные", examples={
            "application/json": {"error": "Не указан ID задачи"}
        }),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Вы не являетесь создателем задачи"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при получении списка откликов"}
        })
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getVotes(request):
    try:
        task_id = request.query_params.get('taskId')
        if not task_id:
            return JsonResponse(
                {"error": "Необходимо указать taskId в параметрах запроса"}, 
                status=400
            )

        task = get_object_or_404(Task, task_id=task_id)
        if task.task_initiator_id != request.user.id:
            return JsonResponse(
                {"error": "Только создатель задачи может просматривать отклики"}, 
                status=403
            )

        votes = TaskVote.objects.filter(
            task_id=task_id
        ).values('task_id', 'executor_id', 'create_dttm', 'is_selected')
        
        return JsonResponse({
            'status': 'success', 
            'count': len(votes), 
            'results': list(votes)
        })
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при получении списка откликов: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='put',
    operation_description="Назначение исполнителя для задачи",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'taskId', 
            openapi.IN_QUERY, 
            description="ID задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'userId', 
            openapi.IN_QUERY, 
            description="ID пользователя-исполнителя", 
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response("Успешное назначение", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
        )),
        400: openapi.Response("Неверные данные", examples={
            "application/json": {"error": "Не указаны обязательные параметры"}
        }),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Только создатель задачи может назначать исполнителя"}
        }),
        404: openapi.Response("Не найдено", examples={
            "application/json": {"error": "Задача или пользователь не найдены"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при назначении исполнителя"}
        })
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def setExecutor(request):
    try:
        task_id = request.query_params.get('taskId')
        user_id = request.query_params.get('userId')

        if not all([task_id, user_id]):
            return JsonResponse(
                {"error": "Необходимо указать taskId и userId в параметрах запроса"}, 
                status=400
            )

        task = get_object_or_404(Task, task_id=task_id)
        if task.task_initiator_id != request.user.id:
            return JsonResponse(
                {"error": "Только создатель задачи может назначать исполнителя"}, 
                status=403
            )

        executor = get_object_or_404(User, id=user_id)
        if executor.role != "executor":
            return JsonResponse(
                {"error": "Указанный пользователь не является исполнителем"}, 
                status=400
            )

        if not TaskVote.objects.filter(task_id=task_id, executor_id=user_id).exists():
            return JsonResponse(
                {"error": "Указанный пользователь не оставлял отклик на эту задачу"}, 
                status=400
            )

        task_status = TaskStatus.objects.get(task_id=task_id)
        task_status.executor_id = user_id
        task_status.save()

        TaskVote.objects.filter(
            task_id=task_id, 
            executor_id=user_id
        ).update(is_selected=True)

        return JsonResponse(
            {"message": "Исполнитель успешно назначен"}, 
            status=200
        )
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при назначении исполнителя: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='get',
    operation_description="Проверка наличия отклика от текущего пользователя",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'taskId', 
            openapi.IN_QUERY, 
            description="ID задачи", 
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Результат проверки",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'has_vote': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Наличие отклика")
                }
            )
        ),
        400: openapi.Response("Неверные данные", examples={
            "application/json": {"error": "Не указан ID задачи"}
        }),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Только исполнители могут проверять отклики"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при проверке отклика"}
        })
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def ifVote(request):
    try:
        task_id = request.query_params.get('taskId')
        if not task_id:
            return JsonResponse(
                {"error": "Необходимо указать taskId в параметрах запроса"}, 
                status=400
            )

        exists = TaskVote.objects.filter(
            task_id=task_id,
            executor_id=request.user.id
        ).exists()
        
        return JsonResponse({'has_vote': exists})
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при проверке отклика: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='get',
    operation_description="Получение списка задач исполнителя",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Список задач",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'task_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'task_desc': openapi.Schema(type=openapi.TYPE_STRING),
                                'cost': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        )
                    )
                }
            )
        ),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Доступ разрешен только исполнителям"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при получении списка задач"}
        })
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_ex_tasks(request):
    try:
        if request.user.role != "executor":
            return JsonResponse(
                {"error": "Доступ разрешен только пользователям с ролью 'executor'"}, 
                status=403
            )
        
        tasks = Task.objects.filter(
            models.Q(taskstatus__task_status='CREATED', taskvote__executor_id=request.user.id) |
            models.Q(taskstatus__task_status__in=['IN_PROGRESS', 'ON_END'], taskstatus__executor_id=request.user.id)
        ).distinct().values('task_id', 'task_name', 'task_desc', 'cost').order_by('-task_id')
        
        return JsonResponse({
            'status': 'success', 
            'count': len(tasks), 
            'results': list(tasks)
        })
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при получении списка задач: {str(e)}"}, 
            status=500
        )

@swagger_auto_schema(
    method='get',
    operation_description="Получение списка задач заказчика",
    manual_parameters=[
        openapi.Parameter(
            'Authorization', 
            openapi.IN_HEADER, 
            description="JWT токен в формате 'Bearer {token}'", 
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Список задач",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'task_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'task_desc': openapi.Schema(type=openapi.TYPE_STRING),
                                'cost': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        )
                    )
                }
            )
        ),
        403: openapi.Response("Доступ запрещен", examples={
            "application/json": {"error": "Доступ разрешен только заказчикам"}
        }),
        500: openapi.Response("Ошибка сервера", examples={
            "application/json": {"error": "Ошибка при получении списка задач"}
        })
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_emp_tasks(request):
    try:
        if request.user.role != "employer":
            return JsonResponse(
                {"error": "Доступ разрешен только пользователям с ролью 'employer'"}, 
                status=403
            )
        
        tasks = Task.objects.filter(
            task_initiator_id=request.user.id,
            taskstatus__task_status__in=['CREATED', 'IN_PROGRESS', 'ON_END']
        ).values('task_id', 'task_name', 'task_desc', 'cost').order_by('-task_id')
        
        return JsonResponse({
            'status': 'success', 
            'count': len(tasks), 
            'results': list(tasks)
        })
    except Exception as e:
        return JsonResponse(
            {"error": f"Ошибка при получении списка задач: {str(e)}"}, 
            status=500
        )