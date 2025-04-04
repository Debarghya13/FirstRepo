import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import os

class IndianMarketData:
    def __init__(self):
        self.indices = {
            '^BSESN': 'SENSEX',
            '^NSEI': 'NIFTY 50',
            "RELIANCE.NS" : "Reliance",
            "TCS.NS" : "TCS",
            "HDFCBANK.NS" : "HDFC Bank",
            "SBIN.NS" : "SBI",
            "RVNL.NS" : "Rail Vikas Nigam",
            "COCHINSHIP.NS" : "Cochin Shipyard",
            "EXIDEIND.NS" : "Exide Industries",
            "TATAMOTORS.NS" : "Tata Motors",
            "ITC.NS" : "ITC",
            "HINDUNILVR.NS" : "Hindustan Unilever",
            "HUDCO.NS" : "HUDCO",
            "GVT&D.NS" : "GE Vernova T&D",
            "PFC.NS" : "Power Finance Corporation",
            "EIHOTEL.NS" : "EIH Limited",
            "CARBORUNIV.NS" : "Carborundum Universal",
            "BHEL.NS" : "Bharat Heavy Electricals Limited",
            "BEL.NS" : "Bharat Electronics",
            "BDL.NS" : "Bharat Dynamics",
            "BAJAJHFL.NS" : "Bajaj Housing Finance",
        }
        self.data = {}
    
    def fetch_index_data(self, symbol, period="5y", interval="1d"):
        """Fetch data for given market index"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            # Convert timezone-aware datetime to timezone-naive
            df.index = df.index.tz_localize(None)
            
            if df.empty:
                st.error(f"No data found for {self.indices.get(symbol, symbol)}")
                return None
            
            # Add company name column
            df['Index'] = self.indices.get(symbol, symbol)
                
            self.data[symbol] = df
            return df
            
        except Exception as e:
            st.error(f"Error fetching data for {self.indices.get(symbol, symbol)}: {str(e)}")
            return None
    
    def save_to_excel(self, filename="market_data_5y.xlsx"):
        """Save all fetched data to Excel file with multiple sheets"""
        try:
            if not self.data:
                print("No data available to save")
                return False
                
            # Create Excel writer object
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Combine all data into one dataframe
                all_data = pd.concat(self.data.values())
                all_data.to_excel(writer, sheet_name='Market_Data')
            
            print(f"Data saved successfully to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving data to Excel: {str(e)}")
            return False

# Test the code
if __name__ == "__main__":
    market = IndianMarketData()
    
    # Fetch 5-year data for all indices
    print("Fetching 5-year market data...")
    success = True
    
    for symbol in market.indices:
        data = market.fetch_index_data(symbol, period="5y")
        if data is None:
            success = False
            
    if success:
        # Save to Excel
        market.save_to_excel()