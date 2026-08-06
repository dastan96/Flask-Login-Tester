import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, db


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
    return app.test_client()
