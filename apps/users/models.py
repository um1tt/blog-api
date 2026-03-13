from __future__ import annotations

from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    class LanguageChoices(models.TextChoices):
        EN = "en", _("English")
        RU = "ru", _("Russian")
        KK = "kk", _("Kazakh")

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first_name"), max_length=50)
    last_name = models.CharField(_("last name"), max_length=50)

    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    avatar = models.ImageField(_("avatar"), upload_to="avatars/", blank=True, null=True)

    preferred_language = models.CharField(
        _("preferred language"),
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.EN,
    )
    timezone = models.CharField(
        _("timezone"),
        max_length=64,
        default="UTC",
    )


    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self) -> str:
        return self.email 