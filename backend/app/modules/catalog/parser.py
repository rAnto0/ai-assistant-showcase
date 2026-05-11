import csv
from pathlib import Path

from app.modules.catalog.types import CatalogChunk

REQUIRED_COLUMNS = {"type", "name", "category", "description"}
OPTIONAL_COLUMNS = {"price", "currency", "tags"}


def parse_csv_to_chunks(file_path: Path) -> list[CatalogChunk]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header")

        fieldnames = {field.strip() for field in reader.fieldnames if field}
        missing_columns = REQUIRED_COLUMNS - fieldnames
        if missing_columns:
            columns = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV file is missing required columns: {columns}")

        chunks: list[CatalogChunk] = []
        for row_number, row in enumerate(reader, start=2):
            normalized_row = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            if not any(normalized_row.values()):
                continue

            row_type = normalized_row.get("type", "")
            name = normalized_row.get("name", "")
            category = normalized_row.get("category", "")
            description = normalized_row.get("description", "")

            if not row_type or not name or not category or not description:
                raise ValueError(f"CSV row {row_number} is missing type, name, category, or description")

            metadata = {
                "row_number": row_number,
                "type": row_type,
                "name": name,
                "category": category,
            }
            for column in OPTIONAL_COLUMNS:
                value = normalized_row.get(column)
                if value:
                    metadata[column] = value

            chunks.append(CatalogChunk(text=_build_chunk_text(normalized_row), metadata=metadata))

    return chunks


def _build_chunk_text(row: dict[str, str]) -> str:
    parts = [
        f"Тип: {row['type']}",
        f"Название: {row['name']}",
        f"Категория: {row['category']}",
        f"Описание: {row['description']}",
    ]
    if row.get("price"):
        price = row["price"]
        currency = row.get("currency", "")
        parts.append(f"Цена: {price} {currency}".strip())
    if row.get("tags"):
        parts.append(f"Теги: {row['tags']}")
    return "\n".join(parts)
