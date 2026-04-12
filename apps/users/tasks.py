from celery import shared_task
from django.core.mail import send_mail

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email(user_email: str):
    send_mail(
        subject="Welcome to Blog API",
        message="Thanks for registering in Blog API.",
        from_email=None,
        recipient_list=[user_email],
        fail_silently=False,
    )