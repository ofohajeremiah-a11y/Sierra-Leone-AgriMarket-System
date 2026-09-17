# AgriMarket — Simple Windows Run Guide

## Requirements
- Windows 10/11
- Python 3.11–3.13 (64-bit recommended)
- Node.js 18+ LTS
- Internet connection during first setup

## 1. Install Python
Download the Windows installer from https://www.python.org/downloads/windows/
During installation, tick **Add python.exe to PATH**.

## 2. Install Node.js
Download the LTS installer from https://nodejs.org/en/download/

## 3. Extract this project
Right-click the ZIP → **Extract All**.

## 4. Run setup
Open the extracted project folder and double-click **setup_windows.bat**.

The setup script:
- creates `.venv`
- upgrades pip
- installs pinned Python packages from official PyPI
- runs Django migrations
- creates demo data
- checks Django

If setup fails, stop there and send the error text or a screenshot.

## 5. Start backend
Double-click **start_backend.bat**.
Leave that black window open.

Backend address: http://127.0.0.1:8000/
Admin: http://127.0.0.1:8000/admin/

## 6. Start frontend
Double-click **start_frontend.bat**.
Leave that window open.

Open: http://localhost:5173/

## Important
Do not run `start_backend.bat` until `setup_windows.bat` ends with **SUCCESS!**.

## New Frontend Features (Alert & Role Upgrade)

The latest version adds:

- Login screen using the existing Django `/api/auth/login/` endpoint.
- Role-aware navigation for Farmer, Trader, Enumerator, Policymaker and Administrator.
- Automatic alerts when a submitted price changes by 5% or more.
- Warning alerts at 10%+ and critical alerts at 20%+.
- Forecast alerts when the average forecast moves 10% or more away from the latest price.
- Market-opportunity alerts for strong positive transport recommendations.
- Alerts page with severity filters, unread count and Mark Read/Mark All Read.
- Dashboard alert summary and automatic refresh every 10 seconds.
- Market Prices page.
- USSD Simulator that uses the real `/api/ussd/` endpoint.
- Improved price submission form showing whether an automatic alert was created.

### Alert test

1. Sign in as `admin` / `admin123` or as one of the role users created in Django Admin.
2. Open **Price Reports** if the account has that role.
3. Select a market and commodity.
4. Look at the latest price in **Prices**.
5. Submit a new price at least 10% higher or lower than the previous price.
6. Open **Alerts**. A Warning or Critical alert should appear depending on the size of the change.
7. Django Admin also shows the same alert under **Alerts**.

### Important note about roles

The role-aware frontend controls what each role sees in the prototype. Django Admin remains the authoritative administration console. For a production deployment, the API should additionally use authenticated tokens/permissions rather than relying on frontend navigation alone.
