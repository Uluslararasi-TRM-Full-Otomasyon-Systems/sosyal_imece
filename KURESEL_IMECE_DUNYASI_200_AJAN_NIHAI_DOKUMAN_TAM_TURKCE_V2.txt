==============================================================================
SOSYAL İMECE
200 YAPAY ZEKA AJANLI SİSTEM
NİHAİ BİLGİLENDİRME DOKÜMANI
==============================================================================

Doküman Türü : Profesyonel Nihai Sürüm
Dil          : Tam Türkçe karakterli
Kapsam       : 200 ajanlık mimari, görev alanları ve çalışma düzeni

KAPAK NOTU
Bu doküman, `SOSYAL İMECE` projesindeki 200 ajanlık operasyon
modelini daha profesyonel, daha okunaklı ve eksiksiz Türkçe karakterlerle
açıklamak için hazırlanmıştır.

ÖNEMLİ AÇIKLAMA
Bu sistemde "200 ajan" ifadesi iki katmandan oluşan operasyonel mimariyi
anlatır:
1. 165 ajanlık temel operasyon havuzu
2. Kod tabanında açık tanımlı 35 genişleme ajanı

Başka bir deyişle, projede 200 ayrı sınıf dosyası bulunması zorunlu değildir.
Mimari; görev havuzları, uzman ajanlar, çekirdek orkestrasyon ve genişleme
modülleri birlikte çalışacak şekilde tasarlanmıştır.

==============================================================================
1. YÖNETİCİ ÖZETİ
==============================================================================
Sistem genel olarak şu zincirle çalışır:
- Veri toplar
- Veriyi analiz eder
- İçeriğe dönüştürür
- Yayın kuyruğuna alır
- Planlı paylaşım yapar
- Performansı ve güvenliği izler
- Sağlık raporu ve durum özeti üretir

Bu zincirin merkezi beyni CoreNexus'tur. CoreNexus; ajanları bağlar, bağlamı
yönetir, Zero-Trust denetimi uygular ve ajan çıktılarının birbirine kontrollü
biçimde aktarılmasını sağlar.

==============================================================================
2. 165 AJANLIK TEMEL OPERASYON HAVUZU
==============================================================================
Aşağıdaki yapı, 001-165 arasındaki temel ajan kapasitesini temsil eder.
Bu bölümde birçok ajan aynı görevi paylaşan operasyon slotları şeklinde
tasarlanmıştır. Bu nedenle profesyonel sürümde tekrarlı metin yerine grup
mantığıyla açıklama yapılmıştır.

Ajan 001-020 | Veri Toplama Ajanları
Görev        : Dış kaynaklardan ürün, kampanya, bağlantı ve trend verisi toplar.
Nasıl çalışır: Web, kanal, liste ve ürün akışlarını izler; veriyi temizleyip
çekirdeğe aktarır.

Ajan 021-040 | Trend ve Analiz Ajanları
Görev        : Toplanan verileri puanlar, sıralar ve fırsatları belirler.
Nasıl çalışır: Başlık, ilgi düzeyi, fiyat, potansiyel dönüşüm ve trend skoru
üzerinden öncelik üretir.

Ajan 041-060 | İçerik Fabrikası Ajanları
Görev        : Trend raporlarını satış odaklı içeriklere dönüştürür.
Nasıl çalışır: Başlık, tanıtım metni, sosyal medya kopyası, çağrı metni ve
etiket üretir.

Ajan 061-080 | Kuyruk ve Yayın Ajanları
Görev        : İçeriği zaman planına göre yayın sırasına alır.
Nasıl çalışır: Gönderileri takvime işler, platform bazlı sıraya koyar ve yayın
sonucunu işler.

Ajan 081-100 | Maskeleme ve Güvenlik Ajanları
Görev        : Daha kontrollü ve düşük görünürlüklü çalışma sağlar.
Nasıl çalışır: Oturum izi, davranış modeli, cihaz sinyali ve risk seviyesini
yönetir.

Ajan 101-120 | Affiliate ve Ağ Ajanları
Görev        : Harici ortaklık ağlarını ve teklif akışlarını sisteme bağlar.
Nasıl çalışır: Katalog, teklif tazeliği, ağ sağlığı ve bağlantı verilerini
merkeze taşır.

Ajan 121-140 | Operasyon ve Sağlık Ajanları
Görev        : Sistemin kesintisiz çalışma durumunu takip eder.
Nasıl çalışır: Heartbeat, servis durumu, kuyruk sağlığı, kurtarma akışı ve
sağlık özeti üretir.

Ajan 141-155 | Finans ve Uyum Ajanları
Görev        : Gelir, komisyon, ödeme ve uyum süreçlerini yönetir.
Nasıl çalışır: Finansal özet, ödeme listesi, vergi hesabı ve raporlama çıktısı
üretir.

