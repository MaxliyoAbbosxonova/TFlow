from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_user_email(result,email):
    send_mail(
        f"{result['code']}",
        "This code is for verify your email .\n "
        "if it's not you please check your accounts \n"
        "and dont tell this code to others",
        "makhliyoabboskhonova@gmail.com",
        [email],
    )

