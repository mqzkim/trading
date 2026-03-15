---
name: python-project-setup
description: "Python 트레이딩 시스템 프로젝트 초기화. pyproject.toml, 패키지 구조, .env.example, pytest 설정 자동 생성."
argument-hint: "[project-root] [--packages core,personal,commercial,cli]"
user-invocable: true
allowed-tools: "Bash, Read, Write"
---

# Python Project Setup

Python 트레이딩 시스템 프로젝트의 초기 설정을 자동화한다.

## 역할

Python 프로젝트 부트스트래퍼 — 트레이딩 시스템에 필요한 모든 프로젝트 구조, 설정 파일, 의존성 명세를 표준 규격에 맞게 생성한다. PEP 517/518 준수, pytest 통합, 환경 변수 분리를 기본 원칙으로 한다.

## 수행 가능 작업

### 1. pyproject.toml 생성

PEP 517/518 규격의 `pyproject.toml`을 생성한다. setuptools 빌드 백엔드를 사용하며 핵심 의존성과 선택적 의존성 그룹을 포함한다.

생성 내용:
- `[build-system]`: setuptools + wheel
- `[project]`: name, version, python requires (>=3.11), 의존성 목록
- `[project.optional-dependencies]`: ml, dev 그룹 분리
- `[tool.pytest.ini_options]`: testpaths, cov 설정
- `[tool.mypy]`: strict 타입 체크 설정
- `[tool.black]`: line-length 100

의존성 목록:

핵심 (항상 포함):
```
pandas>=2.0
numpy>=1.26
requests>=2.31
yfinance>=0.2
python-dotenv>=1.0
pydantic>=2.0
pydantic-settings>=2.0
typer>=0.9
rich>=13.0
fastapi>=0.104
uvicorn[standard]>=0.24
httpx>=0.25
SQLAlchemy>=2.0
aiosqlite>=0.19
```

개발 (dev 그룹):
```
pytest>=7.4
pytest-cov>=4.1
pytest-asyncio>=0.21
black>=23.0
mypy>=1.5
ruff>=0.1
```

선택 ML (ml 그룹):
```
scikit-learn>=1.3
xgboost>=2.0
hmmlearn>=0.3
optuna>=3.3
```

### 2. Python 패키지 구조 생성

아래 디렉토리 트리를 생성하고 각 패키지에 `__init__.py`를 배치한다.

```
{project-root}/
├── core/
│   ├── __init__.py
│   ├── data/
│   │   └── __init__.py
│   ├── scoring/
│   │   └── __init__.py
│   ├── regime/
│   │   └── __init__.py
│   └── signals/
│       └── __init__.py
├── personal/
│   ├── __init__.py
│   ├── sizer/
│   │   └── __init__.py
│   ├── risk/
│   │   └── __init__.py
│   └── execution/
│       └── __init__.py
├── commercial/
│   ├── __init__.py
│   └── api/
│       └── __init__.py
├── cli/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── unit/
    │   └── __init__.py
    └── integration/
        └── __init__.py
```

`--packages` 인수로 생성할 최상위 패키지를 선택할 수 있다 (기본: 전체).

### 3. .env.example 생성

실제 시크릿 없이 환경 변수 키 목록만 포함하는 `.env.example`을 생성한다. 실제 값은 절대 기록하지 않는다.

생성 내용:
```dotenv
# === 데이터 소스 ===
# Phase 1: EODHD (필수)
EODHD_API_KEY=your_eodhd_api_key_here

# Phase 2: Twelve Data (선택)
TWELVE_DATA_API_KEY=your_twelve_data_api_key_here

# Phase 3: Financial Modeling Prep (선택)
FMP_API_KEY=your_fmp_api_key_here

# === 브로커 ===
# Alpaca Paper Trading
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# KIS (한국투자증권) — 선택
KIS_APP_KEY=your_kis_app_key_here
KIS_APP_SECRET=your_kis_app_secret_here
KIS_ACCOUNT_NUMBER=your_kis_account_number_here

# === 데이터베이스 ===
SQLITE_DB_PATH=./data/trading.db
REDIS_URL=redis://localhost:6379/0

# === API 서버 ===
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=change_me_in_production

# === 환경 ===
# development | paper | production
TRADING_ENV=development
LOG_LEVEL=INFO
```

### 4. pytest 설정

`pyproject.toml` 내 `[tool.pytest.ini_options]` 섹션에 pytest 설정을 포함한다. 별도 `pytest.ini`는 생성하지 않는다 (중복 방지).

설정 내용:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "--cov=core",
    "--cov=personal",
    "--cov=commercial",
    "--cov=cli",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "-v",
]
```

### 5. requirements.txt 생성

pip 호환성을 위한 `requirements.txt`를 생성한다. `pyproject.toml`의 핵심 의존성과 동일한 목록을 유지한다. ML 및 dev 의존성은 별도 파일로 분리한다:

- `requirements.txt`: 핵심 런타임 의존성
- `requirements-dev.txt`: 개발 도구 (pytest, black, mypy, ruff)
- `requirements-ml.txt`: ML 라이브러리 (선택적 설치)

### 6. .gitignore 생성 또는 업데이트

아래 항목이 반드시 포함되어야 한다:

```gitignore
# 환경 변수 — 절대 커밋 금지
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
venv/

# 테스트 / 커버리지
.pytest_cache/
htmlcov/
.coverage

# 데이터 / 캐시
data/
*.db
*.sqlite3

# IDE
.idea/
.vscode/
*.swp
```

## 실행 프로토콜

1. `project-root` 인수 확인 (없으면 현재 디렉토리 사용)
2. `--packages` 인수 파싱 (없으면 전체 패키지 생성)
3. 기존 파일 존재 여부 확인 — 덮어쓰기 전 사용자 확인
4. 순서대로 생성:
   a. 디렉토리 구조 및 `__init__.py`
   b. `pyproject.toml`
   c. `requirements.txt`, `requirements-dev.txt`, `requirements-ml.txt`
   d. `.env.example`
   e. `.gitignore` (기존 파일이 있으면 병합)
5. 생성 완료 후 요약 출력 (생성된 파일 목록, 다음 단계 안내)

## 참고 문서

- `docs/strategy-recommendation.md` — 기술 스택 결정 배경
- `trading/.Codex/AGENTS.md` — 프로젝트 기술 스택 명세
- `docs/cli-skill-implementation-plan.md` — CLI 구현 플랜

## 제약 조건

- 외부 API 키는 `.env` 파일에만 저장한다. `pyproject.toml`, 소스 코드, 테스트 파일에 하드코딩 금지
- `.env`는 반드시 `.gitignore`에 포함되어야 한다. 이 조건을 충족하지 않으면 실행을 중단한다
- 기존 파일을 덮어쓸 때는 반드시 Read로 먼저 읽은 후 Edit으로 수정한다 (Write로 전체 덮어쓰기 금지)
- `requirements.txt`와 `pyproject.toml`의 의존성 버전은 항상 동기화 상태를 유지한다
- Python 최소 버전은 3.11 이상으로 고정한다
