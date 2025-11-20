from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional
import csv


def find_latest_export(data_dir: Path) -> Path:
    """Finde die neueste user_mailhistory_ratings_*.csv Datei."""
    exports: List[Path] = sorted(data_dir.glob("user_mailhistory_ratings_*.csv"))
    if not exports:
        raise FileNotFoundError(
            "Kein Export gefunden. Erwartet Dateien wie user_mailhistory_ratings_YYYYMMDDHHMM.csv"
        )
    return exports[-1]


def parse_int(value: Optional[str]) -> Optional[int]:
    """Hilfsfunktion zur robusten Integer-Konvertierung (0 => None)."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        number = int(text)
    except ValueError:
        return None
    return None if number == 0 else number


def load_mailhistory_export(csv_path: Path) -> List[Dict[str, Optional[int]]]:
    """Liest den Export und gibt relevante Felder als Liste von Dicts zurück."""
    records: List[Dict[str, Optional[int]]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append(
                {
                    "thread_id": parse_int(row.get("thread_id")),
                    "counsellor_coherence_rating": parse_int(
                        row.get("counsellor_coherence_rating")
                    ),
                    "client_coherence_rating": parse_int(
                        row.get("client_coherence_rating")
                    ),
                    "quality_rating": parse_int(row.get("quality_rating")),
                    "overall_rating": parse_int(row.get("overall_rating")),
                }
            )
    return records


def count_overall_two_but_good(records: Iterable[Dict[str, Optional[int]]]) -> List[Dict[str, Optional[int]]]:
    """Filtert Bewertungen, bei denen overall=2, die Teilratings aber alle ≤2 sind."""
    result: List[Dict[str, Optional[int]]] = []
    for record in records:
        overall = record["overall_rating"]
        subratings = [
            record["counsellor_coherence_rating"],
            record["client_coherence_rating"],
            record["quality_rating"],
        ]
        if overall != 2:
            continue
        if any(rating is None for rating in subratings):
            continue
        if all(rating <= 2 for rating in subratings):
            result.append(record)
    return result


def count_overall_good(records: Iterable[Dict[str, Optional[int]]]) -> List[Dict[str, Optional[int]]]:
    """Filtert Bewertungen mit overall=1."""
    return [record for record in records if record["overall_rating"] == 1]


def main() -> None:
    data_dir = Path(__file__).parent
    csv_path = find_latest_export(data_dir)
    records = load_mailhistory_export(csv_path)

    overall_two_but_good = count_overall_two_but_good(records)
    overall_good = count_overall_good(records)

    unique_threads_two_but_good = {
        record["thread_id"] for record in overall_two_but_good if record["thread_id"]
    }
    unique_threads_good = {
        record["thread_id"] for record in overall_good if record["thread_id"]
    }

    print(f"Ausgewertete Datei: {csv_path.name}")
    print(f"Anzahl Datensätze insgesamt: {len(records)}")
    print()
    print("Overall-Rating = 2, obwohl Teilratings gut (≤2) waren:")
    print(f"  Anzahl Bewertungen: {len(overall_two_but_good)}")
    print(f"  Unterschiedliche Threads: {len(unique_threads_two_but_good)}")
    print()
    print("Overall-Rating = 1 (Fall als gut bewertet):")
    print(f"  Anzahl Bewertungen: {len(overall_good)}")
    print(f"  Unterschiedliche Threads: {len(unique_threads_good)}")


if __name__ == "__main__":
    main()
