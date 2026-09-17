# Sierra Leone AgriMarket Intelligence Platform

A working academic prototype for collecting agricultural market prices, validating submissions, generating 7-day price forecasts, producing supply-chain recommendations, and exposing a low-bandwidth USSD-style interface.

## Technology
- Backend: Django + Django REST Framework + SQLite (PostgreSQL-ready)
- Forecasting: ARIMA(1,1,1) when sufficient history and `statsmodels` are available; transparent trend fallback otherwise
- Frontend: React + Vite + Recharts
- Admin: Django Admin
- USSD: provider-independent webhook at `/api/ussd/`

## Included pilot data
Markets: Freetown, Bo, Makeni
Commodities: Rice, Cassava, Groundnuts
The seed command creates 28 days of deterministic demonstration prices.

## IDE support

This project is IDE-independent and can be developed in Visual Studio Code or Eclipse with PyDev. The application itself runs from Python/Node commands, not from a specific IDE.

See `RUN_GUIDE.md` for the beginner-friendly setup.

## Windows installation
1. Install Python 3.11+ and Node.js 18+.
2. Double-click `setup_windows.bat`.
3. Double-click `start_backend.bat`.
4. In a second terminal, double-click `start_frontend.bat`.
5. Open the Vite URL shown in the terminal.

### Demo administrator
Username: `admin`
Password: `admin123`

Change this password before any real deployment.

## API endpoints
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET /api/overview/`
- `GET /api/markets/`
- `GET /api/commodities/`
- `GET /api/prices/`
- `POST /api/prices/submit/`
- `GET|POST /api/forecasts/`
- `POST /api/recommendations/`
- `GET /api/alerts/`
- `GET /api/reports/`
- `POST /api/ussd/`
- `/admin/`

## USSD demo
Send an HTTP POST to `/api/ussd/` with `sessionId` and `text`.
Examples of menu progression:
- empty text → main menu
- `1` → commodity menu
- `1*1` → market menu
- `1*1*1` → current Rice price in Freetown
- `2*1*1` → 7-day Rice forecast in Freetown

## Academic integrity
The project does not fabricate evaluation results. Real usability/accuracy percentages should be entered only after the system has been tested with actual participants and data.
