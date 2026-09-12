#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard.py - FastAPI Tabanlı Agent Dashboard
8 ajanın (Elif, Amara, Lucia, Sophie, Emma, Yuki, Alina, Camille) anlık durumlarını,
son loglarını ve görevlerini modern bir grid ekranda canlı olarak gösterir.
"""

import os
import json
import asyncio
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Config yükleme
CONFIG_FILE = "agent_config.json"
LOG_DIR = Path("logs")
INTER_AGENT_BUS_FILE = LOG_DIR / "inter_agent_bus.jsonl"

# FastAPI uygulaması
app = FastAPI(
    title="Agent Dashboard",
    description="Multi-Agent System Dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket bağlantı yöneticisi
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Agent durumları ve süreçleri
agent_processes = {}
agent_states = {
    "elif": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "amara": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "lucia": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "sophie": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "emma": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "yuki": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "alina": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"},
    "camille": {"status": "idle", "task": "Waiting for start", "last_log": "No logs yet"}
}

def load_config() -> dict:
    """agent_config.json dosyasını okur"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"agents": [], "grid_layout": {}}

def read_agent_logs(agent_id: str, limit: int = 10) -> List[dict]:
    """Ajan loglarını okur"""
    log_file = LOG_DIR / f"{agent_id}_agent.log"
    
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logs = []
        for line in lines[-limit:]:
            if line.strip():
                logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": line.strip()
                })
        
        return logs
    except Exception:
        return []

