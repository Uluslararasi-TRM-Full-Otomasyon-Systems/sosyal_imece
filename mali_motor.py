# mali_motor.py (sonuna ekle)

def execute_sosyal_imece_distribution(net_profit: float, users: list[dict]) -> dict:
    allocations = {u['id']: {"phase_1_genel_refah": 0.0, "phase_2_zenginlik_55plus": 0.0, "total": 0.0} for u in users}
    total_users = len(users)
    
    if total_users == 0:
        return allocations

    # 1. Aşama: Herkese temel pay + %20 refah payı (Net kârın %80'i)
    phase1_pool = net_profit * 0.80
    per_user_phase1 = phase1_pool / total_users
    refah_pay_bonus = per_user_phase1 * 0.20
    total_phase1_per_user = per_user_phase1 + refah_pay_bonus

    for u in users:
        uid = u['id']
        allocations[uid]["phase_1_genel_refah"] = round(total_phase1_per_user, 2)

    # 2. Aşama: 55 yaş ve üzeri kişilere özel imece zenginlik payı (Net kârın kalan %20'si)
    wealth_pool = net_profit * 0.20
    older_users = [u for u in users if u.get('age', 0) >= 55]
    num_older = len(older_users)
    
    per_older_wealth = (wealth_pool / num_older) if num_older > 0 else 0.0

    for u in older_users:
        uid = u['id']
        allocations[uid]["phase_2_zenginlik_55plus"] = round(per_older_wealth, 2)

    # Toplam hesaplama
    for u in users:
        uid = u['id']
        allocations[uid]["total"] = round(
            allocations[uid]["phase_1_genel_refah"] + allocations[uid]["phase_2_zenginlik_55plus"], 2
        )

    return allocations


if __name__ == "__main__":
    import json

    # Test verisi (40.000 TL net kâr senaryosu)
    test_net_profit = 40000.0
    test_users = [
        {"id": "uye_fahri", "age": 63},
        {"id": "uye_genc_1", "age": 29},
        {"id": "uye_olgun_1", "age": 57},
        {"id": "uye_genc_2", "age": 34}
    ]

    print("--- SOSYAL İMECE DAĞITIM TESTİ BAŞLATILIYOR ---")
    sonuclar = execute_sosyal_imece_distribution(test_net_profit, test_users)
    print(json.dumps(sonuclar, indent=4, ensure_ascii=False))