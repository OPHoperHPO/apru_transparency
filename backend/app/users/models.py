from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        REGULATOR = "regulator", "Regulator"
        OWNER = "owner", "Business Owner"
        USER = "user", "User"
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser
