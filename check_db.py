#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os
from pathlib import Path

# Veritabanı yollarını kontrol et
db_paths = [
    "database.db",
    "trm_dashboard.db"
]

base_dir = Path(__file__).parent
print(f"Base directory: {base_dir}")

for db_rel_path in db_paths:
    db_path = base_dir / db_rel_path
    if db_path.exists():
        print(f"\n{'='*50}")
        print(f"Veritabanı: {db_path}")
        print(f"{'='*50}")
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Tabloları listele
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Tablolar: {tables}")
            
            # Her tablo için schema bilgisi
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"\n  {table}:")
                for col in columns:
                    print(f"    - {col[1]} ({col[2]})")
            
            conn.close()
        except Exception as e:
            print(f"Hata: {e}")
    else:
        print(f"\nVeritabanı bulunamadı: {db_path}")
