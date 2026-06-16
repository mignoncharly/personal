from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager für das E-Mail-basierte User-Modell (kein username)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("Eine E-Mail-Adresse ist erforderlich."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.EMPLOYEE)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser muss is_staff=True haben."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser muss is_superuser=True haben."))
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User mit E-Mail als Login. Rolle steuert Admin- vs. Mitarbeiter-Rechte."""

    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        EMPLOYEE = "employee", _("Mitarbeiter")

    username = None
    email = models.EmailField(_("E-Mail-Adresse"), unique=True)
    role = models.CharField(
        _("Rolle"), max_length=20, choices=Role.choices, default=Role.EMPLOYEE
    )
    phone = models.CharField(_("Telefonnummer"), max_length=40, blank=True)
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        null=True, blank=True, related_name="users", verbose_name=_("Organisation"),
        help_text=_("Zugehörige Organisation. Leer = plattformweiter Superuser."),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("Benutzer")
        verbose_name_plural = _("Benutzer")

    def __str__(self):
        return self.email

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN
