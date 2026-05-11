from pathlib import Path

import pytest

from app.modules.catalog.parser import parse_csv_to_chunks


def test_parse_csv_to_chunks_builds_chunks_from_template(tmp_path: Path):
    file_path = tmp_path / "catalog.csv"
    file_path.write_text(
        "type,name,category,description,price,currency,tags\n"
        "product,Widget,Tools,Useful widget,100,USD,tool\n",
        encoding="utf-8",
    )

    chunks = parse_csv_to_chunks(file_path)

    assert len(chunks) == 1
    assert "Название: Widget" in chunks[0].text
    assert "Цена: 100 USD" in chunks[0].text
    assert chunks[0].metadata == {
        "row_number": 2,
        "type": "product",
        "name": "Widget",
        "category": "Tools",
        "price": "100",
        "currency": "USD",
        "tags": "tool",
    }


def test_parse_csv_to_chunks_rejects_missing_required_columns(tmp_path: Path):
    file_path = tmp_path / "catalog.csv"
    file_path.write_text("type,name,description\nproduct,Widget,Useful widget\n", encoding="utf-8")

    with pytest.raises(ValueError, match="category"):
        parse_csv_to_chunks(file_path)


def test_parse_csv_to_chunks_rejects_incomplete_rows(tmp_path: Path):
    file_path = tmp_path / "catalog.csv"
    file_path.write_text(
        "type,name,category,description\nproduct,Widget,Tools,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="row 2"):
        parse_csv_to_chunks(file_path)
