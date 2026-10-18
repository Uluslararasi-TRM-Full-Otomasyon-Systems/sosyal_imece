import math
from statistics import mean, median


class RakipFiyatCasusu:
    def __init__(self, hedef_kategori="Trend E-Ticaret Ürünleri"):
        if not isinstance(hedef_kategori, str) or not hedef_kategori.strip():
            raise ValueError("hedef_kategori boş olmayan bir metin olmalıdır")
        self.hedef_kategori = hedef_kategori.strip()

    @staticmethod
    def _valid_price(value, field):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} sayısal olmalıdır")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{field} sıfırdan büyük ve sonlu olmalıdır")
        return float(value)

    def pazar_fiyat_gözlemi_yap(self, urun, bizim_fiyatimiz, rakip_fiyatlari):
        """Kullanıcının sağladığı herkese açık fiyat gözlemlerini özetler.

        Web scraping, hesap erişimi veya otomatik fiyat değişikliği yapmaz.
        """
        if not isinstance(urun, str) or not urun.strip():
            raise ValueError("urun boş olmayan bir metin olmalıdır")
        our_price = self._valid_price(bizim_fiyatimiz, "bizim_fiyatimiz")
        if not isinstance(rakip_fiyatlari, (list, tuple)) or not rakip_fiyatlari:
            raise ValueError("En az bir rakip fiyat gözlemi girilmelidir")
        prices = [
            self._valid_price(price, f"rakip_fiyatlari[{index}]")
            for index, price in enumerate(rakip_fiyatlari)
        ]

        average_price = mean(prices)
        median_price = median(prices)
        difference_percent = (our_price - average_price) / average_price * 100
        if difference_percent > 0.5:
            recommendation = "Fiyat girilen gözlemlerin ortalamasının üzerinde; ürün farkı ve marjı inceleyin."
        elif difference_percent < -0.5:
            recommendation = "Fiyat girilen gözlemlerin ortalamasının altında; marjı koruyup özellikleri açıkça karşılaştırın."
        else:
            recommendation = "Fiyat girilen gözlemlerin ortalamasına yakın; fiyat değişikliği için yeterli kanıt yok."

        return {
            "urun": urun.strip(),
            "hedef_kategori": self.hedef_kategori,
            "veri_kaynagi": "kullanıcı tarafından girilen fiyat gözlemleri",
            "rakip_sayisi": len(prices),
            "rakip_fiyatlari": prices,
            "pazar_ortalama_fiyat": average_price,
            "pazar_medyan_fiyat": median_price,
            "bizim_fiyatimiz": our_price,
            "ortalama_fiyata_gore_fark_yuzde": difference_percent,
            "tavsiye_edilen_aksiyon": recommendation,
            "otomatik_fiyat_degisikligi": False,
            "not": "Fiyatlar canlı taranmadı; yalnızca girilen gözlemler karşılaştırıldı.",
        }


if __name__ == "__main__":
    report = RakipFiyatCasusu().pazar_fiyat_gözlemi_yap(
        "Taşınabilir vantilatör", 620, [650, 640, 675]
    )
    print(report)