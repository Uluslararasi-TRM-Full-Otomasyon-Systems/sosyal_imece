#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication Manager
TRM Ticari Ekosistem Sistemi için API Key tabanlı kimlik doğrulama
"""

import secrets
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

class AuthManager:
    def __init__(self, config_file='api_keys.json'):
        self.config_file = config_file
        self.api_keys = self.load_api_keys()
        self.default_api_key = self.get_or_create_default_key()
    
    def load_api_keys(self):
        """API keys'i dosyadan yükle"""
        try:
            config_path = Path(__file__).parent / self.config_file
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"[Auth] API keys yüklenemedi: {e}")
            return {}
    
    def save_api_keys(self):
        """API keys'i dosyaya kaydet"""
        try:
            config_path = Path(__file__).parent / self.config_file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.api_keys, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Auth] API keys kaydedilemedi: {e}")
            return False
    
    def generate_api_key(self, name='default', description=''):
        """Yeni API key oluştur"""
        # Güvenli random key oluştur
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'active': True
        }
        
        self.save_api_keys()
        
        return key, key_hash
    
    def get_or_create_default_key(self):
        """Varsayılan API key'i oluştur veya getir"""
        # Varsayılan key hash'i
        default_hash = hashlib.sha256('trm-ticari-default-key-2026'.encode()).hexdigest()
        
        if default_hash not in self.api_keys:
            self.api_keys[default_hash] = {
                'name': 'default',
                'description': 'Varsayılan API key',
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'active': True
            }
            self.save_api_keys()
        
        return 'trm-ticari-default-key-2026'
    
    def validate_api_key(self, api_key):
        """API key'i doğrula"""
        if not api_key:
            return False, 'API key gerekli'
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash not in self.api_keys:
            return False, 'Geçersiz API key'
        
        key_data = self.api_keys[key_hash]
        
        if not key_data.get('active', True):
            return False, 'API key devre dışı'
        
        # Son kullanım zamanını güncelle
        key_data['last_used'] = datetime.now().isoformat()
        self.save_api_keys()
        
        return True, 'API key geçerli'
    
    def revoke_api_key(self, api_key):
        """API key'i iptal et"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            self.api_keys[key_hash]['active'] = False
            self.save_api_keys()
            return True
        
        return False
    
    def list_api_keys(self):
        """Tüm API key'leri listele (hash'ler ile)"""
        keys_info = []
        for key_hash, key_data in self.api_keys.items():
            keys_info.append({
                'hash': key_hash[:16] + '...',  # İlk 16 karakter
                'name': key_data.get('name'),
                'description': key_data.get('description'),
                'created_at': key_data.get('created_at'),
                'last_used': key_data.get('last_used'),
                'active': key_data.get('active', True)
            })
        return keys_info
    
    def get_default_api_key(self):
        """Varsayılan API key'i döndür (panel için)"""
        return self.default_api_key

# Authentication decorator
def require_auth(auth_manager):
    """API endpoint'leri için authentication decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # API key'i header'dan al
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                # Query parameter'dan da kontrol et
                api_key = request.args.get('api_key')
            
            if not api_key:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'API key gerekli. X-API-Key header veya api_key query parameter kullanın.'
                }), 401
            
            is_valid, message = auth_manager.validate_api_key(api_key)
            
            if not is_valid:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': message
                }), 401
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Optional authentication decorator (public endpoints için)
def optional_auth(auth_manager):
    """İsteğe bağlı authentication decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if api_key:
                is_valid, message = auth_manager.validate_api_key(api_key)
                if not is_valid:
                    return jsonify({
                        'error': 'Unauthorized',
                        'message': message
                    }), 401
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Test usage
if __name__ == "__main__":
    auth = AuthManager()
    
    print("[Auth] Authentication Manager Test")
    print(f"[Auth] Default API Key: {auth.get_default_api_key()}")
    
    # Test validation
    is_valid, message = auth.validate_api_key(auth.get_default_api_key())
    print(f"[Auth] Validation Test: {is_valid} - {message}")
    
    # List keys
    keys = auth.list_api_keys()
    print(f"[Auth] Total API Keys: {len(keys)}")
    for key in keys:
        print(f"  - {key['name']}: {key['hash']} (Active: {key['active']})")
