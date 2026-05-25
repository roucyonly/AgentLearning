# Turn360 餐饮创业 Agent MVP

This repository contains the MVP implementation for a restaurant entrepreneurship agent focused on:

```text
开店前：地址评定 + 选品 + 算账
```

## Structure

```text
backend/   FastAPI API shell and pure Python MVP engines
frontend/  React + Vite mobile-first UI
docs/      Technical design, UI maps, QA plans, and seed cases
```

## Backend

Install dependencies:

```powershell
cd backend
python -m pip install -r requirements.txt
```

Run API:

```powershell
uvicorn app.main:app --reload
```

Run core tests without FastAPI dependencies:

```powershell
$env:PYTHONPATH="D:\AgentLearning\Turn360Agent\backend"
python -m unittest discover -s backend\tests -v
```

## Frontend

Install dependencies:

```powershell
cd frontend
npm install
```

Run UI:

```powershell
npm run dev
```

Open `http://127.0.0.1:5173`.

## Current MVP

- Pre-opening finance calculation.
- Target breakeven revenue, payback revenue, order target, and cash reserve.
- Seed case loader.
- Mock location scoring.
- Basic category intelligence.
- User UI, Report UI, Debug UI, and Admin UI shells.

