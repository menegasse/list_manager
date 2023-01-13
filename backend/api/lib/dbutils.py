import datetime
from typing import Literal, TypedDict, TypeVar

from dateutil.relativedelta import relativedelta
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import connection, models
from django.db.models import Q
from django.utils import timezone
from typing_extensions import NotRequired

_M = TypeVar("_M", bound=models.Model)
_partitioned_tables = []


class SearchColumn(TypedDict):
    name: str
    weight: NotRequired[Literal["A", "B", "C", "D"]]


def ensure_partitions(start: datetime.date | None = None):
    if not _partitioned_tables or connection.vendor in ["postgresql", "postgis"]:
        return

    with connection.cursor() as c:
        c.execute("SELECT table_name FROM information_schema.tables")
        existing = {t[0] for t in c}

        # Create month partitions
        current = (start or (timezone.localdate() - relativedelta(months=1))).replace(day=1)
        end = (timezone.localdate() + relativedelta(months=1)).replace(day=1)

        while current <= end:
            dnext = current + relativedelta(months=1)
            suffix = f"y{current.year:04d}m{current.month:02d}"

            for table in _partitioned_tables:
                if (partition := f"{table}_{suffix}") in existing:
                    continue

                c.execute(
                    f"CREATE TABLE {partition} PARTITION OF {table} FOR VALUES FROM (%s) TO (%s)",
                    (current.isoformat(), dnext.isoformat()),
                )

            current = dnext

        # Create default partitions
        for table in _partitioned_tables:
            if (partition := f"{table}_default") in existing:
                continue

            c.execute(f"CREATE TABLE {partition} PARTITION OF {table} DEFAULT")


def search(
    qs: models.QuerySet[_M],
    q: str,
    columns: list[SearchColumn],
    *,
    config="portuguese",
    search_type="websearch",
    min_rank: float = 0.1,
) -> models.QuerySet[_M]:
    q = q.strip(" ") if q else ""
    if not q:
        return qs

    if connection.vendor == "postgresql":
        vector = SearchVector(
            columns[0]["name"],
            config=config,
            weight=columns[0].get("weight"),
        )
        for c in columns[1:]:
            vector += SearchVector(c["name"], config=config, weight=c.get("weight"))

        return (
            qs.annotate(
                __rank=SearchRank(vector, SearchQuery(q, config=config, search_type=search_type)),
            )
            .filter(
                __rank__gte=min_rank,
            )
            .order_by(
                "-__rank",
            )
        )
    else:
        cnames = [c["name"] for c in columns]
        flist = []
        for v in q.split(" "):
            if not v:
                continue

            flist.extend([Q(**{f"{c}__icontains": v}) for c in cnames])

        if not flist:
            return qs

        f = flist[0]
        for other in flist[1:]:
            f |= other

        return qs.filter(f)
