from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from tender_crawler.models import Tender


CSV_COLUMNS = [
    "id",
    "title",
    "source",
    "source_url",
    "province",
    "city",
    "buyer",
    "agency",
    "budget",
    "publish_date",
    "deadline",
    "category",
    "matched_keywords",
    "relevance_score",
    "summary",
]


def export_tenders_to_csv(
    tenders: List[Tender],
    output_dir: str | Path = "data/exports",
) -> Path:
    export_dir = Path(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"tenders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_path = export_dir / filename

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for tender in tenders:
            writer.writerow({column: getattr(tender, column, "") for column in CSV_COLUMNS})

    return output_path
