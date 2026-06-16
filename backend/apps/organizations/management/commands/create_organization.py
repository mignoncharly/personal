"""Legt eine neue Organisation samt erstem Admin an (nur für Plattformbetreiber).

Beispiel:
    python manage.py create_organization "Pflegedienst Sonnenschein" \
        --admin-email chef@sonnenschein.de --admin-first-name Maria --admin-last-name Klein

Der Admin erhält standardmäßig kein Passwort, sondern meldet sich beim ersten Mal
über den vorhandenen Passwort-Reset-Flow an. Mit --password kann ein Startpasswort
direkt gesetzt werden.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.organizations.models import Organization

User = get_user_model()


class Command(BaseCommand):
    help = "Erstellt eine Organisation und ihren ersten Admin-Benutzer."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Anzeigename der Organisation")
        parser.add_argument("--slug", help="URL-Kürzel (Standard: aus dem Namen abgeleitet)")
        parser.add_argument("--admin-email", required=True, help="E-Mail des ersten Admins")
        parser.add_argument("--admin-first-name", default="", help="Vorname des Admins")
        parser.add_argument("--admin-last-name", default="", help="Nachname des Admins")
        parser.add_argument(
            "--password",
            help="Optionales Startpasswort. Ohne Angabe meldet sich der Admin "
                 "per Passwort-Reset erstmalig an.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        name = options["name"].strip()
        slug = (options.get("slug") or slugify(name))[:60]
        email = options["admin_email"].strip().lower()
        password = options.get("password")

        if Organization.objects.filter(slug=slug).exists():
            raise CommandError(f"Es existiert bereits eine Organisation mit dem Kürzel '{slug}'.")
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError(f"Es existiert bereits ein Benutzer mit der E-Mail '{email}'.")

        if password:
            try:
                validate_password(password)
            except DjangoValidationError as exc:
                raise CommandError("Passwort ungültig: " + "; ".join(exc.messages))

        org = Organization.objects.create(name=name, slug=slug)

        admin = User(
            email=email,
            first_name=options["admin_first_name"].strip(),
            last_name=options["admin_last_name"].strip(),
            role=User.Role.ADMIN,
            organization=org,
            is_staff=False,
        )
        if password:
            admin.set_password(password)
        else:
            admin.set_unusable_password()
        admin.save()

        self.stdout.write(self.style.SUCCESS(
            f"Organisation '{org.name}' (Kürzel: {org.slug}) angelegt."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Admin '{admin.email}' (Rolle: admin) angelegt."
        ))
        if password:
            self.stdout.write("Der Admin kann sich sofort mit dem gesetzten Passwort anmelden.")
        else:
            self.stdout.write(
                "Kein Passwort gesetzt – der Admin meldet sich über "
                "'Passwort zurücksetzen' erstmalig an."
            )
        self.stdout.write(
            "Firmendetails (Adresse, USt-IdNr., Bank, Logo) bitte im Django-Admin "
            "unter 'Organisationen' ergänzen – sie erscheinen auf den Rechnungen."
        )
