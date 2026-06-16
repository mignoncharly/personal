"""Mandantentrennung (Multi-Tenancy).

Zentrale Helfer, die sicherstellen, dass jeder Benutzer ausschließlich Daten seiner
eigenen Organisation sieht und verändert. Ein plattformweiter Superuser (Rolle ohne
Organisation) sieht organisationsübergreifend alles.

Das Querysetscoping ist die Sicherheitsgrenze: Da DRFs ``get_object`` über
``get_queryset`` läuft, liefert der Zugriff auf ein fremdes Objekt automatisch 404 –
ohne dessen Existenz preiszugeben.
"""

from rest_framework.exceptions import NotFound, ValidationError


def is_unscoped(user) -> bool:
    """True, wenn der Benutzer organisationsübergreifend arbeitet (Plattform-Superuser)."""
    return bool(
        user
        and user.is_authenticated
        and user.is_superuser
        and getattr(user, "organization_id", None) is None
    )


def get_current_org(user):
    """Organisation des Benutzers; None beim Plattform-Superuser."""
    if not user or not user.is_authenticated:
        return None
    if is_unscoped(user):
        return None
    return getattr(user, "organization", None)


def scope_queryset(qs, user, field: str = "organization"):
    """Beschränkt ``qs`` auf die Organisation des Benutzers.

    ``field`` ist der Lookup-Pfad vom Modell zur Organisation, z. B. ``"organization"``
    (direkte FK) oder ``"customer__organization"`` / ``"user__organization"`` (indirekt).
    """
    if is_unscoped(user):
        return qs
    org_id = getattr(user, "organization_id", None)
    if not org_id:
        return qs.none()
    return qs.filter(**{field: org_id})


def assert_org_match(user, org_id) -> None:
    """Stellt sicher, dass ``org_id`` der Organisation des Benutzers entspricht.

    Wird beim Anlegen/Ändern genutzt, um zu verhindern, dass auf fremde Eltern­objekte
    (Kunde, Vertrag, Mitarbeiter) verwiesen wird. Superuser sind ausgenommen.
    """
    if is_unscoped(user):
        return
    if org_id != getattr(user, "organization_id", None):
        raise NotFound()


class TenantScopedViewSet:
    """Mixin für ViewSets mit Mandantentrennung.

    - ``tenant_field``: Lookup-Pfad zur Organisation für das Querysetscoping.
    - Bei direktem FK (``tenant_field == "organization"``) wird die Organisation beim
      Anlegen automatisch gestempelt.
    """

    tenant_field = "organization"

    def get_queryset(self):
        return scope_queryset(super().get_queryset(), self.request.user, self.tenant_field)

    def perform_create(self, serializer):
        if self.tenant_field == "organization":
            org = get_current_org(self.request.user)
            if org is None:
                # Unscoped Plattform-Superuser (oder Benutzer ohne Organisation) kann
                # kein mandantengebundenes Objekt anlegen, da keine Organisation zum
                # Stempeln existiert. Klare 400 statt IntegrityError/500.
                raise ValidationError(
                    "Dem angemeldeten Benutzer ist keine Organisation zugeordnet. "
                    "Bitte einer Organisation zuweisen, um Daten anzulegen."
                )
            serializer.save(organization=org)
        else:
            serializer.save()
