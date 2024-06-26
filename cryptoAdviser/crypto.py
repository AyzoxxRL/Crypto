# crypto_analyzer.py

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def fetch_crypto_data(crypto_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data['prices']
    return pd.DataFrame(prices, columns=['timestamp', 'price'])

def calculate_moving_averages(df, short_window=5, long_window=20):
    df['short_mavg'] = df['price'].rolling(window=short_window).mean()
    df['long_mavg'] = df['price'].rolling(window=long_window).mean()
    return df

def calculate_rsi(df, window=14):
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def calculate_bollinger_bands(df, window=20):
    df['middle_band'] = df['price'].rolling(window=window).mean()
    df['upper_band'] = df['middle_band'] + 2 * df['price'].rolling(window=window).std()
    df['lower_band'] = df['middle_band'] - 2 * df['price'].rolling(window=window).std()
    return df

def generate_signals(df, short_window, long_window):
    df['signal'] = 0
    df.loc[df.index[short_window:], 'signal'] = np.where(
        df['short_mavg'][short_window:] > df['long_mavg'][short_window:], 1, 0
    )
    df['position'] = df['signal'].diff()
    return df

def plot_data(df, crypto_id):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot des prix et des moyennes mobiles
    ax1.plot(df.index, df['price'], label='Prix', color='blue')
    ax1.plot(df.index, df['short_mavg'], label='Moyenne Mobile Courte', color='red')
    ax1.plot(df.index, df['long_mavg'], label='Moyenne Mobile Longue', color='green')
    ax1.plot(df.index, df['upper_band'], label='Bande de Bollinger Supérieure', color='orange')
    ax1.plot(df.index, df['middle_band'], label='Bande de Bollinger Moyenne', color='purple')
    ax1.plot(df.index, df['lower_band'], label='Bande de Bollinger Inférieure', color='orange')
    ax1.set_title(f'Prix de {crypto_id.capitalize()} avec Moyennes Mobiles et Bandes de Bollinger')
    ax1.set_ylabel('Prix (USD)')
    ax1.legend()
    
    # Plot du RSI
    ax2.plot(df.index, df['rsi'], label='RSI', color='magenta')
    ax2.axhline(30, linestyle='--', alpha=0.5, color='red')
    ax2.axhline(70, linestyle='--', alpha=0.5, color='red')
    ax2.set_title('Indice de Force Relative (RSI)')
    ax2.set_ylabel('RSI')
    ax2.set_xlabel('Date')
    ax2.legend()
    
    plt.tight_layout()
    plt.show()

def provide_advice(df):
    for index, row in df.iterrows():
        if row['position'] == 1:
            print(f"{index.date()}: Acheter à {row['price']:.2f} USD")
        elif row['position'] == -1:
            print(f"{index.date()}: Vendre à {row['price']:.2f} USD")
        else:
            if row['rsi'] < 30:
                print(f"{index.date()}: RSI bas ({row['rsi']:.2f}), possible opportunité d'achat bientôt.")
            elif row['rsi'] > 70:
                print(f"{index.date()}: RSI élevé ({row['rsi']:.2f}), possible opportunité de vente bientôt.")
            else:
                print(f"{index.date()}: Attendre. Prix actuel: {row['price']:.2f} USD")

def main():
    crypto_id = input("Entrez l'ID de la cryptomonnaie (ex: bitcoin, ethereum) : ")
    days = int(input("Entrez le nombre de jours de données à récupérer : "))
    
    df = fetch_crypto_data(crypto_id, days)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    short_window = 5
    long_window = 20
    
    df = calculate_moving_averages(df, short_window, long_window)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    df = generate_signals(df, short_window, long_window)
    
    print("Recommandations d'achat/vente :")
    provide_advice(df)
    
    plot_data(df, crypto_id)

if __name__ == "__main__":
    main()