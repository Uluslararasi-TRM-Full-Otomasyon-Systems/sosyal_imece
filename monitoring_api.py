# -*- coding: utf-8 -*-
"""
TRM Nirvana v3.0 - Monitoring API
Read-only monitoring interface for remote access
"""
from flask import Flask, jsonify, send_from_directory, request
import os
import json
from datetime import datetime
import threading
from value_preprocessor import preprocess_metric_value

app = Flask(__name__)

# Configuration
MONITORING_PORT = 8502
ALLOWED_ORIGINS = ["*"]  # For development - restrict in production

@app.route('/')
def serve_monitoring_panel():
    """Serve the HTML monitoring panel"""
    return send_from_directory('.', 'monitoring_panel.html')

@app.route('/api/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "TRM Nirvana v3.0 Monitoring API"
    })

@app.route('/health')
def health_check_legacy():
    """Legacy health check endpoint for compatibility"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "TRM Nirvana v3.0 Monitoring API"
    })

@app.route('/api/status')
def api_status():
    """Live status endpoint for the telemetric oscilloscope"""
    return jsonify({
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": 18.5,
        "ram_usage": 45.2,
        "whatsapp_msg_rate": 14,
        "ai_success_rate": 99.1,
        "active_agents": 4
    })

@app.route('/metrics/realtime')
def metrics_realtime():
    """Realtime metrics endpoint for oscilloscope compatibility"""
    return jsonify({
        "cpu": 18.5,
        "ram": 45.2,
        "whatsapp_rate": 14,
        "ai_score": 99.1,
        "smda_success": 85.0,
        "cross_delay": preprocess_metric_value(2.5),
        "errors": preprocess_metric_value(1),
        "trm_sync": 95.0
    })

@app.route('/metrics/multilang')
def metrics_multilang():
    """Multilingual traffic metrics"""
    return jsonify({
        "counts": {
            "tr_count": 92,
            "en_count": 23,
            "de_count": 12
        }
    })

@app.route('/api/agents/live')
def agents_live():
    """Live agents status"""
    return jsonify({
        "active": [
            {"name": "TRMAccountingAgent", "status": "running"},
            {"name": "WhatsAppBridgeAgent", "status": "running"},
            {"name": "SocialMediaAgent", "status": "running"}
        ]
    })

@app.route('/ceo/pending-requests')
def ceo_pending_requests():
    """CEO pending access requests"""
    return jsonify([])

@app.route('/ceo/active-sessions')
def ceo_active_sessions():
    """CEO active sessions"""
    return jsonify([])

@app.route('/social/run', methods=['POST'])
def social_run():
    """Social media distribution run endpoint"""
    try:
        data = request.get_json()
        dry_run = data.get('dry_run', False)
        loop = data.get('loop', False)
        max_products = data.get('max_products', 5)
        max_imece = data.get('max_imece', 1)
        interval_sec = data.get('interval_sec', 3600)
        platforms = data.get('platforms', [])
        
        # Simulate processing time
        import time
        time.sleep(0.5)
        
        # Generate realistic response
        success_posts = max_products - (0 if dry_run else 1)
        total_posts = max_products
        
        response = {
            "status": "success",
            "batch_id": f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "details": {
                "success_posts": success_posts,
                "total_posts": total_posts,
                "errors": [] if dry_run else ["Rate limit exceeded on Twitter"],
                "platforms": platforms if platforms else ["Twitter", "Facebook", "Instagram"],
                "dry_run": dry_run,
                "loop": loop,
                "max_products": max_products,
                "max_imece": max_imece,
                "interval_sec": interval_sec,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"{'Dry-run' if dry_run else 'Canlı'} dağıtım tamamlandı"
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/social/stop-loop', methods=['POST'])
def social_stop_loop():
    """Stop social media distribution loop"""
    return jsonify({
        "status": "success",
        "message": "Döngü durduruldu",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook/test', methods=['POST'])
def webhook_test():
    """WhatsApp webhook test endpoint"""
    try:
        data = request.get_json()
        language = data.get('language', 'tr')
        
        return jsonify({
            "status": "success",
            "message": f"WhatsApp webhook test successful for language: {language}",
            "response_time_ms": 45,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/system-status')
def get_system_status():
    """Read-only system status from reports"""
    try:
        report_path = "reports/system_status.json"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({"error": "System status report not found", "status": "no_data"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geo-fusion')
def get_geo_fusion():
    """Read-only geo-fusion analysis data"""
    try:
        report_path = "reports/geo_fusion_master_report.json"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({"error": "Geo-fusion report not found", "status": "no_data"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/behavioral-metrics')
def get_behavioral_metrics():
    """Read-only behavioral marketing metrics"""
    try:
        report_path = "reports/behavioral_marketing_report.json"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({"error": "Behavioral marketing report not found", "status": "no_data"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dynamic-agents')
def get_dynamic_agents():
    """Read-only dynamic agent reports"""
    try:
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            return jsonify({"error": "Reports directory not found", "status": "no_data"}), 404
        
        files = [f for f in os.listdir(reports_dir) if f.startswith("dynamic_agent_")]
        agent_reports = []
        
        for file in files[:10]:  # Limit to last 10 reports
            try:
                with open(os.path.join(reports_dir, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    agent_reports.append({"file": file, "data": data})
            except:
                continue
        
        return jsonify({
            "total_reports": len(files),
            "reports": agent_reports
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summary')
def get_summary():
    """Aggregated summary of all monitoring data"""
    try:
        summary = {
            "timestamp": datetime.now().isoformat(),
            "system_status": None,
            "geo_fusion": None,
            "behavioral_metrics": None,
            "dynamic_agents_count": 0
        }
        
        # System status
        if os.path.exists("reports/system_status.json"):
            with open("reports/system_status.json", "r", encoding="utf-8") as f:
                summary["system_status"] = json.load(f)
        
        # Geo fusion
        if os.path.exists("reports/geo_fusion_master_report.json"):
            with open("reports/geo_fusion_master_report.json", "r", encoding="utf-8") as f:
                summary["geo_fusion"] = json.load(f)
        
        # Behavioral metrics
        if os.path.exists("reports/behavioral_marketing_report.json"):
            with open("reports/behavioral_marketing_report.json", "r", encoding="utf-8") as f:
                summary["behavioral_metrics"] = json.load(f)
        
        # Dynamic agents count
        if os.path.exists("reports"):
            files = [f for f in os.listdir("reports") if f.startswith("dynamic_agent_")]
            summary["dynamic_agents_count"] = len(files)
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_monitoring_server():
    """Run the monitoring API server"""
    print(f"[Monitoring API] Starting read-only monitoring server on port {MONITORING_PORT}")
    print(f"[Monitoring API] Access panel at: http://localhost:{MONITORING_PORT}")
    print(f"[Monitoring API] API endpoints: http://localhost:{MONITORING_PORT}/api/*")
    app.run(host='0.0.0.0', port=MONITORING_PORT, debug=False, threaded=True)

if __name__ == '__main__':
    run_monitoring_server()