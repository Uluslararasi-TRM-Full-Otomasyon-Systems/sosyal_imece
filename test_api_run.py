#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for /api/run endpoint - trendurunlermarket.com content generation
"""

import requests
import json

def test_api_run():
    print("Testing /api/run endpoint for trendurunlermarket.com...")
    print("=" * 60)
    
    # API base URL
    base_url = "http://localhost:5000"
    
    # Test payload
    payload = {
        "target_site": "trendurunlermarket.com",
        "content_type": "product_description",
        "agent_count": 50
    }
    
    print(f"Sending request to {base_url}/api/run")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{base_url}/api/run",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                print("\n[OK] Content generation successful!")
                data = result.get("data", {})
                print(f"  Execution ID: {data.get('execution_id')}")
                print(f"  Target Site: {data.get('target_site')}")
                print(f"  LLM Provider: {data.get('llm_provider')}")
                print(f"  LLM Model: {data.get('llm_model')}")
                print(f"  Agents Active: {data.get('agents_active')}")
                print(f"  Content Length: {len(data.get('generated_content', ''))} chars")
            else:
                print(f"\n[ERROR] Content generation failed: {result.get('error')}")
        else:
            print(f"[ERROR] Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is orchestrator_api.py running?")
        print("Start it with: python orchestrator_api.py")
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_api_run()