Ajan 156-161 | Üyelik ve Denetim Ajanları
Görev        : Yeni kullanıcı ve ortak adaylarını sisteme dahil eder.
Nasıl çalışır: Başvuru alır, uygunluk sinyallerini değerlendirir ve destek
akışını başlatır.

Ajan 162 | TRMGlobalAffiliateRecruiterAgent
Görev        : Küresel affiliate ortaklarını ve uluslararası iş birliklerini
sisteme kazandırır.
Nasıl çalışır: Hedef pazarları tarar, aday ortak listesi oluşturur, tanıtım
mesajı hazırlar ve partner verisini günceller.

Ajan 163 | TRMHumanAuditorAgent
Görev        : Adayların samimiyetini, motivasyonunu ve sistem uyumunu
değerlendirir.
Nasıl çalışır: Soru seti üretir, yanıtları analiz eder ve denetim kaydı
oluşturur.

Ajan 164 | TRMLocalRecruiterAgent
Görev        : Türkiye içindeki KOBİ, esnaf ve yerli üreticileri sisteme dahil
eder.
Nasıl çalışır: Şehir bazlı tarama yapar, tanıtım metni hazırlar ve yerel
partner kaydı açar.

Ajan 165 | TRMAccountingAgent
Görev        : Gelir, vergi, stopaj, ödeme ve destek bütçelerini hesaplar.
Nasıl çalışır: Komisyon ve gelir verilerini işleyerek net kâr, ödeme listesi
ve dağıtım özeti üretir.

==============================================================================
3. KODDA AÇIK TANIMLI 35 GENİŞLEME AJANI
==============================================================================
Bu ajanlar sistemde açık biçimde oluşturulur ve CoreNexus üzerinden
senkronize edilir. Üç ana aileden oluşurlar:
- 10 MarketIntelAgent
- 15 BridgeAgent
- 10 SentinelAgent

MarketIntelAgent_01 | Bölge: TR
MarketIntelAgent_02 | Bölge: EU
MarketIntelAgent_03 | Bölge: US
MarketIntelAgent_04 | Bölge: MENA
MarketIntelAgent_05 | Bölge: UK
MarketIntelAgent_06 | Bölge: DE
MarketIntelAgent_07 | Bölge: FR
MarketIntelAgent_08 | Bölge: NL
MarketIntelAgent_09 | Bölge: GCC
MarketIntelAgent_10 | Bölge: CEE
Görev        : Bölgesel fiyat, stok baskısı ve satış stratejisi sinyali üretir.
Nasıl çalışır: Trend raporundaki ürün detaylarını okuyup rekabet kırılımı,
öncelik seviyesi ve içerik yönü belirler.

BridgeAgent_01 | Ağ: AmazonEU
BridgeAgent_02 | Ağ: AmazonUS
BridgeAgent_03 | Ağ: Awin
BridgeAgent_04 | Ağ: CJ
BridgeAgent_05 | Ağ: Impact
BridgeAgent_06 | Ağ: Rakuten
BridgeAgent_07 | Ağ: TradeTracker
BridgeAgent_08 | Ağ: ShareASale
BridgeAgent_09 | Ağ: Partnerize
BridgeAgent_10 | Ağ: Webgains
BridgeAgent_11 | Ağ: ClickBank
BridgeAgent_12 | Ağ: Admitad
BridgeAgent_13 | Ağ: Tradedoubler
BridgeAgent_14 | Ağ: FlexOffers
BridgeAgent_15 | Ağ: Pepperjam
Görev        : Affiliate ağından teklif, katalog ve senkron sağlık verisi taşır.
Nasıl çalışır: Trend bağlamını okur; teklif sayısı, ağ tazeliği, katalog
büyüklüğü ve önerilen senkron modunu üretir.

SentinelAgent_01 | Alan: Gateway
SentinelAgent_02 | Alan: API
SentinelAgent_03 | Alan: Queue
SentinelAgent_04 | Alan: Worker
SentinelAgent_05 | Alan: Health
SentinelAgent_06 | Alan: Identity
SentinelAgent_07 | Alan: ZeroTrust
SentinelAgent_08 | Alan: Network
SentinelAgent_09 | Alan: Content
SentinelAgent_10 | Alan: Publishing
Görev        : Anomali, retry baskısı ve güvenlik riskini izler.
Nasıl çalışır: Kuyruk, paylaşım ve güvenlik durumunu okuyup uyarı seviyesi
belirler; çıktıyı HealthCheckAgent'a taşır.

==============================================================================
4. ÇEKİRDEKTE DOĞRUDAN ÇALIŞAN TEMEL AJANLAR
==============================================================================
CoreNexus
Görev        : Tüm ajanları bağlayan merkez orkestrasyon çekirdeğidir.
Nasıl çalışır: Ajanları kaydeder, bağlamı paylaştırır, Zero-Trust filtresi
uygular ve sonuçları ortak yapıya geri yazar.

