from threading import Event

from security_utils import ZeroTrustSecurityManager


class CoreNexus:
    def __init__(self, domain="trm-operations.net", zero_trust=True, stealth_mode=True):
        self.domain = domain
        self.agents = {} # Ajanları burada tutacağız
        self.shared_context = {}
        self.agent_tokens = {}
        self._stop_requested = Event()
        self.security = ZeroTrustSecurityManager(
            zero_trust=zero_trust,
            stealth_mode=stealth_mode,
        )

    def connect_agent(self, agent_name, agent_instance, capabilities=None, context_allowlist=None):
        """Ajanı sisteme bağlar ve yetkilendirir."""
        self.agents[agent_name] = agent_instance
        self.security.register_agent(
            agent_name,
            capabilities=capabilities,
            context_allowlist=context_allowlist,
        )
        self.agent_tokens[agent_name] = self.security.agent_tokens.get(agent_name)
        print(f"[CoreNexus] {agent_name} başarıyla sisteme bağlandı ve denetim altına alındı.")

    def request_stop(self):
        self._stop_requested.set()

    def reset_stop_request(self):
        self._stop_requested.clear()

    def update_context(self, **kwargs):
        """Ajanlar arasında paylaşılacak bağlamı günceller."""
        self.shared_context.update(kwargs)
        for key, value in kwargs.items():
            self.security.protect_snapshot(key, value)
        self.shared_context["security_status"] = self.get_security_status()

    def get_agent(self, agent_name):
        """Bağlı bir ajanı döndürür."""
        return self.agents.get(agent_name)

    def get_security_status(self):
        report = self.security.get_security_report()
        report["domain"] = self.domain
        report["connected_agents"] = len(self.agents)
        return report

    def _build_agent_context(self, agent_name):
        agent_context = self.security.build_agent_context(agent_name, self.shared_context)
        agent_context["security_status"] = self.get_security_status()
        return agent_context

    def _store_result_in_context(self, agent_name, result):
        """Ajan sonucunu sonraki ajanların kullanabileceği bağlama ekler."""
        normalized = agent_name.lower().replace(" ", "_").replace("-", "_")
        self.shared_context[f"{normalized}_result"] = result
        self.security.protect_snapshot(f"{normalized}_result", result)

        if agent_name.startswith("MarketIntelAgent_"):
            self.shared_context.setdefault("market_intelligence_reports", []).append(result)
            smart_parameter = (result or {}).get("smart_parameter")
            if smart_parameter:
                self.shared_context.setdefault("smart_parameters", []).append(smart_parameter)
        elif agent_name.startswith("BridgeAgent_"):
            self.shared_context.setdefault("bridge_network_reports", []).append(result)
        elif agent_name.startswith("SentinelAgent_"):
            self.shared_context.setdefault("sentinel_alerts", []).append(result)

        alias_map = {
            "content_generator_agent": "content_payload",
            "queueagent": "queue_payload",
            "posteragent": "poster_payload",
            "healthcheckagent": "health_payload",
        }
        alias = alias_map.get(normalized)
        if alias:
            self.shared_context[alias] = result
            self.security.protect_snapshot(alias, result)
        self.shared_context["security_status"] = self.get_security_status()

    def run_system_sync(self, context=None):
        """Tüm bağlı ajanların altyapısını eş zamanlı çalıştırır."""
        if context:
            self.update_context(**context)

        sync_results = {}
        for name, agent in self.agents.items():
            if self._stop_requested.is_set():
                break
            token = self.agent_tokens.get(name)
            if not self.security.authorize(name, token):
                raise PermissionError(f"[CoreNexus] Yetkisiz ajan engellendi: {name}")

            print(f"[CoreNexus] {name} senkronize ediliyor...")
            result = None
            agent_context = self._build_agent_context(name)
            if hasattr(agent, "sync"):
                result = agent.sync(agent_context)
            elif hasattr(agent, "run"):
                result = agent.run()
            sync_results[name] = result
            self._store_result_in_context(name, result)

        return sync_results
