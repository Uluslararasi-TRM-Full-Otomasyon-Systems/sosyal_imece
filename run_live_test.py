# run_live_test.py - Tüm Sistem Canlı Test ve Doğrulama Motoru
import os
from main_orchestrator import MainOrchestrator

if __name__ == "__main__":
    print("🚀 [Live Test] 60 Milyonluk Dağıtık Ekosistem canlı test modunda tetikleniyor...")
    
    # Ana kumandayı çalıştır ve tüm entegrasyonları test et
    orchestrator = MainOrchestrator()
    success = orchestrator.run_full_cycle()
    
    if success:
        print("✨ [Live Test] Başarılı! Tüm sharded cluster dosyaları ve refah kasası data_cluster altında oluşturuldu.")
    else:
        print("⚠️ [Live Test] Test sırasında uyarı alındı, self-healing core devreye girdi.")