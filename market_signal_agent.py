#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Signal Agent - Financial & Piyasa Sinyal Üretimi
- Binance API entegrasyonu (simülasyon modu ile)
- SMA (Simple Moving Average) ve RSI (Relative Strength Index) göstergeleri
- Anlık piyasa sinyalleri ve finansal analiz
"""

import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import time

class MarketSignalAgent:
    def __init__(self, db_path="./data/trm_ticari_analiz.db", use_simulation=True):
        self.db_path = Path(db_path)
        self.use_simulation = use_simulation
        self.signals_history = []
        self.running = False
        self.thread = None
        self._init_database()
        
        # Piyasa verileri simülasyonu için
        self.simulation_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
        self.current_prices = {pair: self._generate_initial_price(pair) for pair in self.simulation_pairs}
        
        # Teknik göstergeler için parametreler
        self.sma_short_period = 9
        self.sma_long_period = 21
        self.rsi_period = 14
        
    def _generate_initial_price(self, pair):
        """Simülasyon için başlangıç fiyatları"""
        base_prices = {
            "BTCUSDT": 45000,
            "ETHUSDT": 3200,
            "BNBUSDT": 320,
            "ADAUSDT": 0.45,
            "XRPUSDT": 0.52
        }
        return base_prices.get(pair, 100) * random.uniform(0.95, 1.05)
    
    def _init_database(self):
        """Market sinyalleri için veritabanı tabloları"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    pair TEXT,
                    current_price REAL,
                    sma_short REAL,
                    sma_long REAL,
                    rsi REAL,
                    signal_type TEXT,
                    confidence REAL,
                    action_recommendation TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    pair TEXT,
                    price REAL,
                    volume REAL
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MarketSignalAgent] Veritabanı hatası: {e}")
    
    def _calculate_sma(self, prices, period):
        """Simple Moving Average hesapla"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def _calculate_rsi(self, prices, period=14):
        """Relative Strength Index hesapla"""
        if len(prices) < period + 1:
            return 50  # Nötr değer
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _generate_price_movement(self, pair):
        """Simüle edilmiş fiyat hareketi"""
        volatility = 0.02  # %2 volatilite
        change = random.uniform(-volatility, volatility)
        new_price = self.current_prices[pair] * (1 + change)
        self.current_prices[pair] = new_price
        return new_price
    
    def _get_price_history(self, pair, limit=50):
        """Fiyat geçmişini al (simülasyon veya veritabanı)"""
        if self.use_simulation:
            # Simülasyon modunda geçmiş fiyatları oluştur
            history = []
            base_price = self.current_prices[pair]
            for i in range(limit):
                change = random.uniform(-0.03, 0.03)
                price = base_price * (1 + change * (limit - i) / limit)
                history.append(price)
            return history
        else:
            # Gerçek API modunda veritabanından oku
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT price FROM price_history 
                    WHERE pair = ? 
                    ORDER BY id DESC LIMIT ?
                ''', (pair, limit))
                rows = cursor.fetchall()
                conn.close()
                return [row[0] for row in reversed(rows)]
            except Exception as e:
                print(f"[MarketSignalAgent] Fiyat geçmişi okuma hatası: {e}")
                return []
    
    def analyze_market_signal(self, pair="BTCUSDT"):
        """Piyasa sinyali analizi"""
        try:
            # Fiyat verisi al
            if self.use_simulation:
                current_price = self._generate_price_movement(pair)
            else:
                current_price = self.current_prices.get(pair, self._generate_initial_price(pair))
            
            # Fiyat geçmişini al
            price_history = self._get_price_history(pair)
            price_history.append(current_price)
            
            # Teknik göstergeleri hesapla
            sma_short = self._calculate_sma(price_history, self.sma_short_period)
            sma_long = self._calculate_sma(price_history, self.sma_long_period)
            rsi = self._calculate_rsi(price_history, self.rsi_period)
            
            # Sinyal tipini belirle
            signal_type = "NEUTRAL"
            confidence = 0.5
            action_recommendation = "HOLD"
            
            if sma_short and sma_long:
                if sma_short > sma_long and rsi < 70:
                    signal_type = "BUY"
                    confidence = 0.75
                    action_recommendation = "ALIM SİNYALİ - Kısa vadeli trend yukarı yönlü"
                elif sma_short < sma_long and rsi > 30:
                    signal_type = "SELL"
                    confidence = 0.75
                    action_recommendation = "SATIM SİNYALİ - Kısa vadeli trend aşağı yönlü"
            
            # RSI bazlı ek analiz
            if rsi > 70:
                signal_type = "SELL"
                action_recommendation = "AŞIRI ALIM BÖLGESİ - Dikkatli olun"
                confidence = 0.8
            elif rsi < 30:
                signal_type = "BUY"
                action_recommendation = "AŞIRI SATIM BÖLGESİ - Fırsat olabilir"
                confidence = 0.8
            
            signal = {
                "timestamp": datetime.now().isoformat(),
                "pair": pair,
                "current_price": round(current_price, 2),
                "sma_short": round(sma_short, 2) if sma_short else None,
                "sma_long": round(sma_long, 2) if sma_long else None,
                "rsi": round(rsi, 2) if rsi else None,
                "signal_type": signal_type,
                "confidence": round(confidence, 2),
                "action_recommendation": action_recommendation
            }
            
            # Veritabanına kaydet
            self._save_signal_to_db(signal)
            
            # Fiyat geçmişine ekle
            self._save_price_to_db(pair, current_price)
            
            self.signals_history.append(signal)
            if len(self.signals_history) > 100:
                self.signals_history.pop(0)
            
            return signal
            
        except Exception as e:
            print(f"[MarketSignalAgent] Sinyal analizi hatası: {e}")
            return None
    
    def _save_signal_to_db(self, signal):
        """Sinyali veritabanına kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO market_signals 
                (timestamp, pair, current_price, sma_short, sma_long, rsi, signal_type, confidence, action_recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (signal["timestamp"], signal["pair"], signal["current_price"],
                  signal["sma_short"], signal["sma_long"], signal["rsi"],
                  signal["signal_type"], signal["confidence"], signal["action_recommendation"]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MarketSignalAgent] Sinyal kayıt hatası: {e}")
    
    def _save_price_to_db(self, pair, price):
        """Fiyatı veritabanına kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history (timestamp, pair, price, volume)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().isoformat(), pair, price, random.uniform(1000, 10000)))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MarketSignalAgent] Fiyat kayıt hatası: {e}")
    
    def get_all_signals(self, limit=20):
        """Tüm sinyalleri getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM market_signals 
                ORDER BY id DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            signals = [dict(zip(columns, row)) for row in rows]
            conn.close()
            return signals
        except Exception as e:
            print(f"[MarketSignalAgent] Sinyal okuma hatası: {e}")
            return []
    
    def get_signal_summary(self):
        """Sinyal özeti"""
        signals = self.get_all_signals(50)
        if not signals:
            return {"message": "Henüz sinyal yok"}
        
        buy_signals = [s for s in signals if s["signal_type"] == "BUY"]
        sell_signals = [s for s in signals if s["signal_type"] == "SELL"]
        neutral_signals = [s for s in signals if s["signal_type"] == "NEUTRAL"]
        
        return {
            "total_signals": len(signals),
            "buy_signals": len(buy_signals),
            "sell_signals": len(sell_signals),
            "neutral_signals": len(neutral_signals),
            "latest_signals": signals[:5],
            "average_confidence": sum(s["confidence"] for s in signals) / len(signals)
        }
    
    def start_background_monitoring(self, interval_seconds=60):
        """Arka planda sürekli izleme başlat"""
        def monitor():
            self.running = True
            while self.running:
                for pair in self.simulation_pairs:
                    signal = self.analyze_market_signal(pair)
                    if signal:
                        print(f"[MarketSignal] {pair}: {signal['signal_type']} - {signal['action_recommendation']}")
                time.sleep(interval_seconds)
        
        if not self.running:
            self.thread = threading.Thread(target=monitor, daemon=True)
            self.thread.start()
            print("[MarketSignalAgent] Arka plan izleme başlatıldı")
    
    def stop_background_monitoring(self):
        """Arka plan izlemeyi durdur"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("[MarketSignalAgent] Arka plan izleme durduruldu")

if __name__ == "__main__":
    agent = MarketSignalAgent(use_simulation=True)
    print("[OK] Market Signal Agent başlatıldı")
    
    # Test sinyali
    signal = agent.analyze_market_signal("BTCUSDT")
    print(f"Test Sinyali: {signal}")
    
    # Özet
    summary = agent.get_signal_summary()
    print(f"Sinyal Özeti: {summary}")
