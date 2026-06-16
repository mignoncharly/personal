"""Hilfsfunktion zum Schreiben von Audit-Einträgen."""

from .models import AuditLog


def _resolve_org_id(actor, instance):
    """Organisation des Eintrags: bevorzugt vom Objekt, sonst vom Akteur."""
    org_id = getattr(instance, "organization_id", None)
    if org_id is None:
        org_id = getattr(actor, "organization_id", None)
    return org_id


def log_action(actor, action, instance, summary="", changes=None):
    """Protokolliert eine Aktion an einem Objekt.

    actor: User (oder None), action: AuditLog.Action, instance: betroffenes Objekt.
    """
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        organization_id=_resolve_org_id(actor, instance),
        action=action,
        entity_type=instance.__class__.__name__,
        entity_id=str(instance.pk),
        summary=summary,
        changes=changes or {},
    )
