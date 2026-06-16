from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Standard-Seitenweise für wachsende Listen (Schichten, Rechnungen, Audit-Log)."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
