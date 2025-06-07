from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class PaymentAcc(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    modify_dttm = models.DateTimeField()
    card_id = models.IntegerField(primary_key=True)
    owner_id = models.IntegerField()
    role = models.CharField(max_length=20)

    class Meta:
        db_table = 'payment_acc'

    @classmethod
    def create_virtual_card(cls, modify_dttm, owner_id, role):
        last_card = cls.objects.order_by('-card_id').first()
        new_card_id = 0 if last_card is None else last_card.card_id + 1
        
        return cls.objects.create(
            balance=0.00,
            modify_dttm=modify_dttm,
            card_id=new_card_id,
            owner_id=owner_id,
            role=role
        )

    @classmethod
    def get_balance(cls, owner_id, role):
        try:
            account = cls.objects.get(owner_id=owner_id, role=role)
            return float(account.balance)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def update_employer_balance(cls, employer_id, amount):
        cls.objects.filter(owner_id=employer_id, role='employer').update(
            balance=models.F('balance') + amount
        )

    @classmethod
    def update_task_balance(cls, task_id, amount):
        cls.objects.filter(owner_id=task_id, role='task').update(
            balance=models.F('balance') + amount
        )

    @classmethod
    def update_executor_balance(cls, executor_id, amount):
        cls.objects.filter(owner_id=executor_id, role='executor').update(
            balance=models.F('balance') + amount
        )


class PaymentOperations(models.Model):
    payment_id = models.IntegerField(primary_key=True)
    reciever_id = models.IntegerField()
    count = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    initiator = models.IntegerField(null=True, blank=True)
    task_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'payment_operations'

    @classmethod
    def get_last_payment_id(cls):
        last_payment = cls.objects.order_by('-payment_id').first()
        return 0 if last_payment is None else last_payment.payment_id + 1

    @classmethod
    def create_operation(cls, payment_id, reciever_id, count, date, initiator=None, task_id=None):
        return cls.objects.create(
            payment_id=payment_id,
            reciever_id=reciever_id,
            count=count,
            date=date,
            initiator=initiator,
            task_id=task_id
        )

    @classmethod
    def get_user_operations(cls, user_id):
        return cls.objects.filter(
            models.Q(reciever_id=user_id) & ~models.Q(task_id=user_id) |
            models.Q(initiator=user_id) & ~models.Q(task_id=user_id)
        ).order_by('-payment_id')