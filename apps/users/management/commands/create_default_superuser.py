from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

class Command(BaseCommand):
    help = "Create default superuser if it does not exist"

    def handle(self, *args, **options):
        email = "beka181296@gmail.com"
        password = "12345678"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Aibek",
                "last_name": "Mannapov",
                "is_staff": True,
                "is_superuser": True,
                "preferred_language": "en",
                "timezone": "UTC",
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS("Default superuser created"))
        else:
            self.stdout.write(self.style.WARNING("Default superuser already exists"))