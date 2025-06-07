from django.db import models
from django.core.exceptions import ValidationError

class Task(models.Model):
    STATUS_CHOICES = (
        ('CREATED', 'Создана'),
        ('IN_PROGRESS', 'В работе'),
        ('ON_END', 'Завершена'),
        ('ENDED', 'Окончена'),
    )
    
    task_id = models.AutoField(primary_key=True)
    task_initiator_id = models.IntegerField()
    task_desc = models.TextField()
    complexity = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    task_name = models.CharField(max_length=255)
    create_dttm = models.DateTimeField()
    
    class Meta:
        db_table = 'task'
        app_label = 'task'
    
    @classmethod
    def create_with_status(cls, initiator_id, validated_data):
        """
        Создает задачу с начальным статусом
        initiator_id - ID пользователя из внешней системы
        """
        task = cls.objects.create(
            task_initiator_id=initiator_id,
            task_desc=validated_data['task_desc'],
            complexity=validated_data['complexity'],
            cost=validated_data['cost'],
            task_name=validated_data['task_name'],
            create_dttm=validated_data['create_dttm']
        )
        TaskStatus.objects.create(
            task=task,
            task_status='CREATED',
            create_dttm=validated_data['create_dttm'],
            modify_dttm=validated_data['create_dttm']
        )
        return task

class TaskStatus(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, primary_key=True)
    task_status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES)
    executor_id = models.IntegerField(null=True, blank=True)
    create_dttm = models.DateTimeField()
    modify_dttm = models.DateTimeField()
    end_dttm = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'task_status'
        app_label = 'task'
    
    def update_status(self, new_status, modify_dttm):
        """
        Обновляет статус задачи с проверкой допустимости перехода
        """
        current_status_value = self.get_status_value_int(self.task_status)
        new_status_value = self.get_status_value(new_status)
        
        if new_status != current_status_value + 1:
            raise ValidationError(
                f"Невозможно перевести задачу из статуса {self.task_status} в статус {new_status_value}"
            )
        
        self.task_status = new_status_value
        self.modify_dttm = modify_dttm
        self.save()
    
    @staticmethod
    def get_status_value(status):
        status_order = ['CREATED', 'IN_PROGRESS', 'ON_END', 'ENDED']
        return status_order[status]
    
    @staticmethod
    def get_status_value_int(status):
        status_order = ['CREATED', 'IN_PROGRESS', 'ON_END', 'ENDED']
        return status_order.index(status)

class TaskVote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    executor_id = models.IntegerField()
    create_dttm = models.DateTimeField()
    is_selected = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'task_votes'
        app_label = 'task'
        constraints = [
            models.UniqueConstraint(fields=['task', 'executor_id'], name='unique_task_executor')
        ]
    
    @classmethod
    def create_vote(cls, task_id, executor_id, create_dttm):
        """
        Создает отклик на задачу с проверкой уникальности
        """
        vote, created = cls.objects.get_or_create(
            task_id=task_id,
            executor_id=executor_id,
            defaults={'create_dttm': create_dttm}
        )
        if not created:
            raise ValidationError("Вы уже откликались на эту задачу")
        return vote