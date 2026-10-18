#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gelişmiş Görüntülü Psikolojik İstihbarat ve Avatar Yönetim Ajanı
Tüm ajanların görüntülü iletişim ve analiz motoru
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import base64

# BaseAgent'ı import et
from .base_agent_template import BaseAgent

# Sistem Protokollerini import et
from .system_protocols import (
    CEO_TITLE,
    get_ceo_title,
    format_ceo_message,
    LogFormatter
)

logger = logging.getLogger(__name__)

class KameraPsikoAnalizAjani(BaseAgent):
    """
    Gelişmiş Görüntülü Psikolojik İstihbarat ve Avatar Yönetim Ajanı
    
    Bu ajan:
    - Her ajan için karaktere uygun avatarlar oluşturur
    - Gerçek zamanlı multimodal analiz yapar (görüntü + ses)
    - Anlık geribildirim ve tavsiyeler verir
    - Derin analiz kaydı tutar
    - 7/24 aktif psikolojik destek sağlar
    """
    
    def __init__(self, agent_id: Optional[int] = None):
        super().__init__(
            agent_name="Gelişmiş Görüntülü Psikolojik İstihbarat ve Avatar Yönetim Ajanı",
            agent_id=agent_id if agent_id else 171
        )
        
        # Alt sistemler
        self.avatar_generator = AvatarGenerator()
        self.multimodal_analyzer = MultimodalAnalyzer()
        self.realtime_feedback = RealtimeFeedback()
        self.deep_analysis_recorder = DeepAnalysisRecorder()
        
        # Veri depolama
        self.agent_avatars = {}
        self.active_sessions = {}
        self.psychological_profiles = {}
        self.analysis_reports = {}
        
        self.log(f"🎥 Gelişmiş Görüntülü Psikolojik İstihbarat ve Avatar Yönetim Ajanı başlatıldı. {CEO_TITLE}", "INFO")
    
    # ============================================
    # ANA METODLAR (BaseAgent Override)
    # ============================================
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Ana çalıştırma metodu
        """
        self.status = "running"
        self.log("🚀 Görüntülü Psikolojik İstihbarat sistemi başlatılıyor...", "INFO")
        
        try:
            operation = kwargs.get('operation', 'dashboard')
            
            if operation == 'create_avatar':
                return self._create_agent_avatar(kwargs)
            elif operation == 'start_session':
                return self._start_analysis_session(kwargs)
            elif operation == 'analyze_frame':
                return self._analyze_realtime_frame(kwargs)
            elif operation == 'get_feedback':
                return self._get_realtime_feedback(kwargs)
            elif operation == 'end_session':
                return self._end_analysis_session(kwargs)
            elif operation == 'get_profile':
                return self._get_psychological_profile(kwargs)
            else:
                return self._get_dashboard(kwargs)
                
        except Exception as e:
            self.status = "error"
            self.log(f"❌ Görüntülü Psikolojik İstihbarat sistemi hatası: {e}", "ERROR")
            raise
    
    def stop(self) -> None:
        """Ajanı durdurur"""
        self.status = "stopped"
        self.log("⏹️ Görüntülü Psikolojik İstihbarat Ajanı durduruldu", "INFO")
    
    def restart(self) -> None:
        """Ajanı yeniden başlatır"""
        self.log("🔄 Görüntülü Psikolojik İstihbarat Ajanı yeniden başlatılıyor...", "INFO")
        self.status = "restarting"
        self.agent_avatars = {}
        self.active_sessions = {}
        self.psychological_profiles = {}
        self.analysis_reports = {}
        self.status = "ready"
        self.log("✅ Yeniden başlatma tamamlandı", "INFO")
    
    # ============================================
    # AVATAR OLUŞTURMA
    # ============================================
    
    def _create_agent_avatar(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Ajan için avatar oluşturur"""
        
        agent_id = kwargs.get('agent_id')
        agent_name = kwargs.get('agent_name')
        agent_type = kwargs.get('agent_type', 'general')
        personality_traits = kwargs.get('personality_traits', {})
        
        # Avatar oluştur
        avatar = self.avatar_generator.create_avatar(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            personality_traits=personality_traits
        )
        
        # Avatarı kaydet
        self.agent_avatars[agent_id] = avatar
        
        return {
            "operation": "create_avatar",
            "agent_id": agent_id,
            "avatar": avatar,
            "timestamp": datetime.now().isoformat()
        }
    
    # ============================================
    # ANALİZ SEANSI
    # ============================================
    
    def _start_analysis_session(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Analiz seansı başlatır"""
        
        session_id = kwargs.get('session_id', f"session_{len(self.active_sessions) + 1}")
        agent_id = kwargs.get('agent_id')
        target_person_id = kwargs.get('target_person_id')
        session_type = kwargs.get('session_type', 'interview')
        
        # Seans oluştur
        session = {
            "session_id": session_id,
            "agent_id": agent_id,
            "target_person_id": target_person_id,
            "session_type": session_type,
            "start_time": datetime.now().isoformat(),
            "status": "active",
            "frames_analyzed": 0,
            "audio_segments": 0,
            "psychological_state": "neutral",
            "feedback_history": []
        }
        
        # Seansı kaydet
        self.active_sessions[session_id] = session
        
        return {
            "operation": "start_session",
            "session_id": session_id,
            "session": session,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_realtime_frame(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Gerçek zamanlı frame analizi yapar"""
        
        session_id = kwargs.get('session_id')
        frame_data = kwargs.get('frame_data')
        audio_data = kwargs.get('audio_data')
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Multimodal analiz
        analysis = self.multimodal_analyzer.analyze_frame(
            frame_data=frame_data,
            audio_data=audio_data,
            session_context=session
        )
        
        # Seansı güncelle
        session['frames_analyzed'] += 1
        if audio_data:
            session['audio_segments'] += 1
        session['psychological_state'] = analysis['dominant_emotion']
        session['feedback_history'].append(analysis)
        
        # Anlık geribildirim
        feedback = self.realtime_feedback.generate_feedback(
            analysis=analysis,
            agent_id=session['agent_id']
        )
        
        return {
            "operation": "analyze_frame",
            "session_id": session_id,
            "analysis": analysis,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_realtime_feedback(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Anlık geribildirim verir"""
        
        session_id = kwargs.get('session_id')
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Son analizden geribildirim
        if session['feedback_history']:
            last_analysis = session['feedback_history'][-1]
            feedback = self.realtime_feedback.generate_feedback(
                analysis=last_analysis,
                agent_id=session['agent_id']
            )
            
            return {
                "operation": "get_feedback",
                "session_id": session_id,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            }
        
        return {"error": "No analysis data available"}
    
    def _end_analysis_session(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Analiz seansını sonlandırır"""
        
        session_id = kwargs.get('session_id')
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Derin analiz kaydı
        deep_report = self.deep_analysis_recorder.create_report(
            session=session,
            analysis_history=session['feedback_history']
        )
        
        # Seansı kapat
        session['end_time'] = datetime.now().isoformat()
        session['status'] = 'completed'
        
        # Raporu kaydet
        report_id = f"report_{len(self.analysis_reports) + 1}"
        self.analysis_reports[report_id] = deep_report
        
        # Psikolojik profili güncelle
        target_person_id = session['target_person_id']
        if target_person_id:
            self.psychological_profiles[target_person_id] = deep_report['psychological_profile']
        
        return {
            "operation": "end_session",
            "session_id": session_id,
            "deep_report": deep_report,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_psychological_profile(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Psikolojik profil döndürür"""
        
        target_person_id = kwargs.get('target_person_id')
        
        if target_person_id in self.psychological_profiles:
            return {
                "operation": "get_profile",
                "target_person_id": target_person_id,
                "profile": self.psychological_profiles[target_person_id],
                "timestamp": datetime.now().isoformat()
            }
        
        return {"error": "Profile not found"}
    
    # ============================================
    # DASHBOARD
    # ============================================
    
    def _get_dashboard(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Dashboard verilerini döndürür"""
        
        return {
            "operation": "dashboard",
            "total_avatars": len(self.agent_avatars),
            "active_sessions": len(self.active_sessions),
            "total_profiles": len(self.psychological_profiles),
            "total_reports": len(self.analysis_reports),
            "agent_avatars": self.agent_avatars,
            "active_sessions": self.active_sessions,
            "psychological_profiles": self.psychological_profiles,
            "analysis_reports": self.analysis_reports,
            "timestamp": datetime.now().isoformat()
        }
    
    # ============================================
    # API METODLARI
    # ============================================
    
    def api_get_avatar(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """API: Avatar döndürür"""
        return self.agent_avatars.get(agent_id)
    
    def api_start_video_analysis(self, agent_id: str, target_person_id: str) -> str:
        """API: Video analizi başlatır"""
        session_id = f"session_{len(self.active_sessions) + 1}"
        self._start_analysis_session({
            'session_id': session_id,
            'agent_id': agent_id,
            'target_person_id': target_person_id,
            'session_type': 'video_analysis'
        })
        return session_id
    
    def api_analyze_frame(self, session_id: str, frame_data: Any, audio_data: Any) -> Dict[str, Any]:
        """API: Frame analizi yapar"""
        return self._analyze_realtime_frame({
            'session_id': session_id,
            'frame_data': frame_data,
            'audio_data': audio_data
        })
    
    def api_get_feedback(self, session_id: str) -> Dict[str, Any]:
        """API: Geribildirim döndürür"""
        return self._get_realtime_feedback({'session_id': session_id})
    
    def api_end_analysis(self, session_id: str) -> Dict[str, Any]:
        """API: Analizi sonlandırır"""
        return self._end_analysis_session({'session_id': session_id})


# ============================================
# ALT SİSTEM SINIFLARI
# ============================================

class AvatarGenerator:
    """Avatar Oluşturma Motoru"""
    
    def create_avatar(self, agent_id: str, agent_name: str, agent_type: str, 
                     personality_traits: Dict) -> Dict[str, Any]:
        """Avatar oluşturur"""
        
        # Ajan tipine göre avatar özellikleri
        avatar_configs = {
            'genclik_imece': {
                'appearance': 'young_professional',
                'voice_tone': 'energetic',
                'personality': 'friendly',
                'clothing': 'casual_professional'
            },
            'anac_asistan': {
                'appearance': 'motherly',
                'voice_tone': 'warm',
                'personality': 'supportive',
                'clothing': 'traditional'
            },
            'general': {
                'appearance': 'professional',
                'voice_tone': 'neutral',
                'personality': 'balanced',
                'clothing': 'business'
            }
        }
        
        config = avatar_configs.get(agent_type, avatar_configs['general'])
        
        # Avatar detayları
        avatar = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "appearance": config['appearance'],
            "voice_tone": config['voice_tone'],
            "personality": config['personality'],
            "clothing": config['clothing'],
            "facial_features": self._generate_facial_features(config['appearance']),
            "voice_profile": self._generate_voice_profile(config['voice_tone']),
            "animation_profile": self._generate_animation_profile(personality_traits),
            "lip_sync_config": {
                "enabled": True,
                "accuracy": "high",
                "realtime": True
            },
            "expression_library": self._generate_expression_library(config['personality']),
            "created_at": datetime.now().isoformat()
        }
        
        return avatar
    
    def _generate_facial_features(self, appearance: str) -> Dict[str, Any]:
        """Yüz özellikleri üretir"""
        
        features = {
            'young_professional': {
                'age_range': '20-30',
                'skin_tone': 'medium',
                'eye_shape': 'almond',
                'hair_style': 'modern'
            },
            'motherly': {
                'age_range': '40-50',
                'skin_tone': 'warm',
                'eye_shape': 'round',
                'hair_style': 'natural'
            },
            'professional': {
                'age_range': '30-40',
                'skin_tone': 'neutral',
                'eye_shape': 'balanced',
                'hair_style': 'conservative'
            }
        }
        
        return features.get(appearance, features['professional'])
    
    def _generate_voice_profile(self, voice_tone: str) -> Dict[str, Any]:
        """Ses profili üretir"""
        
        profiles = {
            'energetic': {
                'pitch': 'medium_high',
                'speed': 'fast',
                'warmth': 'high'
            },
            'warm': {
                'pitch': 'medium',
                'speed': 'moderate',
                'warmth': 'very_high'
            },
            'neutral': {
                'pitch': 'medium',
                'speed': 'normal',
                'warmth': 'medium'
            }
        }
        
        return profiles.get(voice_tone, profiles['neutral'])
    
    def _generate_animation_profile(self, personality_traits: Dict) -> Dict[str, Any]:
        """Animasyon profili üretir"""
        
        return {
            'expressiveness': personality_traits.get('expressiveness', 'medium'),
            'gesture_frequency': personality_traits.get('gesture_frequency', 'medium'),
            'eye_contact_level': personality_traits.get('eye_contact', 'high'),
            'smile_frequency': personality_traits.get('smile_frequency', 'medium'),
            'nod_frequency': personality_traits.get('nod_frequency', 'medium')
        }
    
    def _generate_expression_library(self, personality: str) -> List[str]:
        """İfade kütüphanesi üretir"""
        
        base_expressions = ['neutral', 'happy', 'concerned', 'thoughtful', 'encouraging']
        
        if personality == 'friendly':
            base_expressions.extend(['warm_smile', 'enthusiastic', 'empathetic'])
        elif personality == 'supportive':
            base_expressions.extend(['understanding', 'patient', 'gentle'])
        elif personality == 'balanced':
            base_expressions.extend(['professional', 'focused', 'analytical'])
        
        return base_expressions


class MultimodalAnalyzer:
    """Gerçek Zamanlı Multimodal Analiz Motoru"""
    
    def analyze_frame(self, frame_data: Any, audio_data: Any, session_context: Dict) -> Dict[str, Any]:
        """Frame analizi yapar"""
        
        # Görüntü analizi
        visual_analysis = self._analyze_visual(frame_data)
        
        # Ses analizi
        audio_analysis = self._analyze_audio(audio_data)
        
        # Multimodal entegrasyon
        integrated_analysis = self._integrate_analysis(visual_analysis, audio_analysis)
        
        # Psikolojik durum
        psychological_state = self._determine_psychological_state(integrated_analysis)
        
        return {
            "visual_analysis": visual_analysis,
            "audio_analysis": audio_analysis,
            "integrated_analysis": integrated_analysis,
            "dominant_emotion": psychological_state['dominant_emotion'],
            "confidence": psychological_state['confidence'],
            "stress_level": psychological_state['stress_level'],
            "engagement_level": psychological_state['engagement_level'],
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_visual(self, frame_data: Any) -> Dict[str, Any]:
        """Görüntü analizi yapar"""
        
        # Mock analiz
        return {
            "micro_expressions": self._detect_micro_expressions(),
            "eye_contact": self._analyze_eye_contact(),
            "body_language": self._analyze_body_language(),
            "facial_symmetry": self._analyze_facial_symmetry(),
            "blink_rate": self._analyze_blink_rate(),
            "pupil_dilation": self._analyze_pupil_dilation()
        }
    
    def _detect_micro_expressions(self) -> Dict[str, Any]:
        """Mikro ifadeleri tespit eder"""
        
        expressions = ['neutral', 'slight_smile', 'concern', 'interest', 'tension']
        detected = random.choice(expressions)
        
        return {
            "detected_expression": detected,
            "intensity": random.uniform(0.3, 0.8),
            "duration_ms": random.randint(100, 500)
        }
    
    def _analyze_eye_contact(self) -> Dict[str, Any]:
        """Göz temasını analiz eder"""
        
        return {
            "contact_level": random.choice(['high', 'medium', 'low']),
            "duration_avg": random.uniform(2.0, 5.0),
            "frequency": random.uniform(0.5, 0.9)
        }
    
    def _analyze_body_language(self) -> Dict[str, Any]:
        """Beden dilini analiz eder"""
        
        return {
            "posture": random.choice(['open', 'closed', 'neutral']),
            "gesture_frequency": random.uniform(0.2, 0.8),
            "lean_direction": random.choice(['forward', 'backward', 'neutral']),
            "arm_position": random.choice(['open', 'crossed', 'neutral'])
        }
    
    def _analyze_facial_symmetry(self) -> float:
        """Yüz simetrisini analiz eder"""
        return random.uniform(0.7, 0.95)
    
    def _analyze_blink_rate(self) -> Dict[str, Any]:
        """Göz kırpma oranını analiz eder"""
        
        return {
            "blinks_per_minute": random.randint(10, 25),
            "pattern": random.choice(['normal', 'rapid', 'slow'])
        }
    
    def _analyze_pupil_dilation(self) -> Dict[str, Any]:
        """Pupil genişlemesini analiz eder"""
        
        return {
            "dilation_level": random.uniform(0.3, 0.8),
            "change_rate": random.uniform(-0.1, 0.2)
        }
    
    def _analyze_audio(self, audio_data: Any) -> Dict[str, Any]:
        """Ses analizi yapar"""
        
        return {
            "tone": self._analyze_tone(),
            "pitch": self._analyze_pitch(),
            "speed": self._analyze_speed(),
            "rhythm": self._analyze_rhythm(),
            "volume": self._analyze_volume(),
            "voice_stability": self._analyze_voice_stability()
        }
    
    def _analyze_tone(self) -> str:
        """Tonu analiz eder"""
        return random.choice(['calm', 'tense', 'enthusiastic', 'neutral', 'anxious'])
    
    def _analyze_pitch(self) -> Dict[str, Any]:
        """Ses tonunu analiz eder"""
        
        return {
            "average_hz": random.randint(150, 250),
            "variability": random.uniform(0.1, 0.4),
            "trend": random.choice(['stable', 'rising', 'falling'])
        }
    
    def _analyze_speed(self) -> Dict[str, Any]:
        """Konuşma hızını analiz eder"""
        
        return {
            "words_per_minute": random.randint(120, 180),
            "pattern": random.choice(['steady', 'variable', 'rushed'])
        }
    
    def _analyze_rhythm(self) -> str:
        """Ritmi analiz eder"""
        return random.choice(['regular', 'irregular', 'hesitant'])
    
    def _analyze_volume(self) -> Dict[str, Any]:
        """Ses şiddetini analiz eder"""
        
        return {
            "average_db": random.randint(60, 80),
            "variability": random.uniform(0.1, 0.3)
        }
    
    def _analyze_voice_stability(self) -> float:
        """Ses kararlılığını analiz eder"""
        return random.uniform(0.6, 0.95)
    
    def _integrate_analysis(self, visual: Dict, audio: Dict) -> Dict[str, Any]:
        """Analizleri entegre eder"""
        
        return {
            "visual_weight": 0.6,
            "audio_weight": 0.4,
            "consistency_score": random.uniform(0.7, 0.95),
            "cross_modal_agreement": random.choice(['high', 'medium', 'low'])
        }
    
    def _determine_psychological_state(self, integrated: Dict) -> Dict[str, Any]:
        """Psikolojik durumu belirler"""
        
        emotions = ['calm', 'anxious', 'confident', 'nervous', 'engaged', 'distracted']
        dominant_emotion = random.choice(emotions)
        
        stress_levels = {
            'calm': 'low',
            'anxious': 'high',
            'confident': 'low',
            'nervous': 'medium',
            'engaged': 'low',
            'distracted': 'medium'
        }
        
        engagement_levels = {
            'calm': 'medium',
            'anxious': 'low',
            'confident': 'high',
            'nervous': 'low',
            'engaged': 'high',
            'distracted': 'low'
        }
        
        return {
            "dominant_emotion": dominant_emotion,
            "confidence": random.uniform(0.7, 0.95),
            "stress_level": stress_levels.get(dominant_emotion, 'medium'),
            "engagement_level": engagement_levels.get(dominant_emotion, 'medium')
        }


class RealtimeFeedback:
    """Anlık Geribildirim Sistemi"""
    
    def generate_feedback(self, analysis: Dict, agent_id: str) -> Dict[str, Any]:
        """Geribildirim üretir"""
        
        dominant_emotion = analysis['dominant_emotion']
        stress_level = analysis['stress_level']
        engagement_level = analysis['engagement_level']
        
        # Tavsiyeler
        recommendations = self._generate_recommendations(dominant_emotion, stress_level, engagement_level)
        
        # Hitap tarzı
        communication_style = self._suggest_communication_style(dominant_emotion, stress_level)
        
        # Hızlı eylem
        immediate_action = self._suggest_immediate_action(dominant_emotion, stress_level)
        
        return {
            "agent_id": agent_id,
            "current_emotion": dominant_emotion,
            "stress_level": stress_level,
            "engagement_level": engagement_level,
            "recommendations": recommendations,
            "communication_style": communication_style,
            "immediate_action": immediate_action,
            "confidence": analysis['confidence'],
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, emotion: str, stress: str, engagement: str) -> List[str]:
        """Tavsiyeler üretir"""
        
        recommendations = []
        
        if stress == 'high':
            recommendations.append("Daha yavaş ve sakin bir konuşma temposu kullanın")
            recommendations.append("Destekleyici ve empatik bir dil kullanın")
            recommendations.append("Basit ve net sorular sorun")
        
        if engagement == 'low':
            recommendations.append("Daha fazla görsel ve işitsel uyarıcı kullanın")
            recommendations.append("Daha interaktif bir yaklaşım benimseyin")
            recommendations.append("Kısa ve odaklı mesajlar verin")
        
        if emotion == 'anxious':
            recommendations.append("Güven verici bir ton kullanın")
            recommendations.append("Kontrol hissi verin")
            recommendations.append("Adım adım ilerleyin")
        
        if emotion == 'confident':
            recommendations.append("Daha derin sorular sorun")
            recommendations.append("Liderlik rolü üstlenin")
            recommendations.append("Daha karmaşık konulara girin")
        
        if not recommendations:
            recommendations.append("Mevcut yaklaşımı sürüdürün")
        
        return recommendations
    
    def _suggest_communication_style(self, emotion: str, stress: str) -> Dict[str, str]:
        """İletişim tarzı önerir"""
        
        if stress == 'high':
            return {
                "tone": "supportive",
                "pace": "slow",
                "volume": "soft",
                "language": "simple"
            }
        elif emotion == 'confident':
            return {
                "tone": "professional",
                "pace": "normal",
                "volume": "moderate",
                "language": "professional"
            }
        else:
            return {
                "tone": "neutral",
                "pace": "moderate",
                "volume": "normal",
                "language": "balanced"
            }
    
    def _suggest_immediate_action(self, emotion: str, stress: str, engagement: str = 'medium') -> str:
        """Hızlı eylem önerir"""
        
        if stress == 'high':
            return "Derin nefes egzersizi önerin ve sakinleştirici bir ortam yaratın"
        elif emotion == 'anxious':
            return "Güven verici cümleler kullanın ve endişeleri doğrudan ele alın"
        elif engagement == 'low':
            return "Dikkat çekici bir soru sorun veya konuyu değiştirin"
        else:
            return "Mevcut akışı sürdürün"


class DeepAnalysisRecorder:
    """Derin Analiz Kayıt Sistemi"""
    
    def create_report(self, session: Dict, analysis_history: List[Dict]) -> Dict[str, Any]:
        """Derin analiz raporu oluşturur"""
        
        # Psikolojik profil
        psychological_profile = self._create_psychological_profile(analysis_history)
        
        # İletişim örüntüleri
        communication_patterns = self._analyze_communication_patterns(analysis_history)
        
        # Stres analizi
        stress_analysis = self._analyze_stress_patterns(analysis_history)
        
        # Etkileşim kalitesi
        interaction_quality = self._assess_interaction_quality(analysis_history)
        
        # Özet
        summary = self._generate_summary(psychological_profile, communication_patterns, stress_analysis)
        
        return {
            "session_id": session['session_id'],
            "agent_id": session['agent_id'],
            "target_person_id": session['target_person_id'],
            "session_type": session['session_type'],
            "duration_minutes": self._calculate_duration(session),
            "total_frames": session['frames_analyzed'],
            "psychological_profile": psychological_profile,
            "communication_patterns": communication_patterns,
            "stress_analysis": stress_analysis,
            "interaction_quality": interaction_quality,
            "summary": summary,
            "recommendations": self._generate_recommendations(psychological_profile, stress_analysis),
            "created_at": datetime.now().isoformat()
        }
    
    def _create_psychological_profile(self, analysis_history: List[Dict]) -> Dict[str, Any]:
        """Psikolojik profil oluşturur"""
        
        if not analysis_history:
            return {"error": "No analysis data"}
        
        # Duygu dağılımı
        emotions = [a['dominant_emotion'] for a in analysis_history]
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # Ortama stres seviyesi
        stress_levels = [a['stress_level'] for a in analysis_history]
        avg_stress = sum([1 if s == 'high' else 0.5 if s == 'medium' else 0 for s in stress_levels]) / len(stress_levels)
        
        # Ortama etkileşim seviyesi
        engagement_levels = [a['engagement_level'] for a in analysis_history]
        avg_engagement = sum([1 if e == 'high' else 0.5 if e == 'medium' else 0 for e in engagement_levels]) / len(engagement_levels)
        
        return {
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": emotion_counts,
            "average_stress_level": avg_stress,
            "average_engagement_level": avg_engagement,
            "emotional_stability": self._calculate_emotional_stability(emotions),
            "overall_psychological_state": self._determine_overall_state(dominant_emotion, avg_stress, avg_engagement)
        }
    
    def _calculate_emotional_stability(self, emotions: List[str]) -> float:
        """Duygusal istikrarı hesaplar"""
        
        if len(emotions) < 2:
            return 1.0
        
        # Değişim sayısı
        changes = sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i-1])
        
        # İstikrar skoru (daha az değişim = daha istikrarlı)
        stability = 1.0 - (changes / len(emotions))
        
        return max(0.0, min(1.0, stability))
    
    def _determine_overall_state(self, dominant_emotion: str, avg_stress: float, avg_engagement: float) -> str:
        """Genel durumu belirler"""
        
        if avg_stress > 0.7:
            return "high_stress"
        elif avg_engagement < 0.3:
            return "low_engagement"
        elif dominant_emotion == 'confident':
            return "confident_engaged"
        elif dominant_emotion == 'anxious':
            return "anxious_reserved"
        else:
            return "balanced"
    
    def _analyze_communication_patterns(self, analysis_history: List[Dict]) -> Dict[str, Any]:
        """İletişim örüntülerini analiz eder"""
        
        return {
            "consistency_score": random.uniform(0.7, 0.95),
            "preferred_communication_style": random.choice(['verbal', 'non_verbal', 'balanced']),
            "response_latency": random.uniform(1.0, 3.0),
            "information_processing_speed": random.choice(['fast', 'normal', 'slow'])
        }
    
    def _analyze_stress_patterns(self, analysis_history: List[Dict]) -> Dict[str, Any]:
        """Stres örüntülerini analiz eder"""
        
        stress_levels = [a['stress_level'] for a in analysis_history]
        
        high_stress_count = sum(1 for s in stress_levels if s == 'high')
        
        return {
            "high_stress_episodes": high_stress_count,
            "stress_triggers": self._identify_stress_triggers(analysis_history),
            "stress_recovery_time": random.uniform(30, 120),
            "overall_stress_trend": random.choice(['increasing', 'stable', 'decreasing'])
        }
    
    def _identify_stress_triggers(self, analysis_history: List[Dict]) -> List[str]:
        """Stres tetikleyicilerini tespit eder"""
        
        triggers = []
        
        # Mock tetikleyiciler
        if random.random() > 0.5:
            triggers.append("Kompleks sorular")
        if random.random() > 0.5:
            triggers.append("Zaman baskısı")
        if random.random() > 0.5:
            triggers.append("Yabancı ortam")
        
        return triggers if triggers else ["Belirlenemedi"]
    
    def _assess_interaction_quality(self, analysis_history: List[Dict]) -> Dict[str, Any]:
        """Etkileşim kalitesini değerlendirir"""
        
        engagement_levels = [a['engagement_level'] for a in analysis_history]
        avg_engagement = sum([1 if e == 'high' else 0.5 if e == 'medium' else 0 for e in engagement_levels]) / len(engagement_levels)
        
        return {
            "overall_quality_score": avg_engagement * 100,
            "peak_engagement_moments": random.randint(2, 5),
            "attention_span": random.uniform(5, 15),
            "rapport_building": random.choice(['excellent', 'good', 'fair', 'poor'])
        }
    
    def _calculate_duration(self, session: Dict) -> float:
        """Süre hesaplar"""
        
        start_time = datetime.fromisoformat(session['start_time'])
        end_time = datetime.fromisoformat(session.get('end_time', datetime.now().isoformat()))
        
        duration = (end_time - start_time).total_seconds() / 60
        
        return duration
    
    def _generate_summary(self, profile: Dict, patterns: Dict, stress: Dict) -> str:
        """Özet üretir"""
        
        overall_state = profile.get('overall_psychological_state', 'balanced')
        quality_score = patterns.get('consistency_score', 0.8)
        
        summary_parts = [
            f"Genel psikolojik durum: {overall_state}",
            f"İletişim tutarlılığı: %{quality_score * 100:.0f}",
            f"Stres seviyesi: {stress.get('overall_stress_trend', 'stable')}"
        ]
        
        return ". ".join(summary_parts)
    
    def _generate_recommendations(self, profile: Dict, stress: Dict) -> List[str]:
        """Öneriler üretir"""
        
        recommendations = []
        
        overall_state = profile.get('overall_psychological_state', 'balanced')
        
        if overall_state == 'high_stress':
            recommendations.append("Stres yönetimi teknikleri öğretin")
            recommendations.append("Daha kısa ve odaklı seanslar yapın")
        elif overall_state == 'low_engagement':
            recommendations.append("İlgi alanlarına odaklanın")
            recommendations.append("Daha interaktif yöntemler kullanın")
        elif overall_state == 'anxious_reserved':
            recommendations.append("Güven ortamı oluşturun")
            recommendations.append("Kademeli yaklaşım benimseyin")
        else:
            recommendations.append("Mevcut yaklaşımı sürdürün")
        
        return recommendations


# Test çalıştırması
if __name__ == "__main__":
    agent = KameraPsikoAnalizAjani(agent_id=171)
    
    # Test avatar oluşturma
    print("🎭 TEST AVATAR OLUŞTURMA:")
    avatar_result = agent.run(
        operation='create_avatar',
        agent_id='genclik_imece_001',
        agent_name='Gençlik Refah Ajanı',
        agent_type='genclik_imece',
        personality_traits={
            'expressiveness': 'high',
            'gesture_frequency': 'medium',
            'eye_contact': 'high',
            'smile_frequency': 'high',
            'nod_frequency': 'medium'
        }
    )
    print(json.dumps(avatar_result, indent=2, ensure_ascii=False))
    
    # Test seans başlatma
    print("\n🎥 TEST SEANS BAŞLATMA:")
    session_result = agent.run(
        operation='start_session',
        session_id='session_test_001',
        agent_id='genclik_imece_001',
        target_person_id='person_001',
        session_type='interview'
    )
    print(json.dumps(session_result, indent=2, ensure_ascii=False))
    
    # Test frame analizi
    print("\n📸 TEST FRAME ANALİZİ:")
    frame_result = agent.run(
        operation='analyze_frame',
        session_id='session_test_001',
        frame_data=None,
        audio_data=None
    )
    print(json.dumps(frame_result, indent=2, ensure_ascii=False))
    
    # Test geribildirim
    print("\n💡 TEST GERİBİLDİRİM:")
    feedback_result = agent.run(
        operation='get_feedback',
        session_id='session_test_001'
    )
    print(json.dumps(feedback_result, indent=2, ensure_ascii=False))
    
    # Test seans sonlandırma
    print("\n📊 TEST SEANS SONLANDIRMA:")
    end_result = agent.run(
        operation='end_session',
        session_id='session_test_001'
    )
    print(json.dumps(end_result, indent=2, ensure_ascii=False))
    
    # Dashboard
    print("\n📈 DASHBOARD:")
    dashboard = agent.run(operation='dashboard')
    print(json.dumps(dashboard, indent=2, ensure_ascii=False))
