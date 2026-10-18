from html import escape


class HolografikGorsellestirici:
    def __init__(self, urun_konsepti="Akıllı Solar Espressör"):
        if not isinstance(urun_konsepti, str) or not urun_konsepti.strip():
            raise ValueError("urun_konsepti boş olmayan bir metin olmalıdır")
        self.urun_konsepti = urun_konsepti.strip()

    def _build_preview_svg(self):
        safe_concept = escape(self.urun_konsepti, quote=False)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" role="img" aria-label="{escape(self.urun_konsepti, quote=True)} konsept önizlemesi">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#101b2c"/><stop offset="1" stop-color="#25344a"/></linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#65f4e2" stop-opacity=".62"/><stop offset=".5" stop-color="#42b8d3" stop-opacity=".18"/><stop offset="1" stop-color="#f6c66b" stop-opacity=".42"/></linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="900" height="560" rx="22" fill="url(#bg)"/>
<path d="M45 430H855M80 455H820" stroke="#7de9df" stroke-opacity=".18"/>
<text x="58" y="68" fill="#8cefe4" font-family="sans-serif" font-size="15" letter-spacing="2">HOLOGRAPHIC CONCEPT / SVG PREVIEW</text>
<text x="58" y="112" fill="#f5f7fa" font-family="sans-serif" font-size="27" font-weight="600">{safe_concept}</text>
<g filter="url(#glow)" stroke="#81f0e2" stroke-width="2">
  <ellipse cx="450" cy="420" rx="185" ry="24" fill="none" stroke-opacity=".65"/>
  <path d="M330 180L450 130L570 180V360L450 405L330 360Z" fill="url(#glass)"/>
  <path d="M330 180L450 225L570 180M450 225V405" fill="none" stroke-opacity=".85"/>
  <path d="M366 191L450 160L534 191V340L450 372L366 340Z" fill="none" stroke="#b7fff5" stroke-opacity=".6"/>
  <circle cx="450" cy="286" r="34" fill="#102434" fill-opacity=".65" stroke="#f3ca79"/>
  <path d="M450 267V305M432 286H468" stroke="#f3ca79" stroke-width="3"/>
</g>
<text x="58" y="505" fill="#c1d2dd" font-family="sans-serif" font-size="14">Konsept çizimidir; ürün ölçüsü, malzeme ve özellik doğrulaması içermez.</text>
</svg>'''

    def gorsel_ve_mockup_uret(self):
        return {
            "urun_konsepti": self.urun_konsepti,
            "medya_tipi": "Holografik ürün konsept önizlemesi",
            "durum": "SVG konsept görseli hazır; fotogerçekçi render ve 360° video üretilmedi.",
            "dosya_formati": "SVG (1 konsept önizlemesi)",
            "gercek_render_uretildi": False,
            "preview_svg": self._build_preview_svg(),
            "render_prompt_taslagi": (
                f"{self.urun_konsepti} için ürün özellikleri doğrulanmış, nötr stüdyo ışıklı "
                "e-ticaret konsept görseli oluştur. Görselde bulunmayan işlev veya sertifika iddiası ekleme."
            ),
        }


if __name__ == "__main__":
    visualizer = HolografikGorsellestirici()
    print({key: value for key, value in visualizer.gorsel_ve_mockup_uret().items() if key != "preview_svg"})