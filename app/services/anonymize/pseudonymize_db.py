import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence


@dataclass(frozen=True)
class MunicipalityFeatures:
    muncipality_name: str
    age_quotient: float
    youth_quotient: float
    population: float
    population_density: float
    unemployment: float
    renting_price: float
    social_rate: float
    education: float
    crime_rate: float
    income: float

    def to_feature_vector(self) -> list[float]:
        return [
            float(self.age_quotient),
            float(self.youth_quotient),
            float(self.population),
            float(self.population_density),
            float(self.unemployment),
            float(self.renting_price),
            float(self.social_rate),
            float(self.education),
            float(self.crime_rate),
            float(self.income),
        ]


class PseudonymizeDBHandler:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get_random_firstname_or_lastname(
        self, name_origin: str, min_count: int, old_name: str
    ) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT gender FROM firstnames WHERE firstname = ? LIMIT 1",
                (old_name,),
            )
            firstname_row = cur.fetchone()

            cur.execute(
                "SELECT 1 FROM lastnames WHERE lastname = ? LIMIT 1",
                (old_name,),
            )
            lastname_row = cur.fetchone()

            if firstname_row is not None:
                (old_gender,) = firstname_row
                cur.execute(
                    """
                    SELECT firstname
                    FROM firstnames
                    WHERE name_origin = ?
                      AND count > ?
                      AND gender = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                    (name_origin, int(min_count), old_gender),
                )
                row = cur.fetchone()
                if row:
                    return str(row[0])

            if lastname_row is not None:
                cur.execute(
                    """
                    SELECT lastname
                    FROM lastnames
                    WHERE name_origin = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                    (name_origin,),
                )
                row = cur.fetchone()
                if row:
                    return str(row[0])

            cur.execute(
                """
                SELECT firstname
                FROM firstnames
                WHERE name_origin = ?
                  AND count > ?
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (name_origin, int(min_count)),
            )
            row = cur.fetchone()
            if row:
                return str(row[0])

        return "▓" * 10

    def get_random_firstname(self, name_origin: str, min_count: int, old_name: str) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT gender FROM firstnames WHERE firstname = ? LIMIT 1",
                (old_name,),
            )
            row = cur.fetchone()

            if row is not None:
                (old_gender,) = row
                cur.execute(
                    """
                    SELECT firstname
                    FROM firstnames
                    WHERE name_origin = ?
                      AND count > ?
                      AND gender = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                    (name_origin, int(min_count), old_gender),
                )
            else:
                cur.execute(
                    """
                    SELECT firstname
                    FROM firstnames
                    WHERE name_origin = ?
                      AND count > ?
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                    (name_origin, int(min_count)),
                )

            result = cur.fetchone()
            if result:
                return str(result[0])

        return "▓" * 10

    def get_random_lastname(self, name_origin: str) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT lastname
                FROM lastnames
                WHERE name_origin = ?
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (name_origin,),
            )
            row = cur.fetchone()
            if row:
                return str(row[0])
        return "▓" * 10

    def get_random_muncipality(self) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT muncipality_name FROM muncipalities ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            if row:
                return str(row[0])
        return "▓" * 10

    def get_random_district(self) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT district_name FROM districts ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            if row:
                return str(row[0])
        return "▓" * 10

    def get_random_canton(self) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT canton_name FROM cantons ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            if row:
                return str(row[0])
        return "▓" * 10

    def get_random_muncipality_by_index(self, index_list: Sequence[int]) -> str:
        if not index_list:
            return self.get_random_muncipality()

        placeholders = ",".join("?" for _ in index_list)
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                f"""
                SELECT muncipality_name
                FROM muncipalities
                WHERE muncipality_id IN ({placeholders})
                ORDER BY RANDOM()
                LIMIT 1
                """,
                tuple(int(i) for i in index_list),
            )
            row = cur.fetchone()
            if row:
                return str(row[0])
        return self.get_random_muncipality()

    def get_muncipality_features(self, location: str) -> Optional[MunicipalityFeatures]:
        search_term = f"%{location}%"
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT muncipality_name,
                       age_quotient, youth_quotient, population, population_density,
                       unemployment, renting_price, social_rate, education, crime_rate, income
                FROM muncipalities
                WHERE muncipality_name LIKE ?
                LIMIT 1
                """,
                (search_term,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return MunicipalityFeatures(
                muncipality_name=str(row[0]),
                age_quotient=float(row[1]),
                youth_quotient=float(row[2]),
                population=float(row[3]),
                population_density=float(row[4]),
                unemployment=float(row[5]),
                renting_price=float(row[6]),
                social_rate=float(row[7]),
                education=float(row[8]),
                crime_rate=float(row[9]),
                income=float(row[10]),
            )

    def is_in_district_db(self, location: str) -> bool:
        search_term = f"%{location}%"
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT 1 FROM districts WHERE district_name LIKE ? LIMIT 1", (search_term,))
            return cur.fetchone() is not None

    def is_in_canton_db(self, location: str) -> bool:
        search_term = f"%{location}%"
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT 1 FROM cantons WHERE canton_name LIKE ? LIMIT 1", (search_term,))
            return cur.fetchone() is not None

    def is_in_firstname_db(self, name: str) -> bool:
        search_term = f"%{name}%"
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT 1 FROM firstnames WHERE firstname LIKE ? LIMIT 1", (search_term,))
            return cur.fetchone() is not None

    def is_in_lastname_db(self, name: str) -> bool:
        search_term = f"%{name}%"
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT 1 FROM lastnames WHERE lastname LIKE ? LIMIT 1", (search_term,))
            return cur.fetchone() is not None

