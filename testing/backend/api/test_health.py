import app.main as main_module


def test_health_endpoint_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_db_down_returns_503_for_api_routes(client):
    main_module._db_healthy = False
    res = client.get("/users/")
    assert res.status_code == 503
    assert "Database connection is down" in res.json()["detail"]
    main_module._db_healthy = True


def test_db_down_does_not_block_health(client):
    main_module._db_healthy = False
    res = client.get("/health")
    assert res.status_code == 200
    main_module._db_healthy = True
