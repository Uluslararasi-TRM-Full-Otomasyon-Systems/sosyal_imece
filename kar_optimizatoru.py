import math


class KarOptimizatoru:
    def __init__(self, magaza_adi="Trend Ürünler Market"):
        if not isinstance(magaza_adi, str) or not magaza_adi.strip():
            raise ValueError("magaza_adi boş olmayan bir metin olmalıdır")
        self.magaza_adi = magaza_adi.strip()

    @staticmethod
    def _number(value, field, minimum=0):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} sayısal olmalıdır")
        if not math.isfinite(value) or value < minimum:
            raise ValueError(f"{field} {minimum} veya daha büyük, sonlu bir sayı olmalıdır")
        return float(value)

    def karlilik_ve_donusum_analizi(
        self,
        urun,
        satis_fiyati,
        birim_maliyet,
        ziyaret_sayisi,
        siparis_sayisi,
        reklam_gideri=0,
        hedef_marj=40,
    ):
        if not isinstance(urun, str) or not urun.strip():
            raise ValueError("urun boş olmayan bir metin olmalıdır")

        price = self._number(satis_fiyati, "satis_fiyati")
        if price <= 0:
            raise ValueError("satis_fiyati sıfırdan büyük olmalıdır")
        cost = self._number(birim_maliyet, "birim_maliyet")
        visits = self._number(ziyaret_sayisi, "ziyaret_sayisi")
        orders = self._number(siparis_sayisi, "siparis_sayisi")
        ad_spend = self._number(reklam_gideri, "reklam_gideri")
        target = self._number(hedef_marj, "hedef_marj")
        if target >= 100:
            raise ValueError("hedef_marj %100'den küçük olmalıdır")
        if orders > visits:
            raise ValueError("siparis_sayisi ziyaret_sayisi değerini aşamaz")

        revenue = price * orders
        gross_profit = (price - cost) * orders
        net_profit = gross_profit - ad_spend
        conversion_rate = (orders / visits * 100) if visits else None
        net_margin = (net_profit / revenue * 100) if revenue else None

        target_price = None
        if orders:
            ad_cost_per_order = ad_spend / orders
            target_price = (cost + ad_cost_per_order) / (1 - target / 100)

        recommendation = (
            "Sipariş verisi olmadığından fiyat önerisi üretilemedi."
            if target_price is None
            else (
                "Mevcut fiyat hedef net marjın altında. Fiyat değişikliğinden önce talep etkisini test edin."
                if net_margin is not None and net_margin < target
                else "Girilen verilerde net marj hedefi karşılanıyor."
            )
        )

        return {
            "magaza": self.magaza_adi,
            "urun": urun.strip(),
            "veri_kaynagi": "kullanıcı girdisi",
            "satis_fiyati": price,
            "birim_maliyet": cost,
            "ziyaret_sayisi": int(visits),
            "siparis_sayisi": int(orders),
            "reklam_gideri": ad_spend,
            "ciro": revenue,
            "brut_kar": gross_profit,
            "net_kar": net_profit,
            "donusum_orani": conversion_rate,
            "reklam_dahil_net_marj": net_margin,
            "hedef_marj": target,
            "hedef_fiyat_onerisi": target_price,
            "fiyat_onerisi_varsayimi": (
                "Hesap, satış adedinin değişmediğini varsayar; fiyat otomatik olarak değiştirilmez."
            ),
            "onerilen_aksiyon": recommendation,
        }


if __name__ == "__main__":
    result = KarOptimizatoru().karlilik_ve_donusum_analizi(
        urun="Örnek ürün",
        satis_fiyati=100,
        birim_maliyet=40,
        ziyaret_sayisi=100,
        siparis_sayisi=10,
        reklam_gideri=100,
        hedef_marj=50,
    )
    print(result)