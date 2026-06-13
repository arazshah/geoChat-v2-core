# backend/adapters/geodata/dataset_loader.py

from __future__ import annotations

from pathlib import Path

from backend.adapters.geodata.osm_sqlite_provider import OsmSqliteGeodataProvider

DEFAULT_DATASETS_DIR = Path("data/datasets")


def available_dataset_ids(
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
) -> list[str]:
    """Return dataset ids for which a SQLite file exists."""
    if not datasets_dir.exists():
        return []

    return sorted(
        path.stem
        for path in datasets_dir.glob("*.sqlite")
    )


def load_provider(
    dataset_id: str,
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
) -> OsmSqliteGeodataProvider:
    """Build an OsmSqliteGeodataProvider for a given dataset id."""
    db_path = datasets_dir / f"{dataset_id}.sqlite"
    return OsmSqliteGeodataProvider(dataset_id=dataset_id, db_path=db_path)


def load_all_providers(
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
) -> dict[str, OsmSqliteGeodataProvider]:
    """Build providers for all available datasets."""
    return {
        dataset_id: load_provider(dataset_id, datasets_dir)
        for dataset_id in available_dataset_ids(datasets_dir)
    }
