# -*- coding: utf-8 -*-
"""Esnafa giden WhatsApp tanıtım mesajının TEK kaynağı (metin kilidi).

Bu modül dışındaki hiçbir yer serbest metinle tanıtım göndermemeli;
api_server_2.py ve panel buradaki `esnaf_tanitim_metni()` çıktısını kullanır.
"""

import re

SABLON = (
    "Sayın {yetkili} Hanım veya bey\n"
    "{isletme} dükkanınızı Kuşadası'ndaki nokta hedef kitleye doğrudan "
    "ulaştırmak için TRM Ekosistemi olarak yanınızdayız.\n"
    "📍 Adresiniz: {adres}\n"
    "🎯 Nokta Atışı Tanıtım: İşletmenizin kalitesini ve hizmetlerini sosyal medya "
    "kanallarımızda doğrudan hedef kitlenize tanıtıyoruz.\n"
    "🔒 TRM Nirvana Güvenlik & Doğrulama Sistemi: Kasaya gelen müşteriden 4 haneli "
    "SMS/Anlık Onay Kodu istenir (Örn: TRM-3126). Kod esnaf paneline girildiğinde "
    "Ad-Soyad, T.C. ve GSM doğrulaması anlık yapılır. Suistimal ve kaçaklara karşı "
    "%100 güvenlidir.\n"
    "🎁 İlk 5 Müşteri Yönlendirmesi Sıfır Komisyon! Sistemi canlı görmeniz için ilk "
    "5 yönlendirmede 1 TL bile talep etmiyoruz.\n"
    "Uygun olduğunuzda dükkanınıza bir çayınızı içmeye gelelim mi?"
)

ZORUNLU_ALANLAR = ("isletme", "adres")
SESSIZ_YETKILI = "Yetkili"


class SablonHatasi(ValueError):
    def __init__(self, eksikler):
        super().__init__("Tanıtım şablonu alanları eksik: " + ", ".join(eksikler))
        self.eksikler = list(eksikler)


def _alanlastir(deger, azami_uzunluk):
    if deger is None:
        return ""
    return re.sub(r"\s+", " ", str(deger)).strip()[:azami_uzunluk].strip()


def esnaf_tanitim_metni(isletme, adres, yetkili=None):
    """Kilitli metni üretir. İşletme adı veya adres boşsa SablonHatasi fırlatır."""
    alanlar = {
        "isletme": _alanlastir(isletme, 80),
        "adres": _alanlastir(adres, 160),
        "yetkili": _alanlastir(yetkili, 60) or SESSIZ_YETKILI,
    }
    eksik = [ad for ad in ZORUNLU_ALANLAR if not alanlar[ad]]
    if eksik:
        raise SablonHatasi(eksik)

    metin = SABLON.format(**alanlar)
    if re.search(r"\[[^\]\n]{0,40}\]", metin):
        raise SablonHatasi(["yer tutucu denetimi"])
    return metin
