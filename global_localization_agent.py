# global_localization_agent.py - Çoklu Dil ve Küresel Yerelleştirme Ajanı
class GlobalLocalizationAgent:
    def __init__(self):
        self.supported_languages = {'TR': 'Türkçe', 'EN': 'English', 'DE': 'Deutsch'}

    def localize_copy(self, text, target_lang='EN'):
        print(f'>>> [Localization] Metin \'{target_lang}\' diline uyarlanıyor...')
        if target_lang == 'EN':
            return f'[Localized EN]: Ultimate deal! Check this out: {text}'
        elif target_lang == 'DE':
            return f'[Localized DE]: Top Angebot! Schau mal hier: {text}'
        return text
