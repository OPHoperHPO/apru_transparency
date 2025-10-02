from django.core.management.base import BaseCommand
from app.processing.models import Worker
import os
class Command(BaseCommand):
    help = "Create or update a demo worker using WORKER_BOOTSTRAP_TOKEN env"
    def handle(self, *args, **kwargs):
        token = os.environ.get("WORKER_BOOTSTRAP_TOKEN")
        if not token:
            self.stdout.write(self.style.WARNING("WORKER_BOOTSTRAP_TOKEN not set; skipping"))
            return
        w, created = Worker.objects.get_or_create(name="default-worker", defaults={"token": token})
        if not created:
            w.token = token
            w.is_active = True
            w.save(update_fields=["token","is_active"])
        self.stdout.write(self.style.SUCCESS(f"Worker ready: {w.name}"))
