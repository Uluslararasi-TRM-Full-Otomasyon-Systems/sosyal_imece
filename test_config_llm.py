#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify config.is_llm_configured() functionality
"""

import os
from config import SecureConfig

def test_config_llm():
    print("Testing Config LLM Configuration...")
    print("=" * 50)
    
    # Load config
    cfg = SecureConfig()
    
    # Check individual keys
    print(f"OPENROUTER_API_KEY: {'[SET]' if cfg.openrouter_api_key else '[NOT SET]'}")
    print(f"GEMINI_API_KEY: {'[SET]' if cfg.gemini_api_key else '[NOT SET]'}")
    print(f"GROQ_API_KEY: {'[SET]' if cfg.groq_api_key else '[NOT SET]'}")
    print()
    
    # Check is_llm_configured
    is_configured = cfg.is_llm_configured()
    print(f"is_llm_configured(): {is_configured}")
    print(f"configured_llm_providers(): {cfg.configured_llm_providers()}")
    
    assert is_configured is True, "config.is_llm_configured() must be True when GEMINI/GROQ/OPENROUTER key is set"
    print("[OK] assert config.is_llm_configured() == True")
    
    if is_configured:
        print("[OK] LLM is properly configured")
    else:
        print("[ERROR] LLM is NOT configured - at least one API key needed")
    
    print("=" * 50)
    
    # Also test LLM client
    print("\nTesting LLM Client...")
    print("=" * 50)
    
    try:
        from llm_client import get_llm_client
        llm_client = get_llm_client()
        status = llm_client.get_status()
        
        print(f"LLM Client Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        if status["configured"]:
            print("[OK] LLM Client is configured and ready")
        else:
            print("[ERROR] LLM Client is not configured")
            
    except Exception as e:
        print(f"[ERROR] LLM Client test failed: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_config_llm()
