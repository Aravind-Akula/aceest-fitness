# ACEest Fitness & Gym – Flask CI/CD Project
# Built as part of the DevOps assignment
A Flask REST service for gym management (programs, clients, BMI/calorie targets,
membership checks, workout logs), built with a full DevOps pipeline:
Git/GitHub → Pytest → Docker → GitHub Actions → Jenkins.

The application logic is ported from the original ACEest Tkinter versions
(1.0 – 3.2.4) into a testable web API.

## Local setup

```bash
git clone <your-repo-url> && cd aceest-fitness
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py                                     # http://localhost:5000
```

Try it: `curl localhost:5000/programs`

### Main endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/programs`, `/programs/<name>` | Workout & diet plans |
| POST/GET/DELETE | `/clients`, `/clients/<name>` | Manage clients |
| GET | `/clients/<name>/bmi` · `/calories` · `/membership` | Calculations |
| POST/GET | `/workouts`, `/workouts/<client>` | Log and view workouts |

## Run tests manually

```bash
pytest -v
```

## Docker

```bash
docker build -t aceest-fitness .
docker run -p 5000:5000 aceest-fitness            # run the app
docker run --rm aceest-fitness pytest -v          # run tests in the container
```

The image uses `python:3.12-slim`, caches dependency layers, ignores junk via
`.dockerignore`, and runs as a non-root user with gunicorn.

## CI/CD overview

### GitHub Actions (`.github/workflows/main.yml`)
Triggered on every **push** and **pull_request**:
1. **Build & Lint** – installs dependencies, `py_compile` syntax check, `flake8`.
2. **Docker Build & Test** – builds the image, then runs Pytest *inside* the container.

### Jenkins (`Jenkinsfile`)
A Jenkins Pipeline job (Pipeline script from SCM) pulls the latest code from GitHub and:
1. **Checkout** – fetches the repo.
2. **Clean Build** – `docker build --no-cache` for a from-scratch build.
3. **Test in Container** – runs Pytest in the freshly built image.

Jenkins acts as a second, independent validation of the build in a controlled environment.

## Branching
`main` (stable) · `feature/*` · `bugfix/*` · `infra/*`, merged via pull requests.
