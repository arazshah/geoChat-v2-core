# backend/etl/osm/build_dataset.py

from __future__ import annotations

import argparse
import time
from pathlib import Path

from backend.etl.osm.city_config import get_city_config, list_dataset_ids
from backend.etl.osm.osm_extractor import extract_city_pois
from backend.etl.osm.sqlite_writer import SqliteDatasetWriter

DEFAULT_PBF_PATH = Path("data/raw/iran-latest.osm.pbf")
DEFAULT_OUTPUT_DIR = Path("data/datasets")


def build_dataset(
    dataset_id: str,
    pbf_path: Path,
    output_dir: Path,
) -> int:
    """Build a single city dataset and return the number of POIs written."""
    city = get_city_config(dataset_id)
    db_path = output_dir / f"{dataset_id}.sqlite"

    print(f"[{dataset_id}] city: {city.name_fa} ({city.name_en})")
    print(f"[{dataset_id}] bbox: {city.bbox.as_list()}")
    print(f"[{dataset_id}] reading PBF: {pbf_path}")

    start = time.perf_counter()
    rows = extract_city_pois(pbf_path, city)
    elapsed = time.perf_counter() - start

    print(f"[{dataset_id}] extracted {len(rows)} POIs in {elapsed:.1f}s")

    writer = SqliteDatasetWriter(db_path)
    writer.initialize()
    inserted = writer.write_rows(rows)

    print(f"[{dataset_id}] wrote {inserted} rows -> {db_path}")
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build city POI datasets from an OSM PBF file.",
    )
    parser.add_argument(
        "--dataset",
        choices=[*list_dataset_ids(), "all"],
        default="all",
        help="Dataset id to build, or 'all'.",
    )
    parser.add_argument(
        "--pbf",
        type=Path,
        default=DEFAULT_PBF_PATH,
        help="Path to the OSM PBF file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for dataset databases.",
    )
    args = parser.parse_args()

    if not args.pbf.exists():
        msg = f"PBF file not found: {args.pbf}"
        raise FileNotFoundError(msg)

    dataset_ids = (
        list_dataset_ids() if args.dataset == "all" else [args.dataset]
    )

    total = 0
    for dataset_id in dataset_ids:
        total += build_dataset(dataset_id, args.pbf, args.output_dir)

    print(f"Done. Total POIs written across datasets: {total}")


if __name__ == "__main__":
    main()