CamouflageAgent
Görev        : Dil ve oturum maskelemesi yapar.
Nasıl çalışır: Terimleri dönüştürür, maskeleme moduna göre iz üretir ve
koruyucu katman sağlar.

AccountManagerAgent
Görev        : Operatör kimliği ve kurumsal e-posta üretir.
Nasıl çalışır: Ülke koduna göre rumuz oluşturur ve hesap bilgisini
yapılandırır.

AnalystAgent
Görev        : Ürün havuzunu trend skoruna göre analiz eder.
Nasıl çalışır: Metin, ilgi ve fırsat sinyallerini puanlayarak trend raporu
çıkarır.

ContentGeneratorAgent
Görev        : Trend ve komisyon bilgisini satış kopyasına dönüştürür.
Nasıl çalışır: Başlık, satış metni, sosyal gönderi ve CTA üretir; istihbarat
sinyallerini tona işler.

QueueAgent
Görev        : Üretilen içerikleri yayın kuyruğuna aktarır.
Nasıl çalışır: İçerik paketini okuyup 30 dakikalık planla sıraya dizer.

PosterAgent
Görev        : Zamanı gelen postları platformlara gönderir.
Nasıl çalışır: Kuyruktaki kaydı işler; sonucu `posted` veya `pending_retry`
olarak işaretler.

HealthCheckAgent
Görev        : Sistemin genel sağlık özetini çıkarır.
Nasıl çalışır: İnternet, API, kuyruk, Sentinel ve güvenlik durumunu
birleştirir.

StatsAgent
Görev        : Panel için canlı metrik üretir.
Nasıl çalışır: Aktif kullanıcı, havuz ve paylaşım sayıları gibi özet
ölçümleri hesaplar.

SocialUploaderAgent
Görev        : Sosyal medya yükleme hazırlığını yönetir.
Nasıl çalışır: Platform seçimi, API uygunluğu ve yükleme akışını yürütür ya da
simüle eder.

==============================================================================
5. KOD TABANINDA GÖRÜLEN EK VE ESKİ NESİL AJANLAR
==============================================================================
- MobileGatewayAgent: Mobil onay akışı ve sanal mobil ortam hazırlığı sağlar.
- CyberGuardianAgent: Yetkisiz giriş ve bütünlük ihlallerine karşı savunma
  taraması yapar.
- Agent168_LegalTax: Uluslararası vergi ve fatura uyumunu temsil eder.
- Agent169_MFABridge: SMS ve çok faktörlü doğrulama köprüsü işlevi görür.
- Agent170_AlgorithmShield: İade ve şikâyet baskısında mağaza koruma
  aksiyonları tanımlar.
- Agent171_PayoutDistribution: Ödeme dağıtımı ve transfer emri mantığını temsil
  eder.
- Agent172_PolicyCopyrightFilter: Telif ve platform politika taraması yapar.
- BrowserSpooferAgent: Tarayıcı parmak izi çeşitlendirir.
- HumanizerAgent: Davranışı daha insan benzeri gecikme ve yazım akışıyla
  yumuşatır.
- SentimentTrendAgent: Viral eğilimleri tarar ve vitrin yönü önerir.
- Legacy SentinelAgent: Etkileşim düşüşü ve benzeri riskleri karantina
  mantığıyla izler.

==============================================================================
6. SİSTEMİN ÇALIŞMA AKIŞI
==============================================================================
1. Veri kaynaklarından ürün ve trend sinyalleri toplanır.
2. AnalystAgent ve ilgili analiz katmanı fırsatları puanlar.
3. MarketIntelAgent ailesi fiyat ve rekabet zekâsı ekler.
4. ContentGeneratorAgent satış odaklı içerik üretir.
5. QueueAgent içerikleri zaman planına yerleştirir.
6. PosterAgent zamanı gelen gönderileri yayınlar.
7. BridgeAgent ailesi ağ ve teklif sağlığını günceller.
8. SentinelAgent ailesi risk ve anomali denetimi yapar.
9. HealthCheckAgent tüm zincirin sağlık raporunu üretir.
10. Streamlit paneli ve worker dosyaları durumu görünür kılar.

==============================================================================
7. SONUÇ
==============================================================================
SOSYAL İMECE içindeki 200 ajanlık sistem, yalnızca çok sayıda ajan
isminden oluşan bir liste değildir. Bu yapı; veri toplama, analiz, içerik
üretimi, yayın, güvenlik, ağ senkronizasyonu ve sağlık izleme katmanlarının
birbirine bağlı çalıştığı tam bir operasyon mimarisidir.

Bu nihai sürüm özellikle şu hedeflerle hazırlanmıştır:
- Türkçe karakter bozulmalarını gidermek
- Tekrarlı anlatımı azaltmak
- Daha profesyonel başlıklı ve kapaklı bir sunum vermek
- 165 + 35 mimarisini net biçimde açıklamak
- Kodda görülen gerçek ajan yapısını okunaklı şekilde özetlemek

Doküman sonu.
