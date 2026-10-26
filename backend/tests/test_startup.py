from unittest.mock import MagicMock

import pytest

from backend import main


@pytest.mark.asyncio
async def test_startup_does_not_recreate_retired_legacy_tables(monkeypatch):
    database = MagicMock()
    create_tables = MagicMock()
    monkeypatch.setattr(main, "engine", database)
    monkeypatch.setattr(main.Base.metadata, "create_all", create_tables)

    async with main.lifespan(main.app):
        pass

    create_tables.assert_called_once()
    assert create_tables.call_args.kwargs["bind"] is database
    assert {table.name for table in create_tables.call_args.kwargs["tables"]} == {
        "documents_pdf2_stage",
        "chunks_pdf2_stage",
        "conversation_history",
    }
