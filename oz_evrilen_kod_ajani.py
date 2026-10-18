import ast
from copy import deepcopy
import os
from pathlib import Path
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager


_COMPONENTS = {
    "DispatchQueueManager (SQLite)": "dispatch_queue_manager.py",
    "İlk 3 Saniye Motoru (hook şablonları)": "ilk_uc_saniye_motoru.py",
}


class OzEvrilenKodAjani:
    def __init__(self, hedef_modul="Komuta Merkezi & Akışlar", project_root=None):
        if not isinstance(hedef_modul, str) or not hedef_modul.strip():
            raise ValueError("hedef_modul boş olmayan bir metin olmalıdır")
        self.hedef_modul = hedef_modul.strip()
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent

    @staticmethod
    def _hook_template_count(tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "_HOOK_TEMPLATES"
                for target in node.targets
            ):
                value = node.value
                if isinstance(value, (ast.Tuple, ast.List)):
                    return len(value.elts)
        return None

    def _inspect_component(self, component, filename):
        path = self.project_root / filename
        if not path.is_file():
            return {
                "bilesen": component,
                "dosya": filename,
                "durum": "missing",
                "bulgular": ["Kaynak dosya bulunamadı; analiz yapılmadı."],
                "oneriler": [],
            }

        source = path.read_text(encoding="utf-8-sig")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            return {
                "bilesen": component,
                "dosya": filename,
                "durum": "syntax_error",
                "bulgular": [f"AST ayrıştırması başarısız: satır {exc.lineno or '?'}"],
                "oneriler": ["Kaynak sözdizimini gözden geçirin; sentinel dosyayı değiştirmez."],
            }
        functions = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        long_functions = [
            node.name for node in functions
            if getattr(node, "end_lineno", node.lineno) - node.lineno + 1 > 60
        ]
        findings = [
            f"AST ayrıştırması başarılı; {len(source.splitlines())} kaynak satırı, "
            f"{len(functions)} fonksiyon/metot bulundu."
        ]
        suggestions = []
        if long_functions:
            findings.append("60 satırı aşan fonksiyonlar: " + ", ".join(sorted(long_functions)))
            suggestions.append("Uzun fonksiyonları tek sorumluluklu yardımcı parçalara ayırmayı değerlendirin.")

        if filename == "dispatch_queue_manager.py":
            pending_filter = "WHERE status = 'pending'" in source
            has_status_index = "INDEX" in source.upper() and "STATUS" in source.upper()
            findings.append(
                "task_queue pending durum filtresi "
                + ("bulundu." if pending_filter else "kaynakta bulunamadı.")
            )
            if pending_filter and not has_status_index:
                suggestions.append(
                    "status için indeks olası bir aday; değişiklikten önce gerçek DB'de EXPLAIN QUERY PLAN ve ölçüm alın."
                )

        if filename == "ilk_uc_saniye_motoru.py":
            template_count = self._hook_template_count(tree)
            findings.append(f"Statik kanca şablonu sayısı: {template_count or 0}.")
            if template_count is not None and template_count < 5:
                suggestions.append(
                    "Şablon çeşitliliğini artırmayı ancak doğruluk ve kullanılabilirlik testleriyle değerlendirin; otomatik prompt değişikliği yapılmadı."
                )

        if not suggestions:
            suggestions.append("Bu statik kontrolde doğrudan refactor gerektiren bir eşik bulunmadı.")
        return {
            "bilesen": component,
            "dosya": filename,
            "durum": "analyzed",
            "bulgular": findings,
            "oneriler": suggestions,
        }

    def kod_ve_prompt_optimizasyonu_tara(self, bilesen=None):
        if bilesen is None or bilesen == "Tüm bileşenler":
            selected = list(_COMPONENTS.items())
        elif bilesen in _COMPONENTS:
            selected = [(bilesen, _COMPONENTS[bilesen])]
        else:
            raise ValueError("Desteklenmeyen bileşen seçildi")

        components = [self._inspect_component(name, filename) for name, filename in selected]
        return {
            "hedef_modul": self.hedef_modul,
            "bilesenler": components,
            "veri_kaynagi": "yerel kaynak kodunun salt-okunur AST incelemesi",
            "guven_orani": None,
            "otomatik_kod_degisikligi": False,
            "otomatik_prompt_degisikligi": False,
            "not": "Öneriler statik bulgulara dayanır; performans kazancı ölçülmedi ve kod değiştirilmedi.",
        }

    def inceleme_kuyruguna_ekle(self, rapor, db_path=None):
        if not isinstance(rapor, dict) or not isinstance(rapor.get("bilesenler"), list):
            raise ValueError("Geçerli statik inceleme raporu gereklidir")

        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        task = {
            "account_id": "oz_evrilen_kod_ajani",
            "post_id": f"code-review-{uuid4().hex}",
            "payload": {
                "task_type": "static_refactor_review",
                "status": "pending_review",
                "report": deepcopy(rapor),
            },
        }
        DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
        return task