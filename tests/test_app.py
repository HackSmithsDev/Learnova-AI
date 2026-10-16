def test_testing_app_uses_sqlite_and_serves_homepage(app, client, db):
    assert app.config['TESTING'] is True
    assert db.engine.url.get_backend_name() == 'sqlite'
    assert client.get('/').status_code == 200
