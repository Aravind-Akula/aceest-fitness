import pytest

from app import PROGRAMS, calculate_bmi, calculate_calories, create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def add(client, **overrides):
    payload = {"name": "Ravi", "age": 28, "height": 175, "weight": 70,
               "program": "Fat Loss (FL)"}
    payload.update(overrides)
    return client.post("/clients", json=payload)


# ---- pure logic ----
def test_bmi_value():
    assert calculate_bmi(70, 175) == 22.9


@pytest.mark.parametrize("w,h", [(0, 170), (70, 0), (-1, 170)])
def test_bmi_invalid(w, h):
    with pytest.raises(ValueError):
        calculate_bmi(w, h)


def test_calories_per_program():
    assert calculate_calories(70, "Fat Loss (FL)") == 70 * 22
    assert calculate_calories(70, "Muscle Gain (MG)") == 70 * 35


def test_calories_invalid():
    with pytest.raises(ValueError):
        calculate_calories(70, "Nope")
    with pytest.raises(ValueError):
        calculate_calories(0, "Fat Loss (FL)")


# ---- basic endpoints ----
def test_index_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").get_json() == {"status": "ok"}


def test_list_programs(client):
    assert set(client.get("/programs").get_json()["programs"]) == set(PROGRAMS)


def test_get_program(client):
    r = client.get("/programs/Beginner (BG)")
    assert r.status_code == 200
    assert "Circuit" in r.get_json()["workout"]


def test_get_program_404(client):
    assert client.get("/programs/unknown").status_code == 404


# ---- clients ----
def test_add_and_get_client(client):
    assert add(client).status_code == 201
    r = client.get("/clients/Ravi")
    assert r.status_code == 200
    assert r.get_json()["membership_status"] == "Active"
    assert len(client.get("/clients").get_json()["clients"]) == 1


def test_add_client_validation(client):
    assert add(client, name="").status_code == 400
    assert add(client, program="Bad").status_code == 400


def test_duplicate_client(client):
    add(client)
    assert add(client).status_code == 409


def test_delete_client(client):
    add(client)
    assert client.delete("/clients/Ravi").status_code == 200
    assert client.get("/clients/Ravi").status_code == 404
    assert client.delete("/clients/Ravi").status_code == 404


def test_client_bmi_and_calories(client):
    add(client)
    assert client.get("/clients/Ravi/bmi").get_json()["bmi"] == 22.9
    assert client.get("/clients/Ravi/calories").get_json()["calories"] == 1540


def test_bmi_missing_data(client):
    add(client, weight=None)
    assert client.get("/clients/Ravi/bmi").status_code == 400
    assert client.get("/clients/Ghost/bmi").status_code == 404


# ---- membership ----
def test_membership_active_and_expired(client):
    add(client, name="A", membership_end="2999-01-01")
    add(client, name="B", membership_end="2000-01-01")
    assert client.get("/clients/A/membership").get_json()["membership_status"] == "Active"
    assert client.get("/clients/B/membership").get_json()["membership_status"] == "Expired"


def test_membership_bad_date(client):
    add(client, membership_end="not-a-date")
    assert client.get("/clients/Ravi/membership").status_code == 400


# ---- workouts ----
def test_log_and_fetch_workout(client):
    add(client)
    r = client.post("/workouts", json={"client": "Ravi", "duration_min": 45,
                                       "workout_type": "Strength"})
    assert r.status_code == 201
    assert len(client.get("/workouts/Ravi").get_json()["workouts"]) == 1


def test_workout_validation(client):
    add(client)
    assert client.post("/workouts", json={"client": "Ghost", "duration_min": 30}).status_code == 404
    assert client.post("/workouts", json={"client": "Ravi", "duration_min": -5}).status_code == 400
