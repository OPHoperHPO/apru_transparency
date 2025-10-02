from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
class Command(BaseCommand):
    help = "Create/update demo users for roles"
    def handle(self, *args, **kwargs):
        User = get_user_model()
        demo = [
            (os.environ.get("DEMO_ADMIN_USER", "admin"), os.environ.get("DEMO_ADMIN_PASS", "admin123"), "admin"),
            (os.environ.get("DEMO_REG_USER", "reg"), os.environ.get("DEMO_REG_PASS", "reg123"), "regulator"),
            (os.environ.get("DEMO_OWNER_USER", "owner"), os.environ.get("DEMO_OWNER_PASS", "owner123"), "owner"),
            (os.environ.get("DEMO_USER_USER", "user"), os.environ.get("DEMO_USER_PASS", "user123"), "user"),
        ]
        for username, password, role in demo:
            u, created = User.objects.get_or_create(username=username, defaults={"role": role})
            if not created:
                u.role = role
            u.set_password(password)
            u.is_staff = (role == "admin")
            u.is_superuser = (role == "admin")
            u.save()
            self.stdout.write(self.style.SUCCESS(f"{username}:{password} ({role})"))
