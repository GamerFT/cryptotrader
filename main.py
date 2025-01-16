import requests
import pandas as pd
from datetime import datetime
import time
import json
import os
from typing import Dict, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class DatabaseManager:
    def __init__(self, connection_string):
        #connection string format
        #postgresql://username:password@host:port/database_name
        try:
            self.engine = create_engine(connection_string)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            print("Connected to the database")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

class CryptoDataCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        #self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.base_url = "https://sandbox-api.coinmarketcap.com/v1"
        self.headers = {
            'X-CMC_PRO_API_KEY': api_key,
            'Accept': 'application/json'
        }

    def get_latest_prices(self, symbols):
        #get latest prices for specified cryptocurrency symbols
        try:
            url = f"{self.base_url}/cryptocurrency/quotes/latest"
            parameters = {
                'symbol': ','.join(symbols),
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=self.headers, params=parameters)
            data = response.json()
            
            if response.status_code == 200:
                processed_data = []
                
                for symbol in symbols:
                    if symbol in data['data']:
                        coin_data = data['data'][symbol]
                        processed_data.append({
                            'symbol': symbol,
                            'price': coin_data['quote']['USD']['price'],
                            'volume_24h': coin_data['quote']['USD']['volume_24h'],
                            'percent_change_24h': coin_data['quote']['USD']['percent_change_24h'],
                            'timestamp': datetime.now()
                        })
                
                return pd.DataFrame(processed_data)
            else:
                print(f"Error: {data.get('status', {}).get('error_message')}")
                return None
                
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

class TradeAnalyzer:
    def __init__(self, lookback_periods: int = 24):
        self.lookback_periods = lookback_periods
    
    def analyze(self, data):
        
        #simple analysis based on price movements and volume
        #returns trading signals for each symbol
        
        signals = {}
        
        for symbol in data['symbol'].unique():
            coin_data = data[data['symbol'] == symbol].iloc[0]
            
            # Simple strategy based on 24h performance and volume
            if (coin_data['percent_change_24h'] > 5 and 
                coin_data['volume_24h'] > 1000000):
                signals[symbol] = 'BUY'
            elif coin_data['percent_change_24h'] < -5:
                signals[symbol] = 'SELL'
            else:
                signals[symbol] = 'HOLD'
                
        return signals

def main():
    # initialize with API key
    api_key = "b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c" #testing api key
    #api_key = "xxx" #real api key
    symbols = ['BTC', 'ETH', 'SOL']  # add more symbols as needed
    
    collector = CryptoDataCollector(api_key)
    analyzer = TradeAnalyzer()
    
    while True:
        try:
            # collect data
            print("\nFetching latest crypto data...")
            data = collector.get_latest_prices(symbols)
            
            if data is not None:
                # analyze and get trading signals
                signals = analyzer.analyze(data)
                
                
                print("\nCurrent Data:")
                print(data.to_string())
                print("\nTrading Signals:")
                for symbol, signal in signals.items():
                    print(f"{symbol}: {signal}")
            
            # wait 5 mins for update
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\nStopping data collection...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)  # wait 1 min before retrying

if __name__ == "__main__":
    main()