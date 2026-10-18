#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supply & Quality Guardian Agent (Tedarik ve Kalite Güvence Ajanı)

Bu ajan:
- Ürün stoklarını 7/24 izler
- Diplomatik uyarı sistemi ile üreticileri bilgilendirir
- Failover switch ile kritik durumlarda alternatif ürünlere trafik yönlendirir
- Gelir akışını korur (İR-SA AŞ. komisyon ve refah payı)
- Fiyatsızlaştırma ve Master Geo Intelligence entegrasyonu
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from trm_agents.base_agent_template import BaseAgent
from trm_agents.system_protocols import CEO_TITLE, format_ceo_message, LogFormatter


class SupplyQualityGuardianAgent(BaseAgent):
    """
    Tedarik ve Kalite Güvence Ajanı
    
    Bu ajan:
    - Ürün stok seviyelerini izler
    - Diplomatik uyarı mesajları gönderir
    - Failover switch ile trafik yönlendirir
    - Gelir akışını korur
    """
    
    def __init__(self, agent_id: Optional[int] = None):
        super().__init__(
            agent_name="Supply & Quality Guardian Agent",
            agent_id=agent_id if agent_id else 172
        )
        
        # Stok izleme verileri
        self.product_inventory = {}
        self.supplier_alerts = {}
        self.traffic_shifts = []
        
        # Diplomatik uyarı şablonları
        self.diplomatic_templates = {
            "first_alert": {
                "subject": "Değerli İş Ortaklığımız - Stok Bilgilendirmesi",
                "message": """Değerli iş ortağımız,

Otonom talep motorumuz ürününüze yoğun ilgi saptadı. Mevcut stok seviyeniz kritik eşiğe yaklaşmaktadır.

Müşteri memnuniyeti ve iş birliğimizin sürdürülebilirliği adına, stok yenileme işleminizi en kısa sürede gerçekleştirmenizi rica ederiz.

İş birliğiniz için teşekkürler,
İR-SA AŞ. Otonom Sistem"""
            },
            "second_alert": {
                "subject": "Acil Stok Yenileme Gerekiyor - İş Birliği Çağrısı",
                "message": """Değerli iş ortağımız,

Ürününüzün stok seviyesi kritik düzeydedir. Müşteri taleplerini karşılamakta zorlanıyoruz.

Lütfen stokunuzu 24 saat içinde yenileyin. Aksi takdirde, sistemimiz müşteri memnuniyetini korumak adına alternatif çözümler devreye alabilir.

İş birliğinizin devamını dileriz,
İR-SA AŞ. Otonom Sistem"""
            },
            "final_alert": {
                "subject": "Son Uyarı - Stok Tükenme Riski",
                "message": """Değerli iş ortağımız,

Ürününüzün stok seviyesi tükenme noktasındadır. Bu durum müşteri memnuniyetini ve gelir akışını tehdit etmektedir.

Son bir kez stok yenileme işleminizi gerçekleştirmenizi rica ederiz. Aksi takdirde, sistemimiz otomatik olarak alternatif ürünlere trafik yönlendirecektir.

İş birliğiniz için teşekkürler,
İR-SA AŞ. Otonom Sistem"""
            }
        }
        
        # Failover protokolü
        self.failover_protocol = {
            "enabled": True,
            "traffic_shift_threshold": 0.05,  # %5 stok altında trafik shift
            "max_shift_attempts": 3,
            "revenue_protection": True
        }
        
        # Gelir koruma ayarları
        self.revenue_protection = {
            "commission_split": {"personal": 0.70, "imece_pool": 0.30},
            "volunteer_count": 200,
            "imece_share_active": True
        }
        
        self.log(f"🛡️ Tedarik ve Kalite Güvence Ajanı başlatıldı. {CEO_TITLE}", "INFO")
    
    def monitor_product_inventory(self, product_id: str, current_stock: int, 
                                   critical_threshold: int = 10) -> Dict[str, Any]:
        """
        Ürün stokunu izler ve gerekirse uyarı gönderir
        
        Args:
            product_id: Ürün ID'si
            current_stock: Mevcut stok
            critical_threshold: Kritik eşik (varsayılan: 10)
            
        Returns:
            İzleme sonucu
        """
        self.log(f"📊 {product_id} stok izleniyor: {current_stock} (Kritik: {critical_threshold})", "INFO")
        
        # Stok verisini güncelle
        self.product_inventory[product_id] = {
            "current_stock": current_stock,
            "critical_threshold": critical_threshold,
            "last_updated": datetime.now().isoformat(),
            "status": self._determine_stock_status(current_stock, critical_threshold)
        }
        
        # Stok durumu kontrol et
        status = self.product_inventory[product_id]["status"]
        
        if status == "critical":
            return self._handle_critical_stock(product_id, current_stock)
        elif status == "warning":
            return self._handle_warning_stock(product_id, current_stock)
        else:
            return {
                "product_id": product_id,
                "status": "normal",
                "message": "Stok seviyesi normal",
                "action_required": False
            }
    
    def _determine_stock_status(self, current_stock: int, critical_threshold: int) -> str:
        """Stok durumunu belirler"""
        if current_stock <= critical_threshold:
            return "critical"
        elif current_stock <= critical_threshold * 2:
            return "warning"
        else:
            return "normal"
    
    def _handle_critical_stock(self, product_id: str, current_stock: int) -> Dict[str, Any]:
        """Kritik stok durumunu yönetir"""
        self.log(f"⚠️ {product_id} kritik stok seviyesinde: {current_stock}", "WARNING")
        
        # Önceki uyarıları kontrol et
        if product_id not in self.supplier_alerts:
            self.supplier_alerts[product_id] = []
        
        alert_count = len(self.supplier_alerts[product_id])
        
        # Diplomatik uyarı gönder
        if alert_count == 0:
            alert = self._send_diplomatic_alert(product_id, "first_alert")
            self.supplier_alerts[product_id].append(alert)
            return {
                "product_id": product_id,
                "status": "critical",
                "alert_level": "first",
                "message": "İlk diplomatik uyarı gönderildi",
                "action_required": True,
                "alert": alert
            }
        elif alert_count == 1:
            alert = self._send_diplomatic_alert(product_id, "second_alert")
            self.supplier_alerts[product_id].append(alert)
            return {
                "product_id": product_id,
                "status": "critical",
                "alert_level": "second",
                "message": "İkinci diplomatik uyarı gönderildi",
                "action_required": True,
                "alert": alert
            }
        else:
            # Son uyarı ve failover hazırlığı
            alert = self._send_diplomatic_alert(product_id, "final_alert")
            self.supplier_alerts[product_id].append(alert)
            
            # Failover switch'i hazırla
            failover_ready = self._prepare_failover(product_id)
            
            return {
                "product_id": product_id,
                "status": "critical",
                "alert_level": "final",
                "message": "Son uyarı gönderildi, failover switch hazır",
                "action_required": True,
                "alert": alert,
                "failover_ready": failover_ready
            }
    
    def _handle_warning_stock(self, product_id: str, current_stock: int) -> Dict[str, Any]:
        """Uyarı stok durumunu yönetir"""
        self.log(f"📋 {product_id} uyarı stok seviyesinde: {current_stock}", "INFO")
        
        return {
            "product_id": product_id,
            "status": "warning",
            "message": "Stok seviyesi uyarı eşiğinde",
            "action_required": False,
            "recommendation": "Stok takibi devam ediyor"
        }
    
    def _send_diplomatic_alert(self, product_id: str, alert_type: str) -> Dict[str, Any]:
        """
        Diplomatik uyarı mesajı gönderir
        
        Args:
            product_id: Ürün ID'si
            alert_type: Uyarı tipi (first_alert, second_alert, final_alert)
            
        Returns:
            Uyarı kaydı
        """
        template = self.diplomatic_templates.get(alert_type, self.diplomatic_templates["first_alert"])
        
        alert = {
            "product_id": product_id,
            "alert_type": alert_type,
            "subject": template["subject"],
            "message": template["message"],
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        self.log(f"📧 Diplomatik uyarı gönderildi: {product_id} - {alert_type}", "INFO")
        
        return alert
    
    def _prepare_failover(self, product_id: str) -> Dict[str, Any]:
        """
        Failover switch'i hazırlar
        
        Args:
            product_id: Ürün ID'si
            
        Returns:
            Failover hazırlık durumu
        """
        failover_plan = {
            "product_id": product_id,
            "prepared_at": datetime.now().isoformat(),
            "status": "ready",
            "alternative_products": self._find_alternative_products(product_id),
            "traffic_shift_ready": True,
            "revenue_protection_active": True
        }
        
        self.log(f"🔄 Failover switch hazırlandı: {product_id}", "INFO")
        
        return failover_plan
    
    def _find_alternative_products(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Alternatif ürünleri bulur (Master Geo Intelligence entegrasyonu)
        
        Args:
            product_id: Ürün ID'si
            
        Returns:
            Alternatif ürün listesi
        """
        # Mock data - gerçek sistemde Master Geo Intelligence'dan çekilir
        alternatives = [
            {
                "product_id": f"ALT_{product_id}_1",
                "product_name": "Alternatif Ürün 1",
                "category": "electronics",
                "supplier": "Alternatif Tedarikçi A",
                "stock_level": 100,
                "quality_score": 0.85,
                "price_compatibility": 0.90
            },
            {
                "product_id": f"ALT_{product_id}_2",
                "product_name": "Alternatif Ürün 2",
                "category": "electronics",
                "supplier": "Alternatif Tedarikçi B",
                "stock_level": 150,
                "quality_score": 0.88,
                "price_compatibility": 0.95
            }
        ]
        
        self.log(f"🔍 {len(alternatives)} alternatif ürün bulundu: {product_id}", "INFO")
        
        return alternatives
    
    def execute_failover_switch(self, product_id: str, 
                                 target_product_id: str) -> Dict[str, Any]:
        """
        Failover switch'i uygular - Trafik yönlendirme
        
        Args:
            product_id: Orijinal ürün ID'si
            target_product_id: Hedef ürün ID'si
            
        Returns:
            Failover sonucu
        """
        self.log(f"🚨 Failover switch uygulanıyor: {product_id} -> {target_product_id}", "WARNING")
        
        # Trafik yönlendirme
        traffic_shift = {
            "original_product_id": product_id,
            "target_product_id": target_product_id,
            "shifted_at": datetime.now().isoformat(),
            "shift_percentage": 100,
            "reason": "Stock depletion - Supplier failed to respond",
            "revenue_protection": {
                "commission_split": self.revenue_protection["commission_split"],
                "imece_share_active": self.revenue_protection["imece_share_active"],
                "volunteer_count": self.revenue_protection["volunteer_count"]
            },
            "status": "completed"
        }
        
        self.traffic_shifts.append(traffic_shift)
        
        # Gelir koruma kontrolü
        revenue_status = self._verify_revenue_protection()
        
        self.log(f"✅ Failover switch tamamlandı. Gelir koruması: {revenue_status}", "SUCCESS")
        
        return {
            "traffic_shift": traffic_shift,
            "revenue_protection_status": revenue_status,
            "message": f"Trafik {target_product_id} ürününe başarıyla yönlendirildi"
        }
    
    def _verify_revenue_protection(self) -> Dict[str, Any]:
        """
        Gelir koruma durumunu doğrular
        
        Returns:
            Gelir koruma durumu
        """
        protection_status = {
            "commission_split_active": True,
            "personal_commission": self.revenue_protection["commission_split"]["personal"],
            "imece_pool_commission": self.revenue_protection["commission_split"]["imece_pool"],
            "volunteer_imece_share_active": self.revenue_protection["imece_share_active"],
            "volunteer_count": self.revenue_protection["volunteer_count"],
            "revenue_flow_status": "protected",
            "last_verified": datetime.now().isoformat()
        }
        
        return protection_status
    
    def generate_priceless_content_for_alternative(self, product_id: str) -> Dict[str, Any]:
        """
        Alternatif ürün için fiyatsızlaştırma içeriği üretir
        
        Args:
            product_id: Alternatif ürün ID'si
            
        Returns:
            Fiyatsızlaştırma içeriği
        """
        # Fiyatsızlaştırma ajanı entegrasyonu (mock)
        content = {
            "product_id": product_id,
            "content_type": "priceless",
            "hook": "Kalite ve değer arayanlar için mükemmel seçim",
            "value_proposition": "Fiyat odaklı değil, değer odaklı yaklaşım",
            "platforms": ["tiktok", "reels", "shorts"],
            "generated_at": datetime.now().isoformat(),
            "status": "ready"
        }
        
        self.log(f"🎭 Fiyatsızlaştırma içeriği üretildi: {product_id}", "INFO")
        
        return content
    
    def get_supplier_performance_report(self, supplier_id: str) -> Dict[str, Any]:
        """
        Tedarikçi performans raporu oluşturur
        
        Args:
            supplier_id: Tedarikçi ID'si
            
        Returns:
            Performans raporu
        """
        # Mock data
        report = {
            "supplier_id": supplier_id,
            "report_period": "last_30_days",
            "total_alerts": 3,
            "stock_outs": 1,
            "response_time_avg": "48 hours",
            "reliability_score": 0.75,
            "recommendation": "Monitor closely",
            "generated_at": datetime.now().isoformat()
        }
        
        self.log(f"📊 Tedarikçi performans raporu: {supplier_id}", "INFO")
        
        return report
    
    def get_guardian_dashboard(self) -> Dict[str, Any]:
        """
        Guardian dashboard verilerini döndürür
        
        Returns:
            Dashboard verileri
        """
        dashboard = {
            "monitored_products": len(self.product_inventory),
            "critical_stock_products": sum(1 for p in self.product_inventory.values() if p["status"] == "critical"),
            "warning_stock_products": sum(1 for p in self.product_inventory.values() if p["status"] == "warning"),
            "total_alerts_sent": sum(len(alerts) for alerts in self.supplier_alerts.values()),
            "traffic_shifts_executed": len(self.traffic_shifts),
            "revenue_protection_status": "active",
            "last_updated": datetime.now().isoformat()
        }
        
        self.log(f"📋 Guardian dashboard güncellendi", "INFO")
        
        return dashboard
    
    def run(self, operation: str = "monitor", **kwargs) -> Dict[str, Any]:
        """
        Ajan ana çalışma fonksiyonu
        
        Args:
            operation: İşlem tipi
            **kwargs: İşlem parametreleri
            
        Returns:
            İşlem sonucu
        """
        self.log(f"🚀 Tedarik ve Kalite Güvence Ajanı çalışıyor: {operation}", "INFO")
        
        if operation == "monitor":
            return self.monitor_product_inventory(
                product_id=kwargs.get("product_id", "default_product"),
                current_stock=kwargs.get("current_stock", 50),
                critical_threshold=kwargs.get("critical_threshold", 10)
            )
        elif operation == "failover":
            return self.execute_failover_switch(
                product_id=kwargs.get("product_id"),
                target_product_id=kwargs.get("target_product_id")
            )
        elif operation == "priceless_content":
            return self.generate_priceless_content_for_alternative(
                product_id=kwargs.get("product_id")
            )
        elif operation == "supplier_report":
            return self.get_supplier_performance_report(
                supplier_id=kwargs.get("supplier_id")
            )
        elif operation == "dashboard":
            return self.get_guardian_dashboard()
        else:
            return {
                "error": f"Bilinmeyen işlem: {operation}",
                "available_operations": ["monitor", "failover", "priceless_content", "supplier_report", "dashboard"]
            }
    
    def stop(self) -> Dict[str, Any]:
        """Ajanı durdurur"""
        self.log("🛑 Tedarik ve Kalite Güvence Ajanı durduruluyor", "INFO")
        self.is_running = False
        self.status = "stopped"
        return {"status": "stopped", "agent_id": self.agent_id}
    
    def restart(self) -> Dict[str, Any]:
        """Ajanı yeniden başlatır"""
        self.log("🔄 Tedarik ve Kalite Güvence Ajanı yeniden başlatılıyor", "INFO")
        self.status = "ready"
        self.is_running = True
        return {"status": "restarted", "agent_id": self.agent_id}


# =============================================================================
# TEST BLOĞU
# =============================================================================
if __name__ == "__main__":
    print("🛡️ Supply & Quality Guardian Agent Test")
    print("=" * 50)
    
    # Ajanı başlat
    agent = SupplyQualityGuardianAgent(agent_id=172)
    
    # Test 1: Normal stok
    print("\n📊 Test 1: Normal Stok")
    result1 = agent.run(
        operation="monitor",
        product_id="PROD_001",
        current_stock=100,
        critical_threshold=10
    )
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    
    # Test 2: Kritik stok - ilk uyarı
    print("\n⚠️ Test 2: Kritik Stok - İlk Uyarı")
    result2 = agent.run(
        operation="monitor",
        product_id="PROD_002",
        current_stock=5,
        critical_threshold=10
    )
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    
    # Test 3: Dashboard
    print("\n📋 Test 3: Dashboard")
    result3 = agent.run(operation="dashboard")
    print(json.dumps(result3, indent=2, ensure_ascii=False))
    
    # Test 4: Failover
    print("\n🚨 Test 4: Failover Switch")
    result4 = agent.run(
        operation="failover",
        product_id="PROD_002",
        target_product_id="ALT_PROD_002_1"
    )
    print(json.dumps(result4, indent=2, ensure_ascii=False))
    
    print("\n✅ Tüm testler tamamlandı")
