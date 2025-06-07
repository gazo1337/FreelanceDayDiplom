from django.db import models
from models import Task, TaskStatus, TaskVote

class TaskManager(models.Manager):
    def create_task(self, user, validated_data):
        from django.utils import timezone
        
        task = self.create(
            task_initiator=user,
            task_desc=validated_data['description'],
            complexity=validated_data['complexity'],
            cost=validated_data['cost'],
            task_name=validated_data['name']
        )
        
        TaskStatus.objects.create(
            task=task,
            task_status='CREATED',
            executor=None,
            create_dttm=validated_data['create_dttm'],
            modify_dttm=validated_data['create_dttm'],
            end_dttm=None
        )
        
        return task

class TaskStatusManager(models.Manager):
    def update_status(self, task_id, new_status, modify_dttm):
        from apps.task.enums import TaskStatus, TaskStatusIn
        
        task_status = self.get(task_id=task_id)
        current_status = task_status.task_status
        
        if TaskStatus[current_status].value != TaskStatus[new_status].value - 1:
            raise ValueError(f"Невозможно перевести задачу из статуса {current_status} в статус {new_status}")
        
        task_status.task_status = new_status
        task_status.modify_dttm = modify_dttm
        task_status.save()
        
        return task_status
    