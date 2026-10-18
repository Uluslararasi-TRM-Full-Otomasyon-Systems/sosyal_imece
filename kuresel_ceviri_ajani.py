# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - Küresel Çeviri ve Yerelleştirme Ajanı (Nirvana Seviyesi)
Odak: 130+ ülke ve dil desteği ile akıllı lokalizasyon matrisi
"""
import os
import json
import pandas as pd
from datetime import datetime

class KureselCeviriAjani:
    def __init__(self):
        self.output_file = "kuresel_ceviri_arsivi.json"
        self.excel_file = "KURESLI_CEVIRI_RAPORU.xlsx"
        
        # 130+ ülke ve dil desteği (Asya, Avrupa, Afrika, Amerika, Orta Doğu)
        self.hedef_pazarlar = {
            # Avrupa (40+ ülke)
            "tr": {"ulke": "Türkiye", "dil": "Türkçe", "para_birimi": "TRY", "bolge": "Avrupa", "kulturel_skor": 95},
            "en-gb": {"ulke": "İngiltere", "dil": "İngilizce", "para_birimi": "GBP", "bolge": "Avrupa", "kulturel_skor": 98},
            "en-us": {"ulke": "Amerika Birleşik Devletleri", "dil": "İngilizce", "para_birimi": "USD", "bolge": "Amerika", "kulturel_skor": 97},
            "de": {"ulke": "Almanya", "dil": "Almanca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 96},
            "fr": {"ulke": "Fransa", "dil": "Fransızca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 95},
            "es": {"ulke": "İspanya", "dil": "İspanyolca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 94},
            "it": {"ulke": "İtalya", "dil": "İtalyanca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 93},
            "pt": {"ulke": "Portekiz", "dil": "Portekizce", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 92},
            "nl": {"ulke": "Hollanda", "dil": "Felemenkçe", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 94},
            "pl": {"ulke": "Polonya", "dil": "Lehçe", "para_birimi": "PLN", "bolge": "Avrupa", "kulturel_skor": 91},
            "ru": {"ulke": "Rusya", "dil": "Rusça", "para_birimi": "RUB", "bolge": "Avrupa/Asya", "kulturel_skor": 89},
            "uk": {"ulke": "Ukrayna", "dil": "Ukraynaca", "para_birimi": "UAH", "bolge": "Avrupa", "kulturel_skor": 88},
            "el": {"ulke": "Yunanistan", "dil": "Yunanca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 93},
            "cs": {"ulke": "Çekya", "dil": "Çekçe", "para_birimi": "CZK", "bolge": "Avrupa", "kulturel_skor": 90},
            "ro": {"ulke": "Romanya", "dil": "Rumence", "para_birimi": "RON", "bolge": "Avrupa", "kulturel_skor": 87},
            "hu": {"ulke": "Macaristan", "dil": "Macarca", "para_birimi": "HUF", "bolge": "Avrupa", "kulturel_skor": 89},
            "se": {"ulke": "İsveç", "dil": "İsveççe", "para_birimi": "SEK", "bolge": "Avrupa", "kulturel_skor": 95},
            "no": {"ulke": "Norveç", "dil": "Norveççe", "para_birimi": "NOK", "bolge": "Avrupa", "kulturel_skor": 94},
            "dk": {"ulke": "Danimarka", "dil": "Danca", "para_birimi": "DKK", "bolge": "Avrupa", "kulturel_skor": 93},
            "fi": {"ulke": "Finlandiya", "dil": "Fince", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 92},
            "ch": {"ulke": "İsviçre", "dil": "Almanca/Fransızca/İtalyanca", "para_birimi": "CHF", "bolge": "Avrupa", "kulturel_skor": 96},
            "at": {"ulke": "Avusturya", "dil": "Almanca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 94},
            "be": {"ulke": "Belçika", "dil": "Felemenkçe/Fransızca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 93},
            "bg": {"ulke": "Bulgaristan", "dil": "Bulgarca", "para_birimi": "BGN", "bolge": "Avrupa", "kulturel_skor": 86},
            "hr": {"ulke": "Hırvatistan", "dil": "Hırvatça", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 88},
            "si": {"ulke": "Slovenya", "dil": "Slovence", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 90},
            "sk": {"ulke": "Slovakya", "dil": "Slovakça", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 89},
            "ee": {"ulke": "Estonya", "dil": "Estonca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 88},
            "lv": {"ulke": "Letonya", "dil": "Letonca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 87},
            "lt": {"ulke": "Litvanya", "dil": "Litvanca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 87},
            "is": {"ulke": "İzlanda", "dil": "İzlandaca", "para_birimi": "ISK", "bolge": "Avrupa", "kulturel_skor": 91},
            "ie": {"ulke": "İrlanda", "dil": "İngilizce", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 95},
            "mt": {"ulke": "Malta", "dil": "Maltaca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 89},
            "cy": {"ulke": "Kıbrıs", "dil": "Yunanca/Türkçe", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 90},
            "al": {"ulke": "Arnavutluk", "dil": "Arnavutça", "para_birimi": "ALL", "bolge": "Avrupa", "kulturel_skor": 85},
            "mk": {"ulke": "Kuzey Makedonya", "dil": "Makedonca", "para_birimi": "MKD", "bolge": "Avrupa", "kulturel_skor": 86},
            "ba": {"ulke": "Bosna Hersek", "dil": "Boşnakça", "para_birimi": "BAM", "bolge": "Avrupa", "kulturel_skor": 86},
            "me": {"ulke": "Karadağ", "dil": "Karadağca", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 87},
            "rs": {"ulke": "Sırbistan", "dil": "Sırpça", "para_birimi": "RSD", "bolge": "Avrupa", "kulturel_skor": 87},
            "xk": {"ulke": "Kosova", "dil": "Arnavutça/Sırpça", "para_birimi": "EUR", "bolge": "Avrupa", "kulturel_skor": 85},
            "md": {"ulke": "Moldova", "dil": "Rumence", "para_birimi": "MDL", "bolge": "Avrupa", "kulturel_skor": 84},
            "by": {"ulke": "Belarus", "dil": "Belarusça", "para_birimi": "BYN", "bolge": "Avrupa", "kulturel_skor": 83},
            
            # Asya (40+ ülke)
            "zh-cn": {"ulke": "Çin", "dil": "Çince (Mandarin)", "para_birimi": "CNY", "bolge": "Asya", "kulturel_skor": 92},
            "zh-tw": {"ulke": "Tayvan", "dil": "Çince (Tayvan)", "para_birimi": "TWD", "bolge": "Asya", "kulturel_skor": 90},
            "ja": {"ulke": "Japonya", "dil": "Japonca", "para_birimi": "JPY", "bolge": "Asya", "kulturel_skor": 95},
            "ko": {"ulke": "Güney Kore", "dil": "Korece", "para_birimi": "KRW", "bolge": "Asya", "kulturel_skor": 93},
            "hi": {"ulke": "Hindistan", "dil": "Hintçe", "para_birimi": "INR", "bolge": "Asya", "kulturel_skor": 91},
            "bn": {"ulke": "Bangladeş", "dil": "Bengalce", "para_birimi": "BDT", "bolge": "Asya", "kulturel_skor": 85},
            "ur": {"ulke": "Pakistan", "dil": "Urduca", "para_birimi": "PKR", "bolge": "Asya", "kulturel_skor": 84},
            "id": {"ulke": "Endonezya", "dil": "Endonezce", "para_birimi": "IDR", "bolge": "Asya", "kulturel_skor": 88},
            "ms": {"ulke": "Malezya", "dil": "Malayca", "para_birimi": "MYR", "bolge": "Asya", "kulturel_skor": 89},
            "th": {"ulke": "Tayland", "dil": "Tayca", "para_birimi": "THB", "bolge": "Asya", "kulturel_skor": 90},
            "vi": {"ulke": "Vietnam", "dil": "Vietnamca", "para_birimi": "VND", "bolge": "Asya", "kulturel_skor": 87},
            "ph": {"ulke": "Filipinler", "dil": "Filipince", "para_birimi": "PHP", "bolge": "Asya", "kulturel_skor": 86},
            "my": {"ulke": "Myanmar", "dil": "Birmanca", "para_birimi": "MMK", "bolge": "Asya", "kulturel_skor": 82},
            "kh": {"ulke": "Kamboçya", "dil": "Kmerce", "para_birimi": "KHR", "bolge": "Asya", "kulturel_skor": 81},
            "la": {"ulke": "Laos", "dil": "Lao", "para_birimi": "LAK", "bolge": "Asya", "kulturel_skor": 80},
            "np": {"ulke": "Nepal", "dil": "Nepalce", "para_birimi": "NPR", "bolge": "Asya", "kulturel_skor": 83},
            "lk": {"ulke": "Sri Lanka", "dil": "Sinhala/Tamil", "para_birimi": "LKR", "bolge": "Asya", "kulturel_skor": 84},
            "mm": {"ulke": "Moğolistan", "dil": "Moğolca", "para_birimi": "MNT", "bolge": "Asya", "kulturel_skor": 82},
            "kz": {"ulke": "Kazakistan", "dil": "Kazakça", "para_birimi": "KZT", "bolge": "Asya", "kulturel_skor": 85},
            "uz": {"ulke": "Özbekistan", "dil": "Özbekçe", "para_birimi": "UZS", "bolge": "Asya", "kulturel_skor": 84},
            "kg": {"ulke": "Kırgızistan", "dil": "Kırgızca", "para_birimi": "KGS", "bolge": "Asya", "kulturel_skor": 83},
            "tj": {"ulke": "Tacikistan", "dil": "Tacikçe", "para_birimi": "TJS", "bolge": "Asya", "kulturel_skor": 82},
            "tm": {"ulke": "Türkmenistan", "dil": "Türkmence", "para_birimi": "TMT", "bolge": "Asya", "kulturel_skor": 82},
            "af": {"ulke": "Afganistan", "dil": "Darice/Paştu", "para_birimi": "AFN", "bolge": "Asya", "kulturel_skor": 78},
            "ir": {"ulke": "İran", "dil": "Farsça", "para_birimi": "IRR", "bolge": "Asya", "kulturel_skor": 86},
            "sa": {"ulke": "Suudi Arabistan", "dil": "Arapça", "para_birimi": "SAR", "bolge": "Orta Doğu", "kulturel_skor": 88},
            "ae": {"ulke": "Birleşik Arap Emirlikleri", "dil": "Arapça", "para_birimi": "AED", "bolge": "Orta Doğu", "kulturel_skor": 90},
            "qa": {"ulke": "Katar", "dil": "Arapça", "para_birimi": "QAR", "bolge": "Orta Doğu", "kulturel_skor": 89},
            "kw": {"ulke": "Kuveyt", "dil": "Arapça", "para_birimi": "KWD", "bolge": "Orta Doğu", "kulturel_skor": 88},
            "bh": {"ulke": "Bahreyn", "dil": "Arapça", "para_birimi": "BHD", "bolge": "Orta Doğu", "kulturel_skor": 87},
            "om": {"ulke": "Umman", "dil": "Arapça", "para_birimi": "OMR", "bolge": "Orta Doğu", "kulturel_skor": 86},
            "jo": {"ulke": "Ürdün", "dil": "Arapça", "para_birimi": "JOD", "bolge": "Orta Doğu", "kulturel_skor": 85},
            "lb": {"ulke": "Lübnan", "dil": "Arapça", "para_birimi": "LBP", "bolge": "Orta Doğu", "kulturel_skor": 84},
            "sy": {"ulke": "Suriye", "dil": "Arapça", "para_birimi": "SYP", "bolge": "Orta Doğu", "kulturel_skor": 80},
            "iq": {"ulke": "Irak", "dil": "Arapça/Kürtçe", "para_birimi": "IQD", "bolge": "Orta Doğu", "kulturel_skor": 81},
            "ye": {"ulke": "Yemen", "dil": "Arapça", "para_birimi": "YER", "bolge": "Orta Doğu", "kulturel_skor": 79},
            "il": {"ulke": "İsrail", "dil": "İbranice", "para_birimi": "ILS", "bolge": "Orta Doğu", "kulturel_skor": 91},
            "ps": {"ulke": "Filistin", "dil": "Arapça", "para_birimi": "ILS", "bolge": "Orta Doğu", "kulturel_skor": 82},
            "sg": {"ulke": "Singapur", "dil": "İngilizce/Malayca/Çince", "para_birimi": "SGD", "bolge": "Asya", "kulturel_skor": 94},
            "hk": {"ulke": "Hong Kong", "dil": "Çince/İngilizce", "para_birimi": "HKD", "bolge": "Asya", "kulturel_skor": 93},
            "bn-in": {"ulke": "Hindistan (Bengal)", "dil": "Bengalce", "para_birimi": "INR", "bolge": "Asya", "kulturel_skor": 89},
            "te": {"ulke": "Hindistan (Telugu)", "dil": "Telugu", "para_birimi": "INR", "bolge": "Asya", "kulturel_skor": 88},
            "ta": {"ulke": "Hindistan (Tamil)", "dil": "Tamil", "para_birimi": "INR", "bolge": "Asya", "kulturel_skor": 88},
            "mr": {"ulke": "Hindistan (Marathi)", "dil": "Marathi", "para_birimi": "INR", "bolge": "Asya", "kulturel_skor": 87},
            
            # Afrika (30+ ülke)
            "ar-eg": {"ulke": "Mısır", "dil": "Arapça", "para_birimi": "EGP", "bolge": "Afrika", "kulturel_skor": 85},
            "ar-ma": {"ulke": "Fas", "dil": "Arapça", "para_birimi": "MAD", "bolge": "Afrika", "kulturel_skor": 83},
            "ar-dz": {"ulke": "Cezayir", "dil": "Arapça", "para_birimi": "DZD", "bolge": "Afrika", "kulturel_skor": 82},
            "ar-tn": {"ulke": "Tunus", "dil": "Arapça", "para_birimi": "TND", "bolge": "Afrika", "kulturel_skor": 84},
            "ar-ly": {"ulke": "Libya", "dil": "Arapça", "para_birimi": "LYD", "bolge": "Afrika", "kulturel_skor": 80},
            "en-ng": {"ulke": "Nijerya", "dil": "İngilizce", "para_birimi": "NGN", "bolge": "Afrika", "kulturel_skor": 84},
            "en-za": {"ulke": "Güney Afrika", "dil": "İngilizce/Afrikaans", "para_birimi": "ZAR", "bolge": "Afrika", "kulturel_skor": 86},
            "en-ke": {"ulke": "Kenya", "dil": "İngilizce/Svahili", "para_birimi": "KES", "bolge": "Afrika", "kulturel_skor": 83},
            "en-gh": {"ulke": "Gana", "dil": "İngilizce", "para_birimi": "GHS", "bolge": "Afrika", "kulturel_skor": 82},
            "fr-ma": {"ulke": "Fas (Fransızca)", "dil": "Fransızca", "para_birimi": "MAD", "bolge": "Afrika", "kulturel_skor": 82},
            "fr-dz": {"ulke": "Cezayir (Fransızca)", "dil": "Fransızca", "para_birimi": "DZD", "bolge": "Afrika", "kulturel_skor": 81},
            "fr-tn": {"ulke": "Tunus (Fransızca)", "dil": "Fransızca", "para_birimi": "TND", "bolge": "Afrika", "kulturel_skor": 83},
            "pt-mz": {"ulke": "Mozambik", "dil": "Portekizce", "para_birimi": "MZN", "bolge": "Afrika", "kulturel_skor": 80},
            "pt-ao": {"ulke": "Angola", "dil": "Portekizce", "para_birimi": "AOA", "bolge": "Afrika", "kulturel_skor": 79},
            "sw": {"ulke": "Tanzanya", "dil": "Svahili", "para_birimi": "TZS", "bolge": "Afrika", "kulturel_skor": 81},
            "sw-ke": {"ulke": "Kenya (Svahili)", "dil": "Svahili", "para_birimi": "KES", "bolge": "Afrika", "kulturel_skor": 82},
            "am": {"ulke": "Etiyopya", "dil": "Amharca", "para_birimi": "ETB", "bolge": "Afrika", "kulturel_skor": 80},
            "ha": {"ulke": "Nijerya (Hausa)", "dil": "Hausa", "para_birimi": "NGN", "bolge": "Afrika", "kulturel_skor": 81},
            "yo": {"ulke": "Nijerya (Yoruba)", "dil": "Yoruba", "para_birimi": "NGN", "bolge": "Afrika", "kulturel_skor": 81},
            "ig": {"ulke": "Nijerya (Igbo)", "dil": "Igbo", "para_birimi": "NGN", "bolge": "Afrika", "kulturel_skor": 80},
            "zu": {"ulke": "Güney Afrika (Zulu)", "dil": "Zulu", "para_birimi": "ZAR", "bolge": "Afrika", "kulturel_skor": 83},
            "xh": {"ulke": "Güney Afrika (Xhosa)", "dil": "Xhosa", "para_birimi": "ZAR", "bolge": "Afrika", "kulturel_skor": 82},
            "af": {"ulke": "Güney Afrika (Afrikaans)", "dil": "Afrikaans", "para_birimi": "ZAR", "bolge": "Afrika", "kulturel_skor": 84},
            "so": {"ulke": "Somali", "dil": "Somalice", "para_birimi": "SOS", "bolge": "Afrika", "kulturel_skor": 78},
            "rw": {"ulke": "Ruanda", "dil": "Kinyarwanda", "para_birimi": "RWF", "bolge": "Afrika", "kulturel_skor": 79},
            "mg": {"ulke": "Madagaskar", "dil": "Malgaşça", "para_birimi": "MGA", "bolge": "Afrika", "kulturel_skor": 78},
            "sn": {"ulke": "Senegal", "dil": "Wolof", "para_birimi": "XOF", "bolge": "Afrika", "kulturel_skor": 80},
            "ml": {"ulke": "Mali", "dil": "Bambara", "para_birimi": "XOF", "bolge": "Afrika", "kulturel_skor": 79},
            "bf": {"ulke": "Burkina Faso", "dil": "Mossi", "para_birimi": "XOF", "bolge": "Afrika", "kulturel_skor": 78},
            "ne": {"ulke": "Nijer", "dil": "Hausa", "para_birimi": "XOF", "bolge": "Afrika", "kulturel_skor": 77},
            "td": {"ulke": "Çad", "dil": "Arapça/Fransızca", "para_birimi": "XAF", "bolge": "Afrika", "kulturel_skor": 76},
            "cf": {"ulke": "Orta Afrika Cumhuriyeti", "dil": "Sango/Fransızca", "para_birimi": "XAF", "bolge": "Afrika", "kulturel_skor": 75},
            "cd": {"ulke": "Kongo DR", "dil": "Fransızca/Svahili", "para_birimi": "CDF", "bolge": "Afrika", "kulturel_skor": 74},
            "cg": {"ulke": "Kongo Cumhuriyeti", "dil": "Fransızca", "para_birimi": "XAF", "bolge": "Afrika", "kulturel_skor": 76},
            "cm": {"ulke": "Kamerun", "dil": "Fransızca/İngilizce", "para_birimi": "XAF", "bolge": "Afrika", "kulturel_skor": 77},
            "ci": {"ulke": "Fildişi Sahili", "dil": "Fransızca", "para_birimi": "XOF", "bolge": "Afrika", "kulturel_skor": 79},
            "ug": {"ulke": "Uganda", "dil": "İngilizce", "para_birimi": "UGX", "bolge": "Afrika", "kulturel_skor": 81},
            "et": {"ulke": "Etiyopya (Tigrinya)", "dil": "Tigrinya", "para_birimi": "ETB", "bolge": "Afrika", "kulturel_skor": 79},
            "er": {"ulke": "Eritre", "dil": "Tigrinya/Arapça", "para_birimi": "ERN", "bolge": "Afrika", "kulturel_skor": 77},
            "dj": {"ulke": "Cibuti", "dil": "Somali/Arapça/Fransızca", "para_birimi": "DJF", "bolge": "Afrika", "kulturel_skor": 78},
            
            # Amerika (20+ ülke)
            "en-ca": {"ulke": "Kanada", "dil": "İngilizce/Fransızca", "para_birimi": "CAD", "bolge": "Amerika", "kulturel_skor": 96},
            "fr-ca": {"ulke": "Kanada (Quebec)", "dil": "Fransızca", "para_birimi": "CAD", "bolge": "Amerika", "kulturel_skor": 94},
            "es-mx": {"ulke": "Meksika", "dil": "İspanyolca", "para_birimi": "MXN", "bolge": "Amerika", "kulturel_skor": 90},
            "pt-br": {"ulke": "Brezilya", "dil": "Portekizce", "para_birimi": "BRL", "bolge": "Amerika", "kulturel_skor": 92},
            "es-ar": {"ulke": "Arjantin", "dil": "İspanyolca", "para_birimi": "ARS", "bolge": "Amerika", "kulturel_skor": 88},
            "es-co": {"ulke": "Kolombiya", "dil": "İspanyolca", "para_birimi": "COP", "bolge": "Amerika", "kulturel_skor": 87},
            "es-pe": {"ulke": "Peru", "dil": "İspanyolca", "para_birimi": "PEN", "bolge": "Amerika", "kulturel_skor": 86},
            "es-ve": {"ulke": "Venezuela", "dil": "İspanyolca", "para_birimi": "VES", "bolge": "Amerika", "kulturel_skor": 82},
            "es-cl": {"ulke": "Şili", "dil": "İspanyolca", "para_birimi": "CLP", "bolge": "Amerika", "kulturel_skor": 89},
            "es-ec": {"ulke": "Ekvador", "dil": "İspanyolca", "para_birimi": "USD", "bolge": "Amerika", "kulturel_skor": 85},
            "es-bo": {"ulke": "Bolivya", "dil": "İspanyolca", "para_birimi": "BOB", "bolge": "Amerika", "kulturel_skor": 83},
            "es-py": {"ulke": "Paraguay", "dil": "İspanyolca/Guarani", "para_birimi": "PYG", "bolge": "Amerika", "kulturel_skor": 82},
            "es-uy": {"ulke": "Uruguay", "dil": "İspanyolca", "para_birimi": "UYU", "bolge": "Amerika", "kulturel_skor": 90},
            "es-gt": {"ulke": "Guatemala", "dil": "İspanyolca", "para_birimi": "GTQ", "bolge": "Amerika", "kulturel_skor": 84},
            "es-cu": {"ulke": "Küba", "dil": "İspanyolca", "para_birimi": "CUP", "bolge": "Amerika", "kulturel_skor": 83},
            "es-do": {"ulke": "Dominik Cumhuriyeti", "dil": "İspanyolca", "para_birimi": "DOP", "bolge": "Amerika", "kulturel_skor": 85},
            "es-hn": {"ulke": "Honduras", "dil": "İspanyolca", "para_birimi": "HNL", "bolge": "Amerika", "kulturel_skor": 82},
            "es-sv": {"ulke": "El Salvador", "dil": "İspanyolca", "para_birimi": "USD", "bolge": "Amerika", "kulturel_skor": 83},
            "es-ni": {"ulke": "Nikaragua", "dil": "İspanyolca", "para_birimi": "NIO", "bolge": "Amerika", "kulturel_skor": 81},
            "es-cr": {"ulke": "Kosta Rika", "dil": "İspanyolca", "para_birimi": "CRC", "bolge": "Amerika", "kulturel_skor": 86},
            "es-pa": {"ulke": "Panama", "dil": "İspanyolca", "para_birimi": "USD", "bolge": "Amerika", "kulturel_skor": 87},
            "en-jm": {"ulke": "Jamaika", "dil": "İngilizce", "para_birimi": "JMD", "bolge": "Amerika", "kulturel_skor": 84},
            "en-tt": {"ulke": "Trinidad ve Tobago", "dil": "İngilizce", "para_birimi": "TTD", "bolge": "Amerika", "kulturel_skor": 83},
            "en-bb": {"ulke": "Barbados", "dil": "İngilizce", "para_birimi": "BBD", "bolge": "Amerika", "kulturel_skor": 85},
            "ht": {"ulke": "Haiti", "dil": "Fransızca/Kreol", "para_birimi": "HTG", "bolge": "Amerika", "kulturel_skor": 78},
            "fr-ht": {"ulke": "Haiti (Fransızca)", "dil": "Fransızca", "para_birimi": "HTG", "bolge": "Amerika", "kulturel_skor": 79},
            "nl-sur": {"ulke": "Surinam", "dil": "Felemenkçe", "para_birimi": "SRD", "bolge": "Amerika", "kulturel_skor": 80},
            "nl-aw": {"ulke": "Aruba", "dil": "Felemenkçe", "para_birimi": "AWG", "bolge": "Amerika", "kulturel_skor": 84},
            "nl-cw": {"ulke": "Curaçao", "dil": "Felemenkçe", "para_birimi": "ANG", "bolge": "Amerika", "kulturel_skor": 84},
            "en-gy": {"ulke": "Guyana", "dil": "İngilizce", "para_birimi": "GYD", "bolge": "Amerika", "kulturel_skor": 81},
            "en-bz": {"ulke": "Belize", "dil": "İngilizce", "para_birimi": "BZD", "bolge": "Amerika", "kulturel_skor": 82},
            "es-gq": {"ulke": "Ekvator Ginesi", "dil": "İspanyolca", "para_birimi": "XAF", "bolge": "Afrika", "kulturel_skor": 76}
        }
        
        # Akıllı lokalizasyon matrisi - kültürel ve yerel terminoloji uyarlaması
        self.lokalizasyon_matrisi = {
            "trm_ticari": {
                "tr": "TRM Ticari Ekosistem",
                "en-us": "Social Cooperation",
                "en-gb": "Social Cooperation",
                "de": "Soziale Kooperation",
                "fr": "Coopération Sociale",
                "es": "Cooperación Social",
                "es-mx": "Cooperación Social",
                "pt-br": "Cooperação Social",
                "it": "Cooperazione Sociale",
                "zh-cn": "社会合作",
                "ja": "社会的協力",
                "ko": "사회적 협력",
                "ar": "التعاون الاجتماعي",
                "ru": "Социальное Сотрудничество",
                "hi": "सामाजिक सहयोग",
                "id": "Kerja Sosial",
                "th": "ความร่วมมือทางสังคม",
                "vi": "Hợp tác xã hội",
                "bn": "সামাজিক সহযোগ",
                "ur": "سماجی تعاون",
                "fa": "همکاری اجتماعی",
                "sw": "Ushirikiano wa Kijamii",
                "am": "ማህበራዊ ትብብር"
            },
            "fahri_uye": {
                "tr": "Fahri Üye",
                "en-us": "Honorary Member",
                "en-gb": "Honorary Member",
                "de": "Ehrenmitglied",
                "fr": "Membre Honoraire",
                "es": "Miembro Honorario",
                "es-mx": "Miembro Honorario",
                "pt-br": "Membro Honorário",
                "it": "Membro Onorario",
                "zh-cn": "荣誉会员",
                "ja": "名誉会員",
                "ko": "명예 회원",
                "ar": "عضو فخري",
                "ru": "Почетный член",
                "hi": "मानद सदस्य",
                "id": "Anggota Kehormatan",
                "th": "สมาชิกกิตติมศักดิ์",
                "vi": "Thành viên danh dự",
                "bn": "সম্মানিত সদস্য",
                "ur": "اعزازی رکن",
                "fa": "عضو افتخاری",
                "sw": "Mwanachama wa Heshima",
                "am": "ክቡር አባል"
            },
            "refah_payi": {
                "tr": "Refah Payı",
                "en-us": "Cooperation Share",
                "en-gb": "Cooperation Share",
                "de": "Kooperationsanteil",
                "fr": "Part de Coopération",
                "es": "Cuota de Cooperación",
                "es-mx": "Cuota de Cooperación",
                "pt-br": "Cota de Cooperação",
                "it": "Quota di Cooperazione",
                "zh-cn": "合作份额",
                "ja": "協力シェア",
                "ko": "협력 지분",
                "ar": "حصة التعاون",
                "ru": "Доля Сотрудничества",
                "hi": "सहयोग हिस्सा",
                "id": "Bagian Kerja Sama",
                "th": "ส่วนแบ่งความร่วมมือ",
                "vi": "Phần Hợp tác",
                "bn": "সহযোগ অংশ",
                "ur": "تعاون کا حصہ",
                "fa": "سهم همکاری",
                "sw": "Sehemu ya Ushirikiano",
                "am": "የትብብር ክፍል"
            },
            "ekonomi_analizi": {
                "tr": "Ekonomi Analizi",
                "en-us": "Economic Analysis",
                "en-gb": "Economic Analysis",
                "de": "Wirtschaftsanalyse",
                "fr": "Analyse Économique",
                "es": "Análisis Económico",
                "es-mx": "Análisis Económico",
                "pt-br": "Análise Econômica",
                "it": "Analisi Economica",
                "zh-cn": "经济分析",
                "ja": "経済分析",
                "ko": "경제 분석",
                "ar": "التحليل الاقتصادي",
                "ru": "Экономический анализ",
                "hi": "आर्थिक विश्लेषण",
                "id": "Analisis Ekonomi",
                "th": "การวิเคราะห์ทางเศรษฐกิจ",
                "vi": "Phân tích Kinh tế",
                "bn": "অর্থনৈতিক বিশ্লেষণ",
                "ur": "اقرادی تجزیہ",
                "fa": "تحلیل اقتصادی",
                "sw": "Uchambuzi wa Kiuchumi",
                "am": "የኢኮኖሚ ትንታኔ"
            },
            "sosyal_destek": {
                "tr": "Sosyal Destek",
                "en-us": "Social Support",
                "en-gb": "Social Support",
                "de": "Soziale Unterstützung",
                "fr": "Soutien Social",
                "es": "Apoyo Social",
                "es-mx": "Apoyo Social",
                "pt-br": "Apoio Social",
                "it": "Sostegno Sociale",
                "zh-cn": "社会支持",
                "ja": "社会的支援",
                "ko": "사회적 지원",
                "ar": "الدعم الاجتماعي",
                "ru": "Социальная поддержка",
                "hi": "सामाजिक सहायता",
                "id": "Dukungan Sosial",
                "th": "การสนับสนุนทางสังคม",
                "vi": "Hỗ trợ Xã hội",
                "bn": "সামাজিক সহায়তা",
                "ur": "سماجی مدد",
                "fa": "حمایت اجتماعی",
                "sw": "Msaada wa Kijamii",
                "am": "ማህበራዊ ድጋፍ"
            },
            "e_ticaret": {
                "tr": "E-Ticaret",
                "en-us": "E-Commerce",
                "en-gb": "E-Commerce",
                "de": "E-Commerce",
                "fr": "E-Commerce",
                "es": "Comercio Electrónico",
                "es-mx": "Comercio Electrónico",
                "pt-br": "E-Commerce",
                "it": "E-Commerce",
                "zh-cn": "电子商务",
                "ja": "Eコマース",
                "ko": "전자상거래",
                "ar": "التجارة الإلكترونية",
                "ru": "Электронная коммерция",
                "hi": "ई-कॉमर्स",
                "id": "E-Commerce",
                "th": "อีคอมเมิร์ซ",
                "vi": "Thương mại điện tử",
                "bn": "ই-কমার্স",
                "ur": "ای کامرس",
                "fa": "تجارت الکترونیک",
                "sw": "Biashara ya Mtandao",
                "am": "ኢ-ኮሜርስ"
            }
        }
        
        # Pazar uyumluluk skor faktörleri
        self.pazar_uyumluluk_faktorleri = {
            "ekonomik_stabilite": 0.25,
            "teknoloji_altyapisi": 0.20,
            "kulturel_uygunluk": 0.20,
            "dil_erişimi": 0.15,
            "pazar_buyuklugu": 0.10,
            "regulasyon_ortami": 0.10
        }

    def pazar_uyumluluk_skoru_hesapla(self, dil_kodu):
        """
        Belirtilen ülke için pazar uyumluluk skoru hesaplar.
        """
        if dil_kodu not in self.hedef_pazarlar:
            return 0.0
        
        pazar = self.hedef_pazarlar[dil_kodu]
        kulturel_skor = pazar["kulturel_skor"]
        
        # Bölge bazlı faktörler
        bolge_faktorleri = {
            "Avrupa": 0.95,
            "Amerika": 0.92,
            "Asya": 0.88,
            "Orta Doğu": 0.82,
            "Afrika": 0.75
        }
        
        bolge_skoru = bolge_faktorleri.get(pazar["bolge"], 0.80)
        
        # Nihai skor hesaplama
        nihai_skor = (kulturel_skor / 100) * 0.6 + bolge_skoru * 0.4
        
        return round(nihai_skor * 100, 2)

    def akilli_lokalizasyon(self, kaynak_metin, dil_kodu, icerik_turu="genel"):
        """
        Akıllı lokalizasyon - kültürel ve yerel terminoloji uyarlaması.
        """
        if dil_kodu not in self.hedef_pazarlar:
            return kaynak_metin
        
        lokalize_edilmis = kaynak_metin
        pazar = self.hedef_pazarlar[dil_kodu]
        
        # İçerik türüne göre özel uyarlamalar
        if icerik_turu == "e_ticaret":
            # E-ticaret ürün açıklamaları için uyarlamalar
            lokalize_edilmis = lokalize_edilmis.replace("ürün", "product" if "en" in dil_kodu else "produit" if "fr" in dil_kodu else "produto" if "pt" in dil_kodu else "producto" if "es" in dil_kodu else "منتج" if "ar" in dil_kodu else "محصول" if "fa" in dil_kodu else "محصول")
            lokalize_edilmis = lokalize_edilmis.replace("fiyat", "price" if "en" in dil_kodu else "prix" if "fr" in dil_kodu else "preço" if "pt" in dil_kodu else "precio" if "es" in dil_kodu else "سعر" if "ar" in dil_kodu else "قیمت" if "fa" in dil_kodu else "قیمت")
        
        elif icerik_turu == "refah_esik":
            # Refah eşikleri için uyarlamalar
            lokalize_edilmis = lokalize_edilmis.replace("eşik", "threshold" if "en" in dil_kodu else "seuil" if "fr" in dil_kodu else "limiar" if "pt" in dil_kodu else "umbral" if "es" in dil_kodu else "عتبة" if "ar" in dil_kodu else "آستانه" if "fa" in dil_kodu else "آستانه")
            lokalize_edilmis = lokalize_edilmis.replace("destek", "support" if "en" in dil_kodu else "soutien" if "fr" in dil_kodu else "apoio" if "pt" in dil_kodu else "apoyo" if "es" in dil_kodu else "دعم" if "ar" in dil_kodu else "پشتیبانی" if "fa" in dil_kodu else "پشتیبانی")
        
        elif icerik_turu == "sosyal_rapor":
            # Sosyal destek raporları için uyarlamalar
            lokalize_edilmis = lokalize_edilmis.replace("rapor", "report" if "en" in dil_kodu else "rapport" if "fr" in dil_kodu else "relatório" if "pt" in dil_kodu else "informe" if "es" in dil_kodu else "تقرير" if "ar" in dil_kodu else "گزارش" if "fa" in dil_kodu else "گزارش")
            lokalize_edilmis = lokalize_edilmis.replace("analiz", "analysis" if "en" in dil_kodu else "analyse" if "fr" in dil_kodu else "análise" if "pt" in dil_kodu else "análisis" if "es" in dil_kodu else "تحليل" if "ar" in dil_kodu else "تحلیل" if "fa" in dil_kodu else "تحلیل")
        
        # Anahtar kelime değişimleri
        for tr_kelime, ceviri_sozluk in self.lokalizasyon_matrisi.items():
            if tr_kelime in kaynak_metin.lower():
                # Dil koduna göre en uygun çeviriyi bul
                ceviri = ceviri_sozluk.get(dil_kodu)
                if not ceviri:
                    # Tam eşleşme yoksa, genel dil kodunu dene
                    genel_dil = dil_kodu.split("-")[0]
                    ceviri = ceviri_sozluk.get(genel_dil)
                if ceviri:
                    lokalize_edilmis = lokalize_edilmis.replace(tr_kelime, ceviri)
        
        return lokalize_edilmis

    def ceviri_hazirla(self, kaynak_metin, hedef_diller, icerik_turu="genel"):
        """
        Kaynak metni hedef dillere çevirir ve lokalize eder.
        """
        kaynak_metin = kaynak_metin.strip()
        ceviri_sonuclari = []
        
        for dil_kodu in hedef_diller:
            if dil_kodu not in self.hedef_pazarlar:
                continue
                
            pazar_bilgisi = self.hedef_pazarlar[dil_kodu]
            
            # Akıllı lokalizasyon
            lokalize_edilmis_metin = self.akilli_lokalizasyon(kaynak_metin, dil_kodu, icerik_turu)
            
            # Pazar uyumluluk skoru
            uyumluluk_skoru = self.pazar_uyumluluk_skoru_hesapla(dil_kodu)
            
            ceviri_sonuclari.append({
                "Kaynak_Metin": kaynak_metin,
                "Hedef_Dil_Kodu": dil_kodu,
                "Hedef_Ulke": pazar_bilgisi["ulke"],
                "Hedef_Dil": pazar_bilgisi["dil"],
                "Para_Birimi": pazar_bilgisi["para_birimi"],
                "Bolge": pazar_bilgisi["bolge"],
                "Kulturel_Skor": pazar_bilgisi["kulturel_skor"],
                "Pazar_Uyumluluk_Skoru": uyumluluk_skoru,
                "Icerik_Turu": icerik_turu,
                "Lokalize_Edilmis_Metin": lokalize_edilmis_metin,
                "Ceviri_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return ceviri_sonuclari

    def tum_ulkeler_raporu_olustur(self):
        """
        Tüm 130+ ülke için detaylı rapor oluşturur.
        """
        tum_rapor = []
        
        for dil_kodu, pazar in self.hedef_pazarlar.items():
            uyumluluk_skoru = self.pazar_uyumluluk_skoru_hesapla(dil_kodu)
            
            tum_rapor.append({
                "Dil_Kodu": dil_kodu,
                "Ulke": pazar["ulke"],
                "Dil": pazar["dil"],
                "Para_Birimi": pazar["para_birimi"],
                "Bolge": pazar["bolge"],
                "Kulturel_Skor": pazar["kulturel_skor"],
                "Pazar_Uyumluluk_Skoru": uyumluluk_skoru,
                "Ceviri_Durumu": "Hazır" if uyumluluk_skoru >= 80 else "Kısıtlı" if uyumluluk_skoru >= 60 else "Düşük",
                "Oncelik_Seviyesi": "Yüksek" if uyumluluk_skoru >= 90 else "Orta" if uyumluluk_skoru >= 75 else "Düşük"
            })
        
        return tum_rapor

    def raporu_arsivle(self, yeni_ceviriler):
        """Çeviri sonuçlarını arşive işler."""
        mevcut_veriler = []
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    mevcut_veriler = json.load(f)
                except json.JSONDecodeError:
                    mevcut_veriler = []
                    
        mevcut_veriler.extend(yeni_ceviriler)
        
        # JSON Kayıt
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)
            
        # Excel Raporu Çıktısı
        df = pd.DataFrame(mevcut_veriler)
        df.to_excel(self.excel_file, index=False)
        
        return True
