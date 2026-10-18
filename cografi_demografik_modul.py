# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - Coğrafi ve Demografik Modül (81 İl Entegrasyonu)
Odak: Türkiye genelindeki tüm 81 ilin coğrafi, demografik ve sosyo-ekonomik verileri
"""
import json
import pandas as pd
from datetime import datetime

class CografiDemografikModul:
    def __init__(self):
        self.output_file = "cografi_demografik_veritabani.json"
        self.excel_file = "TURKIYE_81_IL_VERITABANI.xlsx"
        
        # Türkiye 81 İl Veritabanı
        self.turkiye_illeri = {
            # MARMARA BÖLGESİ (11 İl)
            "01": {"plaka": "01", "il_adi": "Adana", "bolge": "Akdeniz", "alt_bolge": "Çukurova", "nufus": 2250000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi", "Lojistik"], "hedef_kitle": "Genç profesyoneller", "affiliate_uygunluk": 85},
            "34": {"plaka": "34", "il_adi": "İstanbul", "bolge": "Marmara", "alt_bolge": "İstanbul", "nufus": 15500000, "yogunluk": "Çok Yüksek", "ekonomik_seviye": "Çok Gelişmiş", "ana_sektorler": ["Finans", "Turizm", "Teknoloji", "Lojistik"], "hedef_kitle": "Kentsel profesyoneller", "affiliate_uygunluk": 98},
            "06": {"plaka": "06", "il_adi": "Ankara", "bolge": "İç Anadolu", "alt_bolge": "Orta Anadolu", "nufus": 5700000, "yogunluk": "Yüksek", "ekonomik_seviye": "Çok Gelişmiş", "ana_sektorler": ["Kamu", "Eğitim", "Teknoloji", "Savunma"], "hedef_kitle": "Kamu çalışanları", "affiliate_uygunluk": 95},
            "35": {"plaka": "35", "il_adi": "İzmir", "bolge": "Ege", "alt_bolge": "İzmir", "nufus": 4400000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Turizm", "Sanayi", "Tarım", "Denizcilik"], "hedef_kitle": "Turist ve yerel halk", "affiliate_uygunluk": 92},
            "41": {"plaka": "41", "il_adi": "Kocaeli", "bolge": "Marmara", "alt_bolge": "Kocaeli", "nufus": 2000000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Otomotiv", "Kimya", "Lojistik"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 90},
            "16": {"plaka": "16", "il_adi": "Bursa", "bolge": "Marmara", "alt_bolge": "Bursa", "nufus": 3100000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Otomotiv", "Tekstil", "Tarım", "Turizm"], "hedef_kitle": "Sanayi ve tarım kesimi", "affiliate_uygunluk": 88},
            "22": {"plaka": "22", "il_adi": "Edirne", "bolge": "Marmara", "alt_bolge": "Trakya", "nufus": 400000, "yogunluk": "Orta", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm", "Sınır ticareti"], "hedef_kitle": "Sınır ticareti yapanlar", "affiliate_uygunluk": 75},
            "59": {"plaka": "59", "il_adi": "Tekirdağ", "bolge": "Marmara", "alt_bolge": "Trakya", "nufus": 1100000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi", "Turizm"], "hedef_kitle": "Kırsal kentsel karışık", "affiliate_uygunluk": 82},
            "17": {"plaka": "17", "il_adi": "Çanakkale", "bolge": "Marmara", "alt_bolge": "Çanakkale", "nufus": 550000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Turizm", "Tarım", "Denizcilik"], "hedef_kitle": "Turist ve çiftçiler", "affiliate_uygunluk": 78},
            "10": {"plaka": "10", "il_adi": "Balıkesir", "bolge": "Marmara", "alt_bolge": "Balıkesir", "nufus": 1250000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Turizm", "Sanayi"], "hedef_kitle": "Turist ve çiftçiler", "affiliate_uygunluk": 80},
            "77": {"plaka": "77", "il_adi": "Yalova", "bolge": "Marmara", "alt_bolge": "Yalova", "nufus": 280000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Turizm", "Sanayi", "Tarım"], "hedef_kitle": "İstanbul komşuları", "affiliate_uygunluk": 83},
            "54": {"plaka": "54", "il_adi": "Sakarya", "bolge": "Marmara", "alt_bolge": "Sakarya", "nufus": 1100000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Tarım", "Otomotiv"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 84},
            
            # EGE BÖLGESİ (8 İl)
            "09": {"plaka": "09", "il_adi": "Aydın", "bolge": "Ege", "alt_bolge": "Aydın", "nufus": 1100000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Turizm", "Enerji"], "hedef_kitle": "Turist ve çiftçiler", "affiliate_uygunluk": 81},
            "45": {"plaka": "45", "il_adi": "Manisa", "bolge": "Ege", "alt_bolge": "Manisa", "nufus": 1450000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Tarım", "Enerji"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 83},
            "48": {"plaka": "48", "il_adi": "Muğla", "bolge": "Ege", "alt_bolge": "Muğla", "nufus": 1050000, "yogunluk": "Düşük", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Turizm", "Tarım", "Denizcilik"], "hedef_kitle": "Turistler", "affiliate_uygunluk": 89},
            "20": {"plaka": "20", "il_adi": "Denizli", "bolge": "Ege", "alt_bolge": "Denizli", "nufus": 1050000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tekstil", "Sanayi", "Turizm"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 82},
            "03": {"plaka": "03", "il_adi": "Afyonkarahisar", "bolge": "Ege", "alt_bolge": "Afyon", "nufus": 750000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi", "Mermer"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 76},
            "43": {"plaka": "43", "il_adi": "Kütahya", "bolge": "Ege", "alt_bolge": "Kütahya", "nufus": 580000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Sanayi", "Seramik", "Tarım"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 77},
            "64": {"plaka": "64", "il_adi": "Uşak", "bolge": "Ege", "alt_bolge": "Uşak", "nufus": 370000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tekstil", "Sanayi", "Tarım"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 74},
            
            # AKDENİZ BÖLGESİ (8 İl)
            "07": {"plaka": "07", "il_adi": "Antalya", "bolge": "Akdeniz", "alt_bolge": "Antalya", "nufus": 2600000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Turizm", "Tarım", "Sanayi"], "hedef_kitle": "Turistler", "affiliate_uygunluk": 93},
            "31": {"plaka": "31", "il_adi": "Hatay", "bolge": "Akdeniz", "alt_bolge": "Hatay", "nufus": 1600000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi", "Turizm"], "hedef_kitle": "Çiftçiler ve sanayi", "affiliate_uygunluk": 80},
            "32": {"plaka": "32", "il_adi": "Isparta", "bolge": "Akdeniz", "alt_bolge": "Isparta", "nufus": 450000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 75},
            "15": {"plaka": "15", "il_adi": "Burdur", "bolge": "Akdeniz", "alt_bolge": "Burdur", "nufus": 270000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 72},
            "80": {"plaka": "80", "il_adi": "Osmaniye", "bolge": "Akdeniz", "alt_bolge": "Çukurova", "nufus": 550000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 79},
            "46": {"plaka": "46", "il_adi": "Kahramanmaraş", "bolge": "Akdeniz", "alt_bolge": "Kahramanmaraş", "nufus": 1150000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Tarım", "Enerji"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 81},
            
            # İÇ ANADOLU BÖLGESİ (13 İl)
            "26": {"plaka": "26", "il_adi": "Eskişehir", "bolge": "İç Anadolu", "alt_bolge": "Eskişehir", "nufus": 900000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Eğitim", "Sanayi", "Tarım"], "hedef_kitle": "Öğrenci ve sanayi", "affiliate_uygunluk": 86},
            "38": {"plaka": "38", "il_adi": "Kayseri", "bolge": "İç Anadolu", "alt_bolge": "Kayseri", "nufus": 1400000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Tarım", "Turizm"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 85},
            "58": {"plaka": "58", "il_adi": "Sivas", "bolge": "İç Anadolu", "alt_bolge": "Sivas", "nufus": 750000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi", "Eğitim"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 73},
            "71": {"plaka": "71", "il_adi": "Kırşehir", "bolge": "İç Anadolu", "alt_bolge": "Kırşehir", "nufus": 280000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 71},
            "68": {"plaka": "68", "il_adi": "Aksaray", "bolge": "İç Anadolu", "alt_bolge": "Aksaray", "nufus": 430000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 74},
            "51": {"plaka": "51", "il_adi": "Niğde", "bolge": "İç Anadolu", "alt_bolge": "Niğde", "nufus": 370000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi", "Madencilik"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 72},
            "50": {"plaka": "50", "il_adi": "Nevşehir", "bolge": "İç Anadolu", "alt_bolge": "Kapadokya", "nufus": 310000, "yogunluk": "Düşük", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Turizm", "Tarım"], "hedef_kitle": "Turistler", "affiliate_uygunluk": 88},
            "71": {"plaka": "71", "il_adi": "Kırıkkale", "bolge": "İç Anadolu", "alt_bolge": "Kırıkkale", "nufus": 280000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Sanayi", "Tarım"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 73},
            "19": {"plaka": "19", "il_adi": "Çorum", "bolge": "Karadeniz", "alt_bolge": "Çorum", "nufus": 550000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Sanayi", "Tarım"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 76},
            "18": {"plaka": "18", "il_adi": "Çankırı", "bolge": "İç Anadolu", "alt_bolge": "Çankırı", "nufus": 200000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 70},
            "66": {"plaka": "66", "il_adi": "Yozgat", "bolge": "İç Anadolu", "alt_bolge": "Yozgat", "nufus": 420000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 71},
            
            # KARADENİZ BÖLGESİ (18 İl)
            "55": {"plaka": "55", "il_adi": "Samsun", "bolge": "Karadeniz", "alt_bolge": "Orta Karadeniz", "nufus": 1350000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 79},
            "61": {"plaka": "61", "il_adi": "Trabzon", "bolge": "Karadeniz", "alt_bolge": "Doğu Karadeniz", "nufus": 810000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Turizm", "Tarım", "Sanayi"], "hedef_kitle": "Turistler", "affiliate_uygunluk": 84},
            "52": {"plaka": "52", "il_adi": "Ordu", "bolge": "Karadeniz", "alt_bolge": "Orta Karadeniz", "nufus": 760000, "yogunluk": "Orta", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 77},
            "28": {"plaka": "28", "il_adi": "Giresun", "bolge": "Karadeniz", "alt_bolge": "Doğu Karadeniz", "nufus": 450000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 75},
            "53": {"plaka": "53", "il_adi": "Rize", "bolge": "Karadeniz", "alt_bolge": "Doğu Karadeniz", "nufus": 350000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 74},
            "08": {"plaka": "08", "il_adi": "Artvin", "bolge": "Karadeniz", "alt_bolge": "Doğu Karadeniz", "nufus": 170000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 70},
            "57": {"plaka": "57", "il_adi": "Sinop", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 200000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 71},
            "05": {"plaka": "05", "il_adi": "Amasya", "bolge": "Karadeniz", "alt_bolge": "Orta Karadeniz", "nufus": 340000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 73},
            "60": {"plaka": "60", "il_adi": "Tokat", "bolge": "Karadeniz", "alt_bolge": "Orta Karadeniz", "nufus": 620000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 75},
            "67": {"plaka": "67", "il_adi": "Zonguldak", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 580000, "yogunluk": "Orta", "ekonomik_seviye": "Orta", "ana_sektorler": ["Madencilik", "Sanayi"], "hedef_kitle": "Madenciler", "affiliate_uygunluk": 74},
            "78": {"plaka": "78", "il_adi": "Karabük", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 260000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Sanayi", "Madencilik"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 72},
            "74": {"plaka": "74", "il_adi": "Bartın", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 200000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 70},
            "37": {"plaka": "37", "il_adi": "Kastamonu", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 380000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 72},
            "81": {"plaka": "81", "il_adi": "Düzce", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 400000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Tarım"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 78},
            "14": {"plaka": "14", "il_adi": "Bolu", "bolge": "Karadeniz", "alt_bolge": "Batı Karadeniz", "nufus": 300000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi", "Turizm"], "hedef_kitle": "Turistler", "affiliate_uygunluk": 76},
            
            # DOĞU ANADOLU BÖLGESİ (14 İl)
            "25": {"plaka": "25", "il_adi": "Erzurum", "bolge": "Doğu Anadolu", "alt_bolge": "Erzurum", "nufus": 770000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Eğitim", "Turizm", "Sanayi"], "hedef_kitle": "Öğrenci ve turist", "affiliate_uygunluk": 76},
            "24": {"plaka": "24", "il_adi": "Erzincan", "bolge": "Doğu Anadolu", "alt_bolge": "Erzincan", "nufus": 230000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 71},
            "04": {"plaka": "04", "il_adi": "Ağrı", "bolge": "Doğu Anadolu", "alt_bolge": "Ağrı", "nufus": 530000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Hayvancılık"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 65},
            "36": {"plaka": "36", "il_adi": "Kars", "bolge": "Doğu Anadolu", "alt_bolge": "Kars", "nufus": 280000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 68},
            "76": {"plaka": "76", "il_adi": "Iğdır", "bolge": "Doğu Anadolu", "alt_bolge": "Iğdır", "nufus": 200000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Sınır ticareti"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 66},
            "75": {"plaka": "75", "il_adi": "Ardahan", "bolge": "Doğu Anadolu", "alt_bolge": "Ardahan", "nufus": 100000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Sınır ticareti"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 63},
            "65": {"plaka": "65", "il_adi": "Van", "bolge": "Doğu Anadolu", "alt_bolge": "Van", "nufus": 1100000, "yogunluk": "Orta", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 72},
            "49": {"plaka": "49", "il_adi": "Muş", "bolge": "Doğu Anadolu", "alt_bolge": "Muş", "nufus": 410000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Hayvancılık"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 64},
            "13": {"plaka": "13", "il_adi": "Bitlis", "bolge": "Doğu Anadolu", "alt_bolge": "Bitlis", "nufus": 350000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Hayvancılık"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 63},
            "30": {"plaka": "30", "il_adi": "Hakkâri", "bolge": "Doğu Anadolu", "alt_bolge": "Hakkâri", "nufus": 280000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Hayvancılık"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 62},
            "62": {"plaka": "62", "il_adi": "Tunceli", "bolge": "Doğu Anadolu", "alt_bolge": "Tunceli", "nufus": 80000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 60},
            "12": {"plaka": "12", "il_adi": "Bingöl", "bolge": "Doğu Anadolu", "alt_bolge": "Bingöl", "nufus": 270000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Hayvancılık"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 63},
            "23": {"plaka": "23", "il_adi": "Elazığ", "bolge": "Doğu Anadolu", "alt_bolge": "Elazığ", "nufus": 580000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sanayi", "Eğitim"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 73},
            "44": {"plaka": "44", "il_adi": "Malatya", "bolge": "Doğu Anadolu", "alt_bolge": "Malatya", "nufus": 810000, "yogunluk": "Orta", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 78},
            
            # GÜNEYDOĞU ANADOLU BÖLGESİ (9 İl)
            "27": {"plaka": "27", "il_adi": "Gaziantep", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Gaziantep", "nufus": 2100000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Sanayi", "Tarım", "Turizm"], "hedef_kitle": "Sanayi çalışanları", "affiliate_uygunluk": 87},
            "63": {"plaka": "63", "il_adi": "Şanlıurfa", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Şanlıurfa", "nufus": 2100000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Turizm", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 82},
            "21": {"plaka": "21", "il_adi": "Diyarbakır", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Diyarbakır", "nufus": 1700000, "yogunluk": "Yüksek", "ekonomik_seviye": "Gelişmiş", "ana_sektorler": ["Tarım", "Sanayi", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 80},
            "47": {"plaka": "47", "il_adi": "Mardin", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Mardin", "nufus": 850000, "yogunluk": "Orta", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 76},
            "72": {"plaka": "72", "il_adi": "Batman", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Batman", "nufus": 620000, "yogunluk": "Orta", "ekonomik_seviye": "Orta", "ana_sektorler": ["Petrol", "Sanayi"], "hedef_kitle": "Petrol çalışanları", "affiliate_uygunluk": 74},
            "73": {"plaka": "73", "il_adi": "Siirt", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Siirt", "nufus": 330000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Sanayi"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 68},
            "56": {"plaka": "56", "il_adi": "Şırnak", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Şırnak", "nufus": 100000, "yogunluk": "Düşük", "ekonomik_seviye": "Düşük", "ana_sektorler": ["Tarım", "Sınır ticareti"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 62},
            "79": {"plaka": "79", "il_adi": "Kilis", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Kilis", "nufus": 150000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Sınır ticareti"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 67},
            "02": {"plaka": "02", "il_adi": "Adıyaman", "bolge": "Güneydoğu Anadolu", "alt_bolge": "Adıyaman", "nufus": 650000, "yogunluk": "Düşük", "ekonomik_seviye": "Orta", "ana_sektorler": ["Tarım", "Turizm"], "hedef_kitle": "Çiftçiler", "affiliate_uygunluk": 75}
        }
        
        # Yerel Niş Profillendirme (DNP) Matrisi
        self.dnp_matrisi = {
            "kentsel_profesyonel": {
                "anahtar_kelimeler": ["iş fırsatı", "kariyer", "networking", "freelance", "uzaktan çalışma"],
                "hedef_kitle": "25-45 yaş, üniversite mezunu, kentli",
                "affiliate_uygunluk": 90
            },
            "sanayi_calisani": {
                "anahtar_kelimeler": ["iş ilanı", "fabrika işi", "üretim", "kalite kontrol", "vardiya"],
                "hedef_kitle": "30-55 yaş, teknik eğitim, sanayi bölgesi",
                "affiliate_uygunluk": 75
            },
            "ciftci": {
                "anahtar_kelimeler": ["tarım", "tohum", "gübre", "hasat", "tarım desteği", "kredi"],
                "hedef_kitle": "35-65 yaş, kırsal, tarım işçisi",
                "affiliate_uygunluk": 65
            },
            "turist": {
                "anahtar_kelimeler": ["tatil", "otel", "tur", "gezi", "yeme içme", "aktivite"],
                "hedef_kitle": "20-60 yaş, şehir dışı, seyahat sever",
                "affiliate_uygunluk": 85
            },
            "ogrenci": {
                "anahtar_kelimeler": ["ders", "sınav", "burs", "yurt", "kampüs", "staj"],
                "hedef_kitle": "18-25 yaş, üniversite öğrencisi",
                "affiliate_uygunluk": 70
            },
            "kamu_calisani": {
                "anahtar_kelimeler": ["memur", "kadro", "sınav", "atama", "maaş"],
                "hedef_kitle": "25-55 yaş, kamu kurumu çalışanı",
                "affiliate_uygunluk": 80
            }
        }

    def il_bilgisi_getir(self, plaka_kodu):
        """Plaka koduna göre il bilgisi döndürür."""
        return self.turkiye_illeri.get(str(plaka_kodu).zfill(2))

    def il_adi_ile_bul(self, il_adi):
        """İl adına göre plaka kodunu döndürür."""
        for plaka, veri in self.turkiye_illeri.items():
            if veri["il_adi"].lower() == il_adi.lower():
                return plaka
        return None

    def bolge_illeri_getir(self, bolge):
        """Bölgeye göre illeri döndürür."""
        return {k: v for k, v in self.turkiye_illeri.items() if v["bolge"] == bolge}

    def ekonomik_seviye_illeri_getir(self, seviye):
        """Ekonomik seviyeye göre illeri döndürür."""
        return {k: v for k, v in self.turkiye_illeri.items() if v["ekonomik_seviye"] == seviye}

    def dnp_profili_olustur(self, il_plakasi):
        """İl için yerel niş profili oluşturur."""
        il_bilgisi = self.il_bilgisi_getir(il_plakasi)
        if not il_bilgisi:
            return None
        
        # İl sosyo-ekonomik dinamiklerine göre profil seçimi
        if il_bilgisi["ekonomik_seviye"] == "Çok Gelişmiş" and il_bilgisi["yogunluk"] in ["Yüksek", "Çok Yüksek"]:
            profil = "kentsel_profesyonel"
        elif "Sanayi" in il_bilgisi["ana_sektorler"]:
            profil = "sanayi_calisani"
        elif "Turizm" in il_bilgisi["ana_sektorler"]:
            profil = "turist"
        elif "Tarım" in il_bilgisi["ana_sektorler"] and il_bilgisi["yogunluk"] == "Düşük":
            profil = "ciftci"
        elif "Eğitim" in il_bilgisi["ana_sektorler"]:
            profil = "ogrenci"
        elif il_bilgisi["il_adi"] == "Ankara":
            profil = "kamu_calisani"
        else:
            profil = "kentsel_profesyonel"
        
        return {
            "Il_Bilgisi": il_bilgisi,
            "DNP_Profili": profil,
            "Profil_Detaylari": self.dnp_matrisi[profil]
        }

    def tum_iller_raporu_olustur(self):
        """Tüm 81 il için kapsamlı rapor oluşturur."""
        tum_rapor = []
        
        for plaka, il_verisi in self.turkiye_illeri.items():
            dnp_profili = self.dnp_profili_olustur(plaka)
            
            tum_rapor.append({
                "Plaka": plaka,
                "Il_Adi": il_verisi["il_adi"],
                "Bolge": il_verisi["bolge"],
                "Alt_Bolge": il_verisi["alt_bolge"],
                "Nufus": il_verisi["nufus"],
                "Yogunluk": il_verisi["yogunluk"],
                "Ekonomik_Seviye": il_verisi["ekonomik_seviye"],
                "Ana_Sektorler": ", ".join(il_verisi["ana_sektorler"]),
                "Hedef_Kitle": il_verisi["hedef_kitle"],
                "Affiliate_Uygunluk": il_verisi["affiliate_uygunluk"],
                "DNP_Profili": dnp_profili["DNP_Profili"] if dnp_profili else "Belirsiz",
                "Anahtar_Kelimeler": ", ".join(dnp_profili["Profil_Detaylari"]["anahtar_kelimeler"]) if dnp_profili else ""
            })
        
        return tum_rapor

    def veritabani_kaydet(self):
        """Veritabanını JSON ve Excel olarak kaydeder."""
        # JSON Kayıt
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.turkiye_illeri, f, ensure_ascii=False, indent=4)
        
        # Excel Kayıt
        df = pd.DataFrame(self.tum_iller_raporu_olustur())
        df.to_excel(self.excel_file, index=False)
        
        return True
