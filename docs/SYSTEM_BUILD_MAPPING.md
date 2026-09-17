# Proposal-to-System Mapping

| Proposal requirement | Implementation |
|---|---|
| Farmers/traders register/authenticate by phone | `/api/auth/register/`, `/api/auth/login/` |
| Current commodity price by market | `/api/prices/` + USSD menu |
| Short-term forecast | `/api/forecasts/` using ARIMA baseline/trend fallback |
| Price submission | `/api/prices/submit/` |
| Alerts | Alert model + API endpoint; telecom sending is provider-dependent |
| Storage/routing recommendation | `/api/recommendations/` |
| Web dashboard | React/Vite dashboard |
| Admin management | Django Admin |
| Policymaker reports | `/api/reports/` CSV export; PDF can be added with ReportLab in deployment if required by supervisor |
| USSD/SMS | Provider-neutral USSD webhook `/api/ussd/` |
| Low-bandwidth | USSD flow has at most 3 choices per screen |
| Modular architecture | models, services, API views and React presentation are separated |
| Pilot markets | Freetown, Bo, Makeni seed data |
| Pilot commodities | Rice, Cassava, Groundnuts seed data |
