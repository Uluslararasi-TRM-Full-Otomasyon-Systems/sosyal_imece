import ast
import os
from urllib.parse import urlparse

import requests


class MultiModelGateway:
    def __init__(
        self,
        varsayilan_saglayici="lokal_ollama",
        ollama_url=None,
        ollama_model=None,
        llm_client=None,
        request_timeout=30,
    ):
        if varsayilan_saglayici not in {"lokal_ollama", "configured_cloud"}:
            raise ValueError("varsayilan_saglayici lokal_ollama veya configured_cloud olmalıdır")
        self.varsayilan_saglayici = varsayilan_saglayici
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL") or "llama3.2"
        self.llm_client = llm_client
        self.request_timeout = request_timeout
        self._validate_local_ollama_url()

    def _validate_local_ollama_url(self):
        parsed = urlparse(self.ollama_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Ollama URL’si yalnızca loopback host üzerinde HTTP olabilir")

    @staticmethod
    def _analyze_python_ast(source):
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return {
                "status": "error",
                "provider": "local_ast",
                "model": None,
                "content": None,
                "error": f"Python sözdizimi hatası: satır {exc.lineno or '?'}",
            }

        functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = sorted({
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        })
        return {
            "status": "draft_ready",
            "provider": "local_ast",
            "model": "Python AST",
            "content": {
                "syntax_valid": True,
                "line_count": len(source.splitlines()),
                "functions": functions,
                "classes": classes,
                "imports": imports,
            },
            "error": None,
        }

    def _run_ollama(self, prompt):
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={"model": self.ollama_model, "prompt": prompt, "stream": False},
            timeout=self.request_timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("response")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Ollama boş yanıt döndürdü")
        return {
            "status": "draft_ready",
            "provider": "ollama",
            "model": payload.get("model", self.ollama_model),
            "content": content.strip(),
            "error": None,
        }

    def _get_llm_client(self):
        if self.llm_client is not None:
            return self.llm_client
        from llm_client import get_llm_client

        self.llm_client = get_llm_client()
        return self.llm_client

    def _run_cloud(self, prompt, preferred_provider=None):
        try:
            from llm_client import LLMProvider

            client = self._get_llm_client()
            if not client.is_configured():
                return None
            provider = LLMProvider(preferred_provider) if preferred_provider else None
            if provider and provider.value not in client.get_available_providers():
                provider = None
            result = client.generate_content(prompt, provider=provider)
            if result.get("content"):
                return {
                    "status": "draft_ready",
                    "provider": result.get("provider"),
                    "model": result.get("model"),
                    "content": result["content"],
                    "error": None,
                }
            return {
                "status": "error",
                "provider": result.get("provider"),
                "model": result.get("model"),
                "content": None,
                "error": result.get("error") or "Configured providers returned no content",
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": preferred_provider or "configured_cloud",
                "model": None,
                "content": None,
                "error": f"Cloud provider error: {exc.__class__.__name__}",
            }

    def akilli_yonlendir(self, gorev_turu, girdi_metni, allow_cloud=False):
        if not isinstance(gorev_turu, str) or not gorev_turu.strip():
            raise ValueError("gorev_turu boş olmayan bir metin olmalıdır")
        if not isinstance(girdi_metni, str) or not girdi_metni.strip():
            raise ValueError("girdi_metni boş olmayan bir metin olmalıdır")
        if not isinstance(allow_cloud, bool):
            raise ValueError("allow_cloud boolean olmalıdır")

        task = gorev_turu.strip()
        prompt = girdi_metni.strip()
        if task == "kod_ast_analizi":
            routed = self._analyze_python_ast(prompt)
            route_reason = "Kod yerel Python AST ile incelendi; dış sağlayıcı kullanılmadı."
        else:
            routed = None
            cloud_failure = None
            cloud_attempted = False
            route_reason = ""
            prefer_cloud = allow_cloud and (
                task == "hizli_kanca" or self.varsayilan_saglayici == "configured_cloud"
            )
            if prefer_cloud:
                preferred = "groq" if task == "hizli_kanca" else None
                cloud_failure = self._run_cloud(prompt, preferred_provider=preferred)
                cloud_attempted = True
                if cloud_failure and cloud_failure["status"] == "draft_ready":
                    routed = cloud_failure
                    route_reason = (
                        "Bulut kullanımı açıkça onaylandı; Groq hızlı görev sağlayıcısı olarak kullanıldı."
                        if preferred == "groq"
                        else "Bulut kullanımı açıkça onaylandı; yapılandırılmış sağlayıcı kullanıldı."
                    )

            if routed is None or routed["status"] != "draft_ready":
                local_result = None
                try:
                    local_result = self._run_ollama(prompt)
                except (requests.RequestException, ValueError) as exc:
                    local_result = {
                        "status": "unavailable",
                        "provider": "ollama",
                        "model": self.ollama_model,
                        "content": None,
                        "error": f"Yerel Ollama kullanılamıyor: {exc.__class__.__name__}",
                    }
                if local_result["status"] == "draft_ready":
                    routed = local_result
                    route_reason = "İstek yerel Ollama modeliyle işlendi."
                elif allow_cloud and not cloud_attempted:
                    cloud_result = self._run_cloud(prompt)
                    if cloud_result and cloud_result["status"] == "draft_ready":
                        routed = cloud_result
                        route_reason = "Yerel model yok; açık bulut izniyle yapılandırılmış LLM kullanıldı."
                    else:
                        routed = cloud_result or local_result
                        route_reason = "Yerel ve izinli sağlayıcı kullanılamadı."
                elif cloud_failure is not None:
                    routed = cloud_failure
                    route_reason = "İzinli bulut sağlayıcısı ve yerel model kullanılamadı."
                else:
                    routed = local_result
                    route_reason = "Bulut sağlayıcısına veri gönderilmedi; yerel model kullanılamadı."

        return {
            "gorev_turu": task,
            "varsayilan_saglayici": self.varsayilan_saglayici,
            "secilen_saglayici": routed["provider"],
            "model": routed["model"],
            "durum": routed["status"],
            "icerik": routed["content"],
            "optimizasyon_kriteri": route_reason,
            "bulut_izni": allow_cloud,
            "islem_ozeti": (
                "İçerik sağlayıcı tarafından üretildi."
                if routed["status"] == "draft_ready"
                else routed["error"]
            ),
        }