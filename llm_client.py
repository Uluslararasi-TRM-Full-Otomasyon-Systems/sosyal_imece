#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Client Module
Provides unified interface for Gemini, Groq, and OpenRouter
All credentials loaded from environment via config.py
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

import requests

from config import SecureConfig, config as app_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"


GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
]

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


class LLMClient:
    """Unified LLM client supporting multiple providers (SDK or HTTP)."""

    def __init__(self, cfg: Optional[SecureConfig] = None):
        self.config = cfg or app_config
        self.primary_provider = self._determine_primary_provider()
        self.clients = {}
        self.http_providers = set()
        self._initialize_clients()

    def _determine_primary_provider(self) -> Optional[LLMProvider]:
        """Prefer Groq, then Gemini, then OpenRouter when keys exist."""
        if self.config.groq_api_key:
            return LLMProvider.GROQ
        if self.config.gemini_api_key:
            return LLMProvider.GEMINI
        if self.config.openrouter_api_key:
            return LLMProvider.OPENROUTER
        return None

    def _initialize_clients(self):
        """Initialize available provider clients from config / environment keys."""
        if self.config.groq_api_key:
            try:
                from groq import Groq
                self.clients[LLMProvider.GROQ] = Groq(api_key=self.config.groq_api_key)
                logger.info("Groq client initialized (SDK)")
            except Exception as e:
                self.http_providers.add(LLMProvider.GROQ)
                self.clients[LLMProvider.GROQ] = "http"
                logger.info("Groq HTTP wrapper active (%s)", e.__class__.__name__)

        if self.config.gemini_api_key:
            gemini_key = self.config.gemini_api_key
            # AI Studio keys start with AIza; AQ. keys are Cloud API keys — use HTTP wrapper.
            use_http = gemini_key.startswith("AQ.")
            if not use_http:
                try:
                    from google import genai
                    self.clients[LLMProvider.GEMINI] = genai.Client(api_key=gemini_key)
                    logger.info("Gemini client initialized (SDK)")
                except Exception as e:
                    use_http = True
                    logger.info("Gemini SDK unavailable (%s)", e.__class__.__name__)
            if use_http:
                self.http_providers.add(LLMProvider.GEMINI)
                self.clients[LLMProvider.GEMINI] = "http"
                logger.info("Gemini HTTP wrapper active")

        if self.config.openrouter_api_key:
            try:
                from openai import OpenAI
                self.clients[LLMProvider.OPENROUTER] = OpenAI(
                    api_key=self.config.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                logger.info("OpenRouter client initialized (SDK)")
            except Exception as e:
                self.http_providers.add(LLMProvider.OPENROUTER)
                self.clients[LLMProvider.OPENROUTER] = "http"
                logger.info("OpenRouter HTTP wrapper active (%s)", e.__class__.__name__)

        if not self.clients:
            logger.warning("No LLM provider keys found in environment")

    def is_configured(self) -> bool:
        """True if a key is present and a client/wrapper is bound."""
        return bool(self.clients) and self.config.is_llm_configured()

    def generate_content(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate content; fall back across configured providers on failure."""
        order = []
        target = provider or self.primary_provider
        if target:
            order.append(target)
        for p in (LLMProvider.GROQ, LLMProvider.GEMINI, LLMProvider.OPENROUTER):
            if p not in order and p in self.clients:
                order.append(p)

        if not order:
            return {
                "content": None,
                "provider": None,
                "model": None,
                "error": "No LLM provider configured",
            }

        last_error = None
        for target_provider in order:
            try:
                if target_provider == LLMProvider.GROQ:
                    result = self._generate_with_groq(prompt, model, max_tokens, temperature)
                elif target_provider == LLMProvider.GEMINI:
                    result = self._generate_with_gemini(prompt, model, max_tokens, temperature)
                else:
                    result = self._generate_with_openrouter(prompt, model, max_tokens, temperature)
                if not result.get("error"):
                    return result
                last_error = result.get("error")
                logger.warning("Provider %s failed: %s", target_provider.value, last_error)
            except Exception as e:
                last_error = str(e)
                logger.error("Content generation error with %s: %s", target_provider.value, e)

        return {
            "content": None,
            "provider": order[0].value if order else None,
            "model": model,
            "error": last_error or "All LLM providers failed",
        }

    def _generate_with_groq(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        models_to_try = ([model] if model else []) + GROQ_MODELS
        last_error = None
        for model_name in models_to_try:
            try:
                if self.clients[LLMProvider.GROQ] == "http":
                    text = self._http_openai_compat(
                        "https://api.groq.com/openai/v1/chat/completions",
                        self.config.groq_api_key,
                        model_name,
                        prompt,
                        max_tokens,
                        temperature,
                    )
                else:
                    client = self.clients[LLMProvider.GROQ]
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    text = response.choices[0].message.content
                if not (text or "").strip():
                    raise ValueError("empty content")
                return {
                    "content": text,
                    "provider": LLMProvider.GROQ.value,
                    "model": model_name,
                    "error": None,
                }
            except Exception as e:
                last_error = str(e)
                logger.warning("Groq model %s failed: %s", model_name, last_error)
        return {
            "content": None,
            "provider": LLMProvider.GROQ.value,
            "model": None,
            "error": last_error or "All Groq models failed",
        }

    def _generate_with_gemini(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        models_to_try = ([model] if model else []) + GEMINI_MODELS
        last_error = None
        for model_name in models_to_try:
            try:
                if self.clients[LLMProvider.GEMINI] == "http":
                    text = self._http_gemini(model_name, prompt, max_tokens, temperature)
                else:
                    client = self.clients[LLMProvider.GEMINI]
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={"max_output_tokens": max_tokens, "temperature": temperature},
                    )
                    text = response.text
                return {
                    "content": text,
                    "provider": LLMProvider.GEMINI.value,
                    "model": model_name,
                    "error": None,
                }
            except Exception as e:
                last_error = str(e)
                logger.warning("Gemini model %s failed: %s", model_name, last_error)
        return {
            "content": None,
            "provider": LLMProvider.GEMINI.value,
            "model": None,
            "error": last_error or "All Gemini models failed",
        }

    def _generate_with_openrouter(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        model_name = model or "openai/gpt-4o-mini"
        if self.clients[LLMProvider.OPENROUTER] == "http":
            text = self._http_openai_compat(
                "https://openrouter.ai/api/v1/chat/completions",
                self.config.openrouter_api_key,
                model_name,
                prompt,
                max_tokens,
                temperature,
                extra_headers={
                    "HTTP-Referer": "https://trendurunlermarket.com",
                    "X-Title": "Sosyal Imece TRM",
                },
            )
        else:
            client = self.clients[LLMProvider.OPENROUTER]
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content
        return {
            "content": text,
            "provider": LLMProvider.OPENROUTER.value,
            "model": model_name,
            "error": None,
        }

    def _http_openai_compat(
        self,
        url: str,
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        resp = requests.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _http_gemini(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        resp = requests.post(
            url,
            params={"key": self.config.gemini_api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                },
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def get_available_providers(self) -> List[str]:
        return [p.value for p in self.clients.keys()]

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "config_is_llm_configured": self.config.is_llm_configured(),
            "primary_provider": self.primary_provider.value if self.primary_provider else None,
            "available_providers": self.get_available_providers(),
            "configured_keys": self.config.configured_llm_providers(),
            "has_gemini": LLMProvider.GEMINI in self.clients,
            "has_groq": LLMProvider.GROQ in self.clients,
            "has_openrouter": LLMProvider.OPENROUTER in self.clients,
        }


_llm_client_instance = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance


if __name__ == "__main__":
    print("Testing LLM Client...")
    client = get_llm_client()
    print(f"Status: {client.get_status()}")
    if client.is_configured():
        result = client.generate_content("Reply with exactly: OK")
        print(f"Provider: {result.get('provider')} model: {result.get('model')} error: {result.get('error')}")
        print(f"Content length: {len(result.get('content') or '')}")
    else:
        print("No LLM provider configured")
