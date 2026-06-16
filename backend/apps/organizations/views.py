from rest_framework import generics
from rest_framework.exceptions import NotFound

from apps.accounts.permissions import IsAdmin
from apps.common.tenancy import get_current_org

from .models import Organization
from .serializers import OrganizationSerializer


class CurrentOrganizationView(generics.RetrieveUpdateAPIView):
    """Eigene Organisation des angemeldeten Admins lesen und bearbeiten.

    Singleton-Endpunkt: ``get_object`` liefert ausschließlich die Organisation des
    Benutzers, nie eine fremde – damit ist die Mandantentrennung strukturell
    garantiert. Ein org-loser Plattform-Superuser hat keine eigene Organisation
    und erhält 404.
    """

    serializer_class = OrganizationSerializer
    permission_classes = [IsAdmin]

    def get_object(self) -> Organization:
        org = get_current_org(self.request.user)
        if org is None:
            raise NotFound(
                "Dem angemeldeten Benutzer ist keine Organisation zugeordnet."
            )
        return org
