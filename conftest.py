import pytest

from app import create_app
from app import models
from app.extensions import db as database


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        database.create_all()
        yield app
        database.session.remove()
        database.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def db(app):
    return database
