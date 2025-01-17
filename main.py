import requests
import pandas as pd
from datetime import datetime
import time
import json
import os
from typing import Dict, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.exc import SQLAlchemyError

class Base(DeclarativeBase):
    pass

class CryptoPrice(Base):
    __tablename__ = 'crypto_prices'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    price = Column(Float)
    volume_24h = Column(Float)
    percent_change_24h = Column(Float)
    timestamp = Column(DateTime)
    
class TradeSignal(Base):
    __tablename__ = 'trade_signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10))
    signal = Column(String(10))
    timestamp = Column(DateTime)

class DatabaseManager:
    def __init__(self, connection_string):
        #connection string format
        #postgresql://username:password@host:port/database_name
        try:
            self.engine = create_engine(connection_string)
            Base.metadata.create_all(self.engine)
            self.session_factory = sessionmaker(bind=self.engine)
            print("Successfully connected to the database")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def store_crypto_data(self, data: pd.DataFrame):
        #store crypto price data
        with Session(self.engine) as session:
            try:
                for _, row in data.iterrows():
                    crypto_price = CryptoPrice(
                        symbol=row['symbol'],
                        price=row['price'],
                        volume_24h=row['volume_24h'],
                        percent_change_24h=row['percent_change_24h'],
                        timestamp=row['timestamp']
                    )
                    session.add(crypto_price)
                session.commit()
            except SQLAlchemyError as e:
                print(f"Error storing crypto data: {e}")
                session.rollback()
                raise
        

    def store_signals(self, signals: Dict[str, str]):
        #stores trading signals
        with Session(self.engine) as session:
            try:
                for symbol, signal in signals.items():
                    trade_signal = TradeSignal(
                        symbol=symbol,
                        signal=signal,
                        timestamp=datetime.now()
                    )
                    session.add(trade_signal)
                session.commit()
            except SQLAlchemyError as e:
                print(f"Error storing signals: {e}")
                session.rollback()
                raise
    
    def get_recent_prices(self, symbol: str, limit: int = 24):
        #get recent price data for a symbol
        try:
            with Session(self.engine) as session:
                query = session.query(CryptoPrice)\
                    .filter(CryptoPrice.symbol == symbol)\
                    .order_by(CryptoPrice.timestamp.desc())\
                    .limit(limit)
                return pd.read_sql(query.statement, self.engine)
        except SQLAlchemyError as e:
            print(f"Error retrieving price data: {e}")
            return pd.DataFrame()
            
class CryptoDataCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        #self.base_url = "https://sandbox-api.coinmarketcap.com/v1"
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
    def __init__(self,db_manager: DatabaseManager, lookback_periods: int = 24):
        self.db_manager = db_manager
        self.lookback_periods = lookback_periods
    
    def analyze(self, data: pd.DataFrame):
        
        #analyze and generate trading signals based on price movements and volume
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
    #api_key = "b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c" #testing api key
    api_key = os.getenv('COINMARKETCAP_API_KEY') #real api key
    symbols = ['BTC', 'ETH', 'SOL']  # add more symbols as needed
    db_connection_string = os.getenv('AWS_RDS_CONNECTION_STRING')
    try:
        #init
        db_manager = DatabaseManager(db_connection_string)
        collector = CryptoDataCollector(api_key)
        analyzer = TradeAnalyzer(db_manager)
    
        while True:
            try:
                # collect data
                print("\nFetching latest crypto data...")
                data = collector.get_latest_prices(symbols)
                
                if data is not None:
                    db_manager.store_crypto_data(data)

                    # analyze and get trading signals
                    signals = analyzer.analyze(data)
                    
                    #store signals
                    db_manager.store_signals(signals)
                    
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
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()