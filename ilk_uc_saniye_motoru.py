import random


_HOOK_TEMPLATES = (
    "{urun} hakkında karar vermeden önce şu özelliğine göz atın.",
    "{hedef} için {urun}: günlük kullanımda neleri kolaylaştırabilir?",
    "Kısa ürün incelemesi: {urun} kimler için uygun olabilir?",
)


def kanca_ekle(urun_adi, hedef_kitle="Global"):
    """Ürün ve hedef kitle için kısa, doğrulanabilir bir açılış metni üretir."""
    if not isinstance(urun_adi, str) or not urun_adi.strip():
        raise ValueError("urun_adi boş olmayan bir metin olmalıdır")
    if not isinstance(hedef_kitle, str) or not hedef_kitle.strip():
        raise ValueError("hedef_kitle boş olmayan bir metin olmalıdır")

    hook = random.choice(_HOOK_TEMPLATES).format(
        urun=urun_adi.strip(),
        hedef=hedef_kitle.strip(),
    )
    print(f"[İlk 3 Saniye] Hedef kitle: {hedef_kitle.strip()}")
    print(f"[Video kancası] {hook}")
    return hook


if __name__ == "__main__":
    kanca_ekle("Trend Akıllı Ürün")