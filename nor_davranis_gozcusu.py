from copy import deepcopy
from random import Random


_DEMO_ENGAGEMENT_SIGNALS = (
    {
        "icerik_turu": "Kısa ürün demosu",
        "tamamlama_orani": 71.2,
        "kaydetme_orani": 8.4,
        "paylasim_orani": 3.1,
        "tavsiye_edilen_aksiyon": (
            "Ürünün kullanımını, doğrulanmış özelliklerini ve fiyat/koşul bilgisini "
            "kısa, anlaşılır bir demoda gösterin."
        ),
    },
    {
        "icerik_turu": "Özellik ve fiyat karşılaştırması",
        "tamamlama_orani": 64.7,
        "kaydetme_orani": 10.2,
        "paylasim_orani": 4.6,
        "tavsiye_edilen_aksiyon": (
            "Ürün özelliklerini ve toplam maliyeti açıkça karşılaştırın; "
            "iddiaları doğrulanmış kaynaklarla destekleyin."
        ),
    },
)


class NorDavranisGozcusu:
    def __init__(self, platform="TikTok / Reels", sinyaller=None, rng=None):
        if not isinstance(platform, str) or not platform.strip():
            raise ValueError("platform boş olmayan bir metin olmalıdır")
        self.platform = platform.strip()
        self._sinyaller = tuple(
            sinyaller if sinyaller is not None else _DEMO_ENGAGEMENT_SIGNALS
        )
        self._rng = rng if rng is not None else Random()

    def kitle_ruh_hali_analiz_et(self):
        """Geriye uyumlu ad; yalnızca toplu içerik sinyali döndürür.

        Bireysel ruh hâli, kişilik veya psikografik profil çıkarımı yapmaz.
        Varsayılan sinyaller simülasyondur, canlı platform verisi değildir.
        """
        if not self._sinyaller:
            raise ValueError("Analiz için en az bir toplu sinyal kaydı gereklidir")

        signal = deepcopy(self._rng.choice(self._sinyaller))
        for field in ("tamamlama_orani", "kaydetme_orani", "paylasim_orani"):
            value = signal.get(field)
            if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                raise ValueError(f"{field} 0 ile 100 arasında sayısal bir oran olmalıdır")

        return {
            "platform": self.platform,
            "veri_kaynagi": "simülasyon" if self._sinyaller is _DEMO_ENGAGEMENT_SIGNALS else "toplu etkileşim verisi",
            "bireysel_profil_cikarimi": "Yapılmaz",
            "gozlemlenen_icerik_sinyali": signal,
            "tavsiye_edilen_aksiyon": signal.get(
                "tavsiye_edilen_aksiyon",
                "İçeriği açık ürün bilgileri ve doğrulanabilir özelliklerle hazırlayın.",
            ),
        }


if __name__ == "__main__":
    report = NorDavranisGozcusu(platform="Instagram Reels / TikTok").kitle_ruh_hali_analiz_et()
    print(report)