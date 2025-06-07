from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import PaymentAcc, PaymentOperations
from .serializers import VirtualCardSerializer

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
    PaymentAcc.create_virtual_card(
        modify_dttm=val['modify_dttm'],
        owner_id=val['owner'],
        role=val['role']
    )
    
    return Response("Виртуальный счёт создан!")

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('role', openapi.IN_QUERY, type=openapi.TYPE_STRING),
    ]
)
@api_view(['GET'])
def getBalance(request):
    userId = request.query_params.get('id')
    userRole = request.query_params.get('role')
    
    balance = PaymentAcc.get_balance(owner_id=userId, role=userRole)
    if balance is None:
        return Response("Виртуальный счёт не найден", status=status.HTTP_404_NOT_FOUND)
    
    return JsonResponse({"balance": balance})

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('count', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def toEmloyer(request):
    emId = request.query_params.get('id')
    count = float(request.query_params.get('count'))
    date = request.query_params.get('date')
    
    PaymentAcc.update_employer_balance(employer_id=emId, amount=count)
    PaymentOperations.create_operation(
        payment_id=PaymentOperations.get_last_payment_id(),
        reciever_id=emId,
        count=count,
        date=date
    )
    
    return Response("Операция проведена успешно, счёт пополнен!")

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('EmployerID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('TaskID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('count', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def toTask(request):
    emId = request.query_params.get('EmployerID')
    tId = request.query_params.get('TaskID')
    count = float(request.query_params.get('count'))
    date = request.query_params.get('date')
    
    PaymentAcc.update_employer_balance(employer_id=emId, amount=-count)
    PaymentAcc.update_task_balance(task_id=tId, amount=count)
    PaymentOperations.create_operation(
        payment_id=PaymentOperations.get_last_payment_id(),
        reciever_id=tId,
        count=count,
        date=date,
        initiator=emId,
        task_id=tId
    )
    
    return Response("Операция проведена успешно, счёт пополнен!")

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('ExecutorID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('TaskID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('count', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def toExecutor(request):
    exId = request.query_params.get('ExecutorID')
    tId = request.query_params.get('TaskID')
    count = float(request.query_params.get('count'))
    date = request.query_params.get('date')
    
    PaymentAcc.update_task_balance(task_id=tId, amount=-count)
    PaymentAcc.update_executor_balance(executor_id=exId, amount=count)
    PaymentOperations.create_operation(
        payment_id=PaymentOperations.get_last_payment_id(),
        reciever_id=exId,
        count=count,
        date=date,
        initiator=tId,
        task_id=tId
    )
    
    return Response("Операция проведена успешно, счёт пополнен!")

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('ExecutorID', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('count', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING),
    ],
    responses={201: "Успех"}
)
@api_view(['POST'])
def fromExecutor(request):
    exId = request.query_params.get('ExecutorID')
    count = float(request.query_params.get('count'))
    date = request.query_params.get('date')
    
    PaymentAcc.update_executor_balance(executor_id=exId, amount=-count)
    PaymentOperations.create_operation(
        payment_id=PaymentOperations.get_last_payment_id(),
        reciever_id=0,
        count=count,
        date=date,
        initiator=exId,
        task_id=0
    )
    
    return Response("Операция проведена успешно, счёт пополнен!")

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('role', openapi.IN_QUERY, type=openapi.TYPE_STRING),
    ]
)
@api_view(['GET'])
def getOperations(request):
    userId = request.query_params.get('id')
    
    operations = PaymentOperations.get_user_operations(user_id=userId)
    if not operations.exists():
        return JsonResponse({'status': 'none'}, status=status.HTTP_404_NOT_FOUND)
    
    data = [{
        'payment_id': op.payment_id,
        'reciever_id': op.reciever_id,
        'count': float(op.count),
        'date': op.date,
        'initiator': op.initiator,
        'task_id': op.task_id
    } for op in operations]
        
    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'results': data
    })