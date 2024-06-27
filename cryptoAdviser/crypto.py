import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import webbrowser
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

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

def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
    df['ema_short'] = df['price'].ewm(span=short_window, adjust=False).mean()
    df['ema_long'] = df['price'].ewm(span=long_window, adjust=False).mean()
    df['macd'] = df['ema_short'] - df['ema_long']
    df['macd_signal'] = df['macd'].ewm(span=signal_window, adjust=False).mean()
    return df

def generate_signals(df, short_window, long_window):
    df['signal'] = 0
    df.loc[df.index[short_window:], 'signal'] = np.where(
        (df['short_mavg'][short_window:] > df['long_mavg'][short_window:]) &
        (df['macd'][short_window:] > df['macd_signal'][short_window:]) &
        (df['rsi'][short_window:] < 30), 1, 0
    )
    df.loc[df.index[short_window:], 'signal'] = np.where(
        (df['short_mavg'][short_window:] < df['long_mavg'][short_window:]) &
        (df['macd'][short_window:] < df['macd_signal'][short_window:]) &
        (df['rsi'][short_window:] > 70), -1, df['signal'][short_window:]
    )
    df['position'] = df['signal'].diff()
    return df

def plot_data(df, crypto_id):
    plt.close('all')
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
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
    
    # Ajouter des annotations pour les signaux d'achat/vente
    for index, row in df.iterrows():
        if row['position'] == 1:
            ax1.annotate('Acheter', xy=(index, row['price']), xytext=(index, row['price'] + 0.05),
                         arrowprops=dict(facecolor='red', shrink=0.05), color='red')
        elif row['position'] == -1:
            ax1.annotate('Vendre', xy=(index, row['price']), xytext=(index, row['price'] + 0.05),
                         arrowprops=dict(facecolor='green', shrink=0.05), color='green')
    
    # Ajouter des lignes de tendance
    ax1.plot(df.index, df['price'].rolling(window=30).min(), color='green', linestyle='--', label='Meilleur prix d\'achat')
    ax1.plot(df.index, df['price'].rolling(window=30).max(), color='red', linestyle='--', label='Meilleur prix de vente')
    
    # Ajouter des flèches pour indiquer les mouvements de prix
    for i in range(1, len(df)):
        if df['price'].iloc[i] > df['price'].iloc[i-1]:
            ax1.annotate('', xy=(df.index[i], df['price'].iloc[i]), xytext=(df.index[i-1], df['price'].iloc[i-1]),
                         arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=5))
        else:
            ax1.annotate('', xy=(df.index[i], df['price'].iloc[i]), xytext=(df.index[i-1], df['price'].iloc[i-1]),
                         arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=5))
    
    # Ajouter des annotations spécifiques pour les points d'achat et de vente
    buy_points = df[df['position'] == 1].index
    sell_points = df[df['position'] == -1].index
    
    for point in buy_points:
            ax1.annotate('Acheter', xy=(point, df.loc[point, 'price']), xytext=(point, df.loc[point, 'price'] + 0.05),
                 arrowprops=dict(facecolor='red', shrink=0.05), color='red')

    for point in sell_points:
        ax1.annotate('Vendre', xy=(point, df.loc[point, 'price']), xytext=(point, df.loc[point, 'price'] + 0.05),
                     arrowprops=dict(facecolor='blue', shrink=0.05), color='blue')
    
    plt.tight_layout()
    plt.show()
    plt.close(fig)  # Fermer explicitement la figure après l'affichage

def provide_advice(df):
    for index, row in df.iterrows():
        if row['position'] == 1:
            print(f"{index.date()}: Acheter à {row['price']:.2f} USD")
        elif row['position'] == -1:
            print(f"{index.date()}: Vendre à {row['price']:.2f} USD")
        else:
            if row['rsi'] < 30 and row['macd'] > row['macd_signal'] and row['price'] < row['lower_band']:
                print(f"{index.date()}: RSI bas ({row['rsi']:.2f}), possible opportunité d'achat bientôt.")
            elif row['rsi'] > 70 and row['macd'] < row['macd_signal'] and row['price'] > row['upper_band']:
                print(f"{index.date()}: RSI élevé ({row['rsi']:.2f}), possible opportunité de vente bientôt.")
            else:
                print(f"{index.date()}: Attendre. Prix actuel: {row['price']:.2f} USD")

def open_buy_link(crypto_id):
    url = f"https://www.coingecko.com/en/coins/{crypto_id}"
    webbrowser.open(url)

def main():
    cryptos = {
        'bitcoin': 'bitcoin',
        'ethereum': 'ethereum',
        'ripple': 'ripple',
        'litecoin': 'litecoin',
        'cardano': 'cardano',
        'polkadot': 'polkadot',
        'binancecoin': 'binancecoin',
        'dogecoin': 'dogecoin',
        'solana': 'solana',
        'chainlink': 'chainlink'
    }
    
    root = tk.Tk()
    root.title("Analyseur de Cryptomonnaies")
    root.geometry("400x400")
    root.configure(bg="#f0f0f0")
    
    title_label = tk.Label(root, text="Analyseur de Cryptomonnaies", font=("Helvetica", 16, "bold"), bg="#f0f0f0")
    title_label.pack(pady=10)
    
    tk.Label(root, text="Cryptomonnaies disponibles :", font=("Helvetica", 12), bg="#f0f0f0").pack(pady=5)
    
    # Utiliser une combobox pour sélectionner la cryptomonnaie
    crypto_name_var = tk.StringVar()
    crypto_combobox = ttk.Combobox(root, textvariable=crypto_name_var, font=("Helvetica", 12))
    crypto_combobox['values'] = [name.capitalize() for name in cryptos.keys()]
    crypto_combobox.pack(pady=5)
    
    tk.Label(root, text="Entrez le nombre de jours :", font=("Helvetica", 12), bg="#f0f0f0").pack(pady=5)
    days_var = tk.IntVar()
    tk.Entry(root, textvariable=days_var, font=("Helvetica", 12)).pack(pady=5)
    
    def on_analyze():
        crypto_name = crypto_name_var.get().lower()
        crypto_id = cryptos.get(crypto_name)
        
        if not crypto_id:
            messagebox.showerror("Erreur", "Cryptomonnaie non trouvée.")
            return
        
        days = days_var.get()
        
        df = fetch_crypto_data(crypto_id, days)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        short_window = 5
        long_window = 20
        df = calculate_moving_averages(df, short_window, long_window)
        df = calculate_rsi(df)
        df = calculate_bollinger_bands(df)
        df = calculate_macd(df)
        df = generate_signals(df, short_window, long_window)
        print("Recommandations d'achat/vente :")
        provide_advice(df)
        plot_data(df, crypto_id)
    
    analyze_button = tk.Button(root, text="Analyser", command=on_analyze, font=("Helvetica", 12), bg="#4CAF50", fg="white")
    analyze_button.pack(pady=10)

    def on_buy():
        crypto_name = crypto_name_var.get().lower()
        crypto_id = cryptos.get(crypto_name)
        if not crypto_id:
            messagebox.showerror("Erreur", "Cryptomonnaie non trouvée.")
            return
        open_buy_link(crypto_id)

    buy_button = tk.Button(root, text="Acheter", command=on_buy, font=("Helvetica", 12), bg="#2196F3", fg="white")
    buy_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()