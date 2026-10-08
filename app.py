"""ACEest Fitness & Gym - Flask service.

Logic ported from the Tkinter reference versions (programs, clients,
workouts, progress, membership) into a small REST API.
Data is kept in memory so the app is simple to test and containerise.
"""
from datetime import date, datetime

from flask import Flask, jsonify, request

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\n"
                   "Wed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\n"
                   "Fri: 30min Active Recovery",
        "diet": "B: 3 Egg Whites + Oats Idli\nL: Grilled Chicken + Brown Rice\n"
                "D: Fish Curry + Millet Roti\nTarget: 2,000 kcal",
        "calorie_factor": 22,
    },
    "Muscle Gain (MG)": {
        "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\n"
                   "Thu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
        "diet": "B: 4 Eggs + PB Oats\nL: Chicken Biryani (250g Chicken)\n"
                "D: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal",
        "calorie_factor": 35,
    },
    "Beginner (BG)": {
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups.\n"
                   "Focus: Technique Mastery & Form (90% Threshold)",
        "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
        "calorie_factor": 26,
    },
}


def calculate_bmi(weight_kg, height_cm):
    """Return BMI rounded to 1 decimal. Raises ValueError on bad input."""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("weight and height must be positive")
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def calculate_calories(weight_kg, program):
    """Daily calorie target = weight * program factor."""
    if program not in PROGRAMS:
        raise ValueError("unknown program")
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    return int(weight_kg * PROGRAMS[program]["calorie_factor"])


def create_app():
    app = Flask(__name__)
    clients = {}
    workouts = []

    @app.get("/")
    def index():
        return jsonify(service="ACEest Fitness & Gym", status="running")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/programs")
    def list_programs():
        return jsonify(programs=list(PROGRAMS.keys()))

    @app.get("/programs/<name>")
    def get_program(name):
        program = PROGRAMS.get(name)
        if program is None:
            return jsonify(error="program not found"), 404
        return jsonify(name=name, workout=program["workout"], diet=program["diet"])

    @app.post("/clients")
    def add_client():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify(error="name is required"), 400
        if name in clients:
            return jsonify(error="client already exists"), 409
        program = data.get("program")
        if program is not None and program not in PROGRAMS:
            return jsonify(error="unknown program"), 400
        client = {
            "name": name,
            "age": data.get("age"),
            "height": data.get("height"),
            "weight": data.get("weight"),
            "program": program,
            "membership_status": "Active",
            "membership_end": data.get("membership_end"),
        }
        clients[name] = client
        return jsonify(client), 201

    @app.get("/clients")
    def list_clients():
        return jsonify(clients=list(clients.values()))

    @app.get("/clients/<name>")
    def get_client(name):
        client = clients.get(name)
        if client is None:
            return jsonify(error="client not found"), 404
        return jsonify(client)

    @app.delete("/clients/<name>")
    def delete_client(name):
        if clients.pop(name, None) is None:
            return jsonify(error="client not found"), 404
        return jsonify(deleted=name)

    @app.get("/clients/<name>/bmi")
    def client_bmi(name):
        client = clients.get(name)
        if client is None:
            return jsonify(error="client not found"), 404
        try:
            bmi = calculate_bmi(client["weight"], client["height"])
        except (TypeError, ValueError):
            return jsonify(error="valid weight and height required"), 400
        return jsonify(name=name, bmi=bmi)

    @app.get("/clients/<name>/calories")
    def client_calories(name):
        client = clients.get(name)
        if client is None:
            return jsonify(error="client not found"), 404
        try:
            kcal = calculate_calories(client["weight"], client["program"])
        except (TypeError, ValueError):
            return jsonify(error="valid weight and program required"), 400
        return jsonify(name=name, calories=kcal)

    @app.get("/clients/<name>/membership")
    def membership(name):
        client = clients.get(name)
        if client is None:
            return jsonify(error="client not found"), 404
        status = client["membership_status"]
        end = client["membership_end"]
        if end:
            try:
                if datetime.strptime(end, "%Y-%m-%d").date() < date.today():
                    status = "Expired"
            except ValueError:
                return jsonify(error="membership_end must be YYYY-MM-DD"), 400
        return jsonify(name=name, membership_status=status, membership_end=end)

    @app.post("/workouts")
    def log_workout():
        data = request.get_json(silent=True) or {}
        client = data.get("client")
        duration = data.get("duration_min")
        if client not in clients:
            return jsonify(error="client not found"), 404
        if not isinstance(duration, int) or duration <= 0:
            return jsonify(error="duration_min must be a positive integer"), 400
        entry = {
            "client": client,
            "date": data.get("date") or date.today().isoformat(),
            "workout_type": data.get("workout_type", "General"),
            "duration_min": duration,
        }
        workouts.append(entry)
        return jsonify(entry), 201

    @app.get("/workouts/<client>")
    def client_workouts(client):
        if client not in clients:
            return jsonify(error="client not found"), 404
        return jsonify(workouts=[w for w in workouts if w["client"] == client])

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
