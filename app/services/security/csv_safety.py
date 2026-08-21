"""
CSV-Formula-Injection-Schutz (CWE-1236).

Tabellenkalkulationen (Excel, LibreOffice, Google Sheets) interpretieren den
Inhalt einer Zelle als Formel, wenn er mit `=`, `+`, `-`, `@` (oder bestimmten
Steuerzeichen) beginnt. Exportiert LLARS untrusted Daten (LLM-Output, importierte
Evaluationsdaten, frei wählbare Item-Labels/Usernamen) ungeschützt als CSV, kann
eine präparierte Zelle wie `=HYPERLINK(...)` oder `=cmd|...` beim Öffnen Code
auslösen.

Zentrale Stelle, damit alle CSV-Exporte denselben Schutz verwenden.
"""

# Zeichen, die am Zellanfang eine Formel/Command-Auswertung auslösen können.
_DANGEROUS_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def csv_safe_cell(value):
    """
    Neutralisiert eine einzelne CSV-Zelle gegen Formula-Injection.

    Stellt einem gefährlichen String-Anfang ein einfaches Hochkomma voran
    (de-facto-Standard, den Spreadsheets als "Text, nicht Formel" interpretieren).
    Nicht-Strings werden unverändert zurückgegeben.
    """
    if isinstance(value, str) and value and value[0] in _DANGEROUS_PREFIXES:
        return "'" + value
    return value


def csv_safe_row(row: dict) -> dict:
    """Wendet csv_safe_cell auf alle Werte eines Dict-Rows an."""
    return {key: csv_safe_cell(val) for key, val in row.items()}
