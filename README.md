# Sierra Leone AgriMarket Intelligence Platform — Enhanced Group 4 Build

This is the enhanced academic prototype aligned with the Group 4 project specification: food price forecasting + supply-chain optimization + low-bandwidth access.

## Stack
- Django 5.2 + Django REST Framework
- React + Vite + Recharts
- PostgreSQL-ready / SQLite for local development
- statsmodels, scikit-learn, optional XGBoost, PuLP
- WhiteNoise for production static files
- Render deployment configuration

## Major modules
1. Authentication and role management
2. Market and commodity data
3. Price import and validation
4. Climate and macroeconomic indicators
5. Multi-model forecasting (1–12 weeks)
6. Forecast evaluation (MAE/RMSE/MAPE)
7. Supply-chain transportation optimization
8. Blocked-road and demand-shock scenarios
9. Market opportunity recommendations
10. Early-warning price alerts
11. PDF/CSV reporting
12. USSD simulator and SMS subscription preference
13. Django Administration

## Demo login
Username: `admin`
Password: `admin123`

Change the password before any real deployment.

## Local setup
### Backend
```text
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### Frontend
```text
cd frontend
npm install
npm run dev
```

The frontend uses `http://127.0.0.1:8000/api` in development.

## Production
The Render build creates the React production bundle and collects it into Django/WhiteNoise static storage. The Vite production base is `/static/`, preventing the previous Render white-screen asset problem.

See `docs/PDF_FEATURE_IMPLEMENTATION.md` for the exact mapping between the project specification and this implementation.
