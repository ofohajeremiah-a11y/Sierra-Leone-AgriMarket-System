# PDF Feature Implementation Map

This build upgrades the earlier AgriMarket prototype toward the 45-page Group 4 project specification.

## Implemented in the software
- Registration, login and role management: Farmer, Trader, Transporter, Field Agent, Policy Maker, Analyst, Administrator.
- Five staple commodities: Rice, Cassava, Maize, Groundnuts, Palm Oil.
- Five pilot markets across Western, Southern, Northern, Eastern and North West regions.
- Historical price records and CSV price import.
- Price validation workflow.
- Climate records: rainfall and temperature.
- Macroeconomic records: exchange rate, CPI, inflation and fuel price.
- Supply/demand records.
- Transport route table with distance, fuel usage, cost, spoilage and blocked-route flag.
- Forecast horizons from 1 to 12 weeks.
- Forecast model comparison: Seasonal Naive, SARIMA, XGBoost (with a gradient-boosting fallback if the optional XGBoost package is unavailable), and a lightweight recurrent LSTM-style forecaster.
- Walk-forward-style holdout evaluation with MAE, RMSE and MAPE.
- Prediction intervals.
- Price-spike and low-price early warnings.
- Transportation optimization with PuLP, supply/demand constraints, fuel cost, route availability, blocked-road scenario and demand-shock scenario.
- Market opportunity recommendations.
- Dashboard, reporting and administration.
- PDF and CSV report export.
- USSD simulator for price and forecast queries.
- SMS alert subscription preference stored in the database.
- English/Krio language preference field for users.
- Responsive web interface for low-bandwidth use.

## External service limitation
Real SMS delivery still requires a telecom/SMS aggregator account, API credentials and a live callback URL. The software includes the subscription and gateway-ready architecture, but it does not invent or embed a real telecom provider credential.

## Data-source limitation
The application contains a reproducible demo dataset for development and presentation. The climate, macroeconomic, price and transport tables are designed so real WFP/HDX, Statistics Sierra Leone, MAFS, Bank of Sierra Leone, CHIRPS or field-survey data can be imported. This build does not claim that live external feeds are already connected.
