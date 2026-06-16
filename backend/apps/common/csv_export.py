"""Hilfsfunktion für CSV-Downloads (Excel-DE-freundlich)."""

import csv
from io import StringIO

from django.http import HttpResponse


def csv_response(filename: str, header: list[str], rows) -> HttpResponse:
    """Baut eine CSV-HttpResponse.

    Nutzt Semikolon als Trenner (deutsches Excel) und stellt der Datei eine
    UTF-8-BOM voran, damit Umlaute in Excel korrekt erscheinen.
    """
    buffer = StringIO()
    buffer.write("﻿")  # BOM für Excel
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