def read_inter_agent_bus(limit: int = 20) -> List[dict]:
    """Inter-agent bus loglarını okur"""
    if not INTER_AGENT_BUS_FILE.exists():
        return []
    
    try:
        with open(INTER_AGENT_BUS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        messages = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    message = json.loads(line)
                    messages.append(message)
                except json.JSONDecodeError:
                    pass
        
        return messages
    except Exception:
        return []

def check_agent_process_status(agent_id: str) -> str:
    """Ajan sürecinin durumunu kontrol eder"""
    if agent_id not in agent_processes:
        return "idle"
    
    process = agent_processes[agent_id]
    if process is None:
        return "idle"
    
    try:
        # Sürecin hala çalışıp çalışmadığını kontrol et
        if process.poll() is None:
            # Süreç çalışıyor, CPU kullanımına göre busy/active belirle
            try:
                cpu_percent = process.cpu_percent(interval=0.1)
                if cpu_percent > 50:
                    return "busy"
                else:
                    return "active"
            except:
                return "active"
        else:
            # Süreç sonlandı
            agent_processes[agent_id] = None
            return "idle"
    except:
        return "idle"

def monitor_agent_processes():
    """Ajan süreçlerini izler ve durumları günceller"""
    for agent_id in agent_states:
        status = check_agent_process_status(agent_id)
        
        if agent_states[agent_id]["status"] != status:
            agent_states[agent_id]["status"] = status
            
            # Log dosyasını oku
            log_file = LOG_DIR / f"{agent_id}_agent.log"
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    if lines:
                        agent_states[agent_id]["last_log"] = lines[-1].strip()[:100]
                except:
                    pass

# API Endpoint'leri

@app.get("/")
async def get_dashboard():
    """Dashboard ana sayfasını döndürür (static/index.html)"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Dashboard not found. Please create static/index.html</h1>")

@app.get("/api/agents")
async def get_agents():
    """Tüm ajanları döndürür"""
    config = load_config()
    return JSONResponse(config.get("agents", []))

@app.get("/api/agents/states")
async def get_agent_states():
    """Tüm ajan durumlarını döndürür"""
    return JSONResponse(agent_states)

@app.get("/api/agents/{agent_id}/state")
async def get_agent_state(agent_id: str):
    """Tekil ajan durumunu döndürür"""
    if agent_id not in agent_states:
        raise HTTPException(status_code=404, detail="Agent not found")
    return JSONResponse(agent_states[agent_id])

@app.get("/api/agents/{agent_id}/logs")
async def get_agent_logs(agent_id: str, limit: int = 10):
    """Ajan loglarını döndürür"""
    logs = read_agent_logs(agent_id, limit)
    return JSONResponse(logs)

@app.get("/api/bus/messages")
async def get_bus_messages(limit: int = 20):
    """Inter-agent bus mesajlarını döndürür"""
    messages = read_inter_agent_bus(limit)
    return JSONResponse(messages)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or process data
            await manager.broadcast({"type": "echo", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/agents/{agent_id}/state")
async def update_agent_state(agent_id: str, state: dict):
    """Ajan durumunu günceller"""
    if agent_id not in agent_states:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_states[agent_id].update(state)
    
    # Broadcast update via WebSocket
    await manager.broadcast({
        "type": "agent_state",
        "agent_id": agent_id,
        **agent_states[agent_id]
    })
    
    return JSONResponse({"status": "success", "agent_id": agent_id})

@app.post("/api/bus/message")
async def send_bus_message(message: dict):
    """Inter-agent bus'a mesaj gönderir"""
    message["timestamp"] = datetime.now().isoformat()
    
    # Write to file
    INTER_AGENT_BUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INTER_AGENT_BUS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")
    
    # Broadcast via WebSocket
    await manager.broadcast({
        "type": "bus_message",
        **message
    })
    
    return JSONResponse({"status": "success"})

@app.post("/api/agents/start")
async def start_all_agents():
    """Tüm ajanları başlatır (gerçek süreçler)"""
    try:
        config = load_config()
        agents = config.get("agents", [])
        
        for agent in agents:
            agent_id = agent["id"]
            command = agent.get("command", f"python {agent.get('module', '')}")
            
            try:
                # Ajan sürecini başlat
                process = subprocess.Popen(
                    command.split(),
                    cwd=os.getcwd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                agent_processes[agent_id] = process
                agent_states[agent_id]["status"] = "active"
                agent_states[agent_id]["task"] = "Starting up..."
                
                # Broadcast update
                await manager.broadcast({
                    "type": "agent_state",
                    "agent_id": agent_id,
                    **agent_states[agent_id]
                })
                
                print(f"✅ [Dashboard] Agent {agent_id} started (PID: {process.pid})")
            except Exception as e:
                print(f"❌ [Dashboard] Failed to start agent {agent_id}: {e}")
                agent_states[agent_id]["status"] = "idle"
                agent_states[agent_id]["task"] = "Failed to start"
        
        return JSONResponse({
            "success": True,
            "message": "All agents started successfully"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Error starting agents: {str(e)}"
        }, status_code=500)

@app.post("/api/agents/stop")
async def stop_all_agents():
    """Tüm ajanları durdurur (gerçek süreçleri sonlandırır)"""
    try:
        # Tüm ajan süreçlerini sonlandır
        for agent_id in agent_processes:
            process = agent_processes[agent_id]
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✅ [Dashboard] Agent {agent_id} stopped")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"⚠️ [Dashboard] Agent {agent_id} force killed")
                except:
                    pass
                
                agent_processes[agent_id] = None
        
        # Tüm ajan durumlarını idle yap
        for agent_id in agent_states:
            agent_states[agent_id]["status"] = "idle"
            agent_states[agent_id]["task"] = "Stopped"
            
            # Broadcast update
            await manager.broadcast({
                "type": "agent_state",
                "agent_id": agent_id,
                **agent_states[agent_id]
            })
        
        # Bus'a durdurma mesajı gönder
        stop_message = {
            "source": "dashboard",
            "target": "all",
            "type": "system",
            "message": "System stop command received"
        }
        await send_bus_message(stop_message)
        
        return JSONResponse({
            "success": True,
            "message": "All agents stopped successfully"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Error stopping agents: {str(e)}"
        }, status_code=500)

@app.post("/api/affiliate/trigger")
async def trigger_affiliate_task():
    """Affiliate görevini tetikler (orchestrator üzerinden)"""
    try:
        # Affiliate görev mesajı gönder
        affiliate_message = {
            "source": "dashboard",
            "target": "emma",  # Financial agent
            "type": "affiliate_task",
            "message": "Affiliate yield harmonization task triggered"
        }
        await send_bus_message(affiliate_message)
        
        # Emma ajanını busy yap
        if "emma" in agent_states:
            agent_states["emma"]["status"] = "busy"
            agent_states["emma"]["task"] = "Processing affiliate yield harmonization"
            
            # Broadcast update
            await manager.broadcast({
                "type": "agent_state",
                "agent_id": "emma",
                **agent_states["emma"]
            })
        
        return JSONResponse({
            "success": True,
            "message": "Affiliate task triggered successfully"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Error triggering affiliate task: {str(e)}"
        }, status_code=500)

# Background task for monitoring real agent processes
async def monitor_real_agent_processes():
    """Gerçek ajan süreçlerini izler ve WebSocket'e günceller"""
    while True:
        try:
            monitor_agent_processes()
            
            # Durum değişikliklerini broadcast et
            for agent_id in agent_states:
                await manager.broadcast({
                    "type": "agent_state",
                    "agent_id": agent_id,
                    **agent_states[agent_id]
                })
        except Exception as e:
            print(f"❌ [Monitor] Error monitoring processes: {e}")
        
        await asyncio.sleep(2)  # 2 saniyede bir kontrol

# Background task for monitoring inter-agent bus
async def monitor_inter_agent_bus():
    """Inter-agent bus dosyasını izler ve yeni mesajları WebSocket'e gönderir"""
    last_position = 0
    
    while True:
        try:
            if INTER_AGENT_BUS_FILE.exists():
                with open(INTER_AGENT_BUS_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                
                for line in new_lines:
                    if line.strip():
                        try:
                            message = json.loads(line)
                            await manager.broadcast({
                                "type": "bus_message",
                                **message
                            })
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"❌ [Bus Monitor] Error: {e}")
        
        await asyncio.sleep(1)  # 1 saniyede bir kontrol

# Background task for monitoring agent log files
async def monitor_agent_logs():
    """Ajan log dosyalarını izler ve yeni logları WebSocket'e gönderir"""
    log_positions = {}
    
    while True:
        try:
            for agent_id in agent_states:
                log_file = LOG_DIR / f"{agent_id}_agent.log"
                
                if log_file.exists():
                    if agent_id not in log_positions:
                        log_positions[agent_id] = 0
                    
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(log_positions[agent_id])
                            new_lines = f.readlines()
                            log_positions[agent_id] = f.tell()
                        
                        if new_lines:
                            # Son log'u güncelle
                            agent_states[agent_id]["last_log"] = new_lines[-1].strip()[:100]
                            
                            # Broadcast update
                            await manager.broadcast({
                                "type": "agent_log",
                                "agent_id": agent_id,
                                "log": new_lines[-1].strip()
                            })
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"❌ [Log Monitor] Error: {e}")
        
        await asyncio.sleep(1)  # 1 saniyede bir kontrol

@app.on_event("startup")
async def startup_event():
    """Başlangıçta background task'ları başlatır"""
    asyncio.create_task(monitor_real_agent_processes())
    asyncio.create_task(monitor_inter_agent_bus())
    asyncio.create_task(monitor_agent_logs())

if __name__ == "__main__":
    uvicorn.run(
        "dashboard:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
