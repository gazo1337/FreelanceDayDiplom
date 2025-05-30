from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = [
        ('employer', 'Работодатель'),
        ('executor', 'Исполнитель'),
    ]

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['email', 'username', 'role']
    
    login = models.CharField(
        _('login'),
        max_length=30,
        unique=True,
        help_text=_('Required. 30 characters or fewer. Used for authentication.'),
        error_messages={
            'unique': _("A user with that login already exists."),
        },
    )
    
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=False,
        help_text=_('Required. 150 characters or fewer. Displayed as user name.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_login'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username 


class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'employer'


class Executor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    level = models.IntegerField(default=0)
    loyalty = models.IntegerField(default=0)
    rating = models.FloatField(default=0)
    completed_orders = models.IntegerField(default=0)

    class Meta:
        db_table = 'executor'