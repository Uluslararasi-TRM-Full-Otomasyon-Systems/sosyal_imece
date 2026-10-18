from muzakere_ajani import tedarikci_analiz_et


class SesliMuzakereAjani:
    def __init__(self, firma_adi, yetkili_adi, hedef_iskonto=None):
        self.firma_adi = self._required_text(firma_adi, "firma_adi")
        self.yetkili_adi = self._required_text(yetkili_adi, "yetkili_adi")
        if hedef_iskonto is not None and not 0 <= float(hedef_iskonto) <= 100:
            raise ValueError("hedef_iskonto 0 ile 100 arasında olmalıdır")
        self.hedef_iskonto = None if hedef_iskonto is None else float(hedef_iskonto)

    @staticmethod
    def _required_text(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} boş olmayan bir metin olmalıdır")
        return value.strip()

    def muzakere_taslagi_olustur(self):
        """Görüşme metni üretir; ses veya kişilik analizi yapmaz."""
        base_report = tedarikci_analiz_et(self.firma_adi, self.yetkili_adi)
        report = {
            "firma": self.firma_adi,
            "yetkili": self.yetkili_adi,
            "ses_tonu_kriteri": "Nötr, anlaşılır ve profesyonel; kişiye göre çıkarım yapılmaz.",
            "hedef_iskonto_yuzdesi": self.hedef_iskonto,
            "ses_sentez_durumu": (
                "Ses klonlama kapalı; yalnızca görüşme metni hazırlanmıştır."
            ),
            "ornek_sesli_cumle": base_report["ilk_cumle_taslagi"],
            "gorusme_hazirligi": base_report["tavsiye"],
        }
        if self.hedef_iskonto is not None:
            report["hedef_iskonto_notu"] = (
                f"Kullanıcının belirlediği hedef: %{self.hedef_iskonto:.1f}. "
                "Bu oran piyasa verisi veya garanti edilmiş tasarruf değildir."
            )
        return report


if __name__ == "__main__":
    agent = SesliMuzakereAjani("Global Tedarik A.Ş.", "Mehmet Bey")
    print(agent.muzakere_taslagi_olustur())