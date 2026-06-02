"""
Fetches raw financial data for a ticker via Yahoo Finance.
This runs before any agent — it gives all agents a shared data context.
"""
from typing import Optional
import yfinance as yf


def fetch(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "description": info.get("longBusinessSummary"),
        "currency": info.get("currency"),
        # price & valuation
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "pe_ratio_trailing": info.get("trailingPE"),
        "pe_ratio_forward": info.get("forwardPE"),
        "ev_to_ebitda": info.get("enterpriseToEbitda"),
        "ev_to_revenue": info.get("enterpriseToRevenue"),
        "price_to_book": info.get("priceToBook"),
        # income statement
        "revenue_ttm": info.get("totalRevenue"),
        "ebitda": info.get("ebitda"),
        "gross_margin": info.get("grossMargins"),
        "operating_margin": info.get("operatingMargins"),
        "net_margin": info.get("profitMargins"),
        "revenue_growth_yoy": info.get("revenueGrowth"),
        "earnings_growth_yoy": info.get("earningsGrowth"),
        # balance sheet & cash
        "total_debt": info.get("totalDebt"),
        "cash": info.get("totalCash"),
        "free_cashflow": info.get("freeCashflow"),
        "debt_to_equity": info.get("debtToEquity"),
        # market & sentiment
        "price_52w_high": info.get("fiftyTwoWeekHigh"),
        "price_52w_low": info.get("fiftyTwoWeekLow"),
        "price_change_1y_pct": _price_change(stock, "1y"),
        "short_ratio": info.get("shortRatio"),
        "short_percent_float": info.get("shortPercentOfFloat"),
        # analyst consensus
        "analyst_target_mean": info.get("targetMeanPrice"),
        "analyst_recommendation": info.get("recommendationKey"),
        "analyst_count": info.get("numberOfAnalystOpinions"),
    }


def _price_change(stock: yf.Ticker, period: str) -> Optional[float]:
    try:
        hist = stock.history(period=period)
        if len(hist) < 2:
            return None
        start = hist["Close"].iloc[0]
        end = hist["Close"].iloc[-1]
        return round((end - start) / start * 100, 2)
    except Exception:
        return None
