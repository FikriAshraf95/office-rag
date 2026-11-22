"""SPEC-11 §6 acceptance checks 1-4, the static half.

These read the compose file, Dockerfiles, nginx config and repo, so they run in the normal suite with no
Docker and no network. The live half (a running stack, the worker offline, image layers) is
`scripts/release_check.sh`, run before a release.
"""

import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]
BACKEND = REPO / "backend"
FRONTEND = REPO / "frontend"

pytestmark = pytest.mark.skipif(
    not (REPO / "docker-compose.yml").exists(), reason="needs the repo root (compose file) next to backend/"
)


def _compose() -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))
    return data


def _nginx() -> str:
    return (FRONTEND / "nginx" / "default.conf").read_text(encoding="utf-8")


def _location(conf: str, name: str) -> str:
    match = re.search(r"location\s+" + re.escape(name) + r"\s*\{(.*?)\n\s*\}", conf, re.DOTALL)
    assert match, f"nginx has no `location {name}` block"
    return match.group(1)


def test_spec11_ac01_compose_services_ports_and_health() -> None:
    services = _compose()["services"]
    assert {"postgres", "api", "worker", "frontend"} <= services.keys()

    for name, svc in services.items():
        for port in svc.get("ports", []):
            assert str(port).startswith("127.0.0.1:"), f"{name} publishes {port} beyond loopback"
    assert "127.0.0.1:8080:80" in services["frontend"]["ports"]
    assert "127.0.0.1:8000:8000" in services["api"]["ports"]

    assert "healthcheck" in services["postgres"]
    assert services["api"]["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert services["worker"]["depends_on"]["api"]["condition"] == "service_healthy"
    assert services["api"]["build"]["target"] == "api"
    assert services["worker"]["build"]["target"] == "worker"
    for name in ("api", "worker"):
        assert services[name]["env_file"] == ".env"
        assert services[name]["environment"]["DATABASE_URL"].endswith("@postgres:5432/rag")
        assert services[name]["environment"]["STORAGE_DIR"] == "/data/storage"

    dockerfile = (BACKEND / "Dockerfile").read_text(encoding="utf-8")
    api_stage = dockerfile.split("FROM base AS api", 1)[1].split("FROM ", 1)[0]
    assert "HEALTHCHECK" in api_stage and "/health" in api_stage
    assert "alembic upgrade head" in api_stage

    conf = _nginx()
    assert "proxy_pass http://api:8000;" in (FRONTEND / "nginx" / "proxy.conf").read_text(encoding="utf-8")
    _location(conf, "/api/")
    _location(conf, "= /health")
    assert "try_files $uri /index.html" in conf


def test_spec11_ac02_nginx_streams_chat_unbuffered() -> None:
    chat = _location(_nginx(), "= /api/v1/chat")
    assert "proxy_buffering off;" in chat
    assert "gzip off;" in chat
    read_timeout = re.search(r"proxy_read_timeout\s+(\d+)s;", chat)
    assert read_timeout and int(read_timeout.group(1)) > 15, "must outlast the 15 s SSE keep-alive"

    chat_api = (BACKEND / "app" / "api" / "chat.py").read_text(encoding="utf-8")
    assert '"X-Accel-Buffering": "no"' in chat_api


def test_spec11_ac02_csp_allows_pdfjs_and_nothing_external() -> None:
    headers = (FRONTEND / "nginx" / "security-headers.conf").read_text(encoding="utf-8")
    csp = re.search(r'Content-Security-Policy "([^"]+)"', headers)
    assert csp
    directives = dict(d.strip().split(" ", 1) for d in csp.group(1).split(";") if d.strip())
    assert directives["default-src"] == "'self'"
    assert directives["script-src"] == "'self'"
    assert set(directives["img-src"].split()) >= {"'self'", "blob:", "data:"}
    assert set(directives["worker-src"].split()) >= {"'self'", "blob:"}
    assert "http" not in csp.group(1), "the CSP names no external origin"


def test_spec11_ac03_worker_models_baked_and_offline() -> None:
    dockerfile = (BACKEND / "Dockerfile").read_text(encoding="utf-8")
    worker_stage = dockerfile.split("FROM base AS worker", 1)[1]
    assert "docling-tools models download" in worker_stage
    for model in ("layout", "tableformer", "rapidocr"):
        assert model in worker_stage
    assert "AutoTokenizer.from_pretrained" in worker_stage
    # Offline flags are set after the download step, so the build can fetch and the runtime can't.
    download_at = worker_stage.index("docling-tools models download")
    assert worker_stage.index("HF_HUB_OFFLINE=1") > download_at
    assert "DOCLING_ARTIFACTS_PATH=/models/docling" in worker_stage

    worker_env = _compose()["services"]["worker"]["environment"]
    assert worker_env["HF_HUB_OFFLINE"] == "1"
    assert worker_env["DOCLING_ARTIFACTS_PATH"] == "/models/docling"


_SECRET_NAME = re.compile(r"(^|_)(KEY|SECRET|TOKEN|PASSWORD)(_|$)", re.IGNORECASE)


def test_spec11_ac04_no_secret_build_args_or_env_in_images() -> None:
    for dockerfile in (BACKEND / "Dockerfile", FRONTEND / "Dockerfile"):
        for line in dockerfile.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("ARG ", "ENV ")):
                names = re.findall(r"([A-Z_][A-Z0-9_]*)=", stripped) or [stripped.split()[1]]
                leaked = [n for n in names if _SECRET_NAME.search(n)]
                assert not leaked, f"{dockerfile.name}: {stripped}"
            assert not stripped.startswith("COPY .env"), dockerfile.name

    # `.env` never enters a build context or the repo.
    for ignore in (BACKEND / ".dockerignore", FRONTEND / ".dockerignore"):
        assert ".env" in ignore.read_text(encoding="utf-8").splitlines(), ignore
    assert ".env" in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    # The compose file passes secrets only through env_file, never inline.
    for name, svc in _compose()["services"].items():
        for key in svc.get("environment", {}):
            assert not (_SECRET_NAME.search(key) and key != "POSTGRES_PASSWORD"), f"{name}: {key}"


def _tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "-c", "safe.directory=*", "ls-files", "-z"],
            cwd=REPO,
            capture_output=True,
            check=True,
        ).stdout
    except OSError, subprocess.CalledProcessError:
        pytest.skip("git is not available")
    return [REPO / p for p in out.decode().split("\0") if p]


def _env_file_value(name: str) -> str | None:
    env = REPO / ".env"
    if not env.exists():
        return None
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip("\"'") or None
    return None


def test_spec11_ac04_no_secret_value_in_repo() -> None:
    files = _tracked_files()
    assert REPO / ".env" not in files, ".env is tracked"

    example = (REPO / ".env.example").read_text(encoding="utf-8")
    assert re.search(r"^AI_API_KEY=$", example, re.MULTILINE), ".env.example must leave AI_API_KEY empty"

    key = _env_file_value("AI_API_KEY")
    key_shaped = re.compile(rb"\bsk-(?!test-)[A-Za-z0-9_-]{20,}")  # sk-test-… is the fake key in conftest
    for path in files:
        if not path.is_file():
            continue
        data = path.read_bytes()
        assert not key_shaped.search(data), f"{path.relative_to(REPO)} holds an API-key-shaped string"
        if key and len(key) >= 8:
            assert key.encode() not in data, f"{path.relative_to(REPO)} holds the AI_API_KEY value"
