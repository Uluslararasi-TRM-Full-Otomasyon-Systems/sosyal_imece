def tedarikci_analiz_et(firma_adi, yetkili_adi):
    """Tedarikçi görüşmesi için veriye dayalı hazırlık taslağı oluşturur."""
    if not isinstance(firma_adi, str) or not firma_adi.strip():
        raise ValueError("firma_adi boş olmayan bir metin olmalıdır")
    if not isinstance(yetkili_adi, str) or not yetkili_adi.strip():
        raise ValueError("yetkili_adi boş olmayan bir metin olmalıdır")

    firma = firma_adi.strip()
    yetkili = yetkili_adi.strip()
    rapor = {
        "firma_adi": firma,
        "yetkili_adi": yetkili,
        "profil_tipi": "Doğrulanmış profil verisi yok",
        "tavsiye": (
            "Kişilik varsayımı yapmayın. Görüşmeye güncel komisyon marjı, "
            "lojistik süreleri, satış hacmi tahmini ve yazılı hedeflerle hazırlanın; "
            "karşı tarafın önceliklerini doğrudan sorun."
        ),
        "ilk_cumle_taslagi": (
            f"Merhaba {yetkili}, {firma} ile olası iş birliğini değerlendirmek "
            "ve hedefleri, lojistik koşulları ile komisyon yapısını birlikte "
            "netleştirmek istiyoruz."
        ),
    }

    print("\n--- TEDARİKÇİ GÖRÜŞME HAZIRLIĞI ---")
    print(f"Firma: {firma}")
    print(f"Yetkili: {yetkili}")
    print(f"Profil: {rapor['profil_tipi']}")
    print(f"Hazırlık: {rapor['tavsiye']}")
    print(f"Açılış: {rapor['ilk_cumle_taslagi']}")
    return rapor


if __name__ == "__main__":
    tedarikci_analiz_et("Global Tedarik A.Ş.", "Ahmet Bey")