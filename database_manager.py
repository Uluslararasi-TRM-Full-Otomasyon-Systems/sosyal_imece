#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Database Manager
TRM ticari ekosistemi için veritabanı yönetimi
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Agents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT,
                    web TEXT,
                    status TEXT DEFAULT 'inactive',
                    last_heartbeat TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # System logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    message TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # System metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User behavior analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_behavior_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    product_id TEXT,
                    category TEXT,
                    click_count INTEGER DEFAULT 0,
                    dwell_time_seconds INTEGER DEFAULT 0,
                    region TEXT DEFAULT 'yurtici',
                    inferred_persona TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_behavior_session_id ON user_behavior_analytics(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_behavior_timestamp ON user_behavior_analytics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_behavior_persona ON user_behavior_analytics(inferred_persona)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_behavior_product ON user_behavior_analytics(product_id)')
            
            print("[Database] SQLite database initialized successfully")
    
    def migrate_agents_from_json(self, json_path):
        """Migrate agents from JSON file to SQLite"""
        try:
            json_file = Path(json_path)
            if not json_file.exists():
                print(f"[Database] JSON file not found: {json_path}")
                return False
            
            with open(json_file, 'r', encoding='utf-8') as f:
                agents_data = json.load(f)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear existing agents
                cursor.execute('DELETE FROM agents')
                
                # Insert agents from JSON
                agents_list = agents_data.get('agents', [])
                for agent in agents_list:
                    cursor.execute('''
                        INSERT OR REPLACE INTO agents (id, name, role, web, status, last_heartbeat)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        agent.get('id'),
                        agent.get('name'),
                        agent.get('role'),
                        agent.get('web'),
                        agent.get('status', 'inactive'),
                        agent.get('last_heartbeat')
                    ))
                
                print(f"[Database] Migrated {len(agents_list)} agents from JSON to SQLite")
                return True
                
        except Exception as e:
            print(f"[Database] Migration error: {e}")
            return False
    
    def get_all_agents(self):
        """Get all agents from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agents ORDER BY id')
            agents = cursor.fetchall()
            return [dict(agent) for agent in agents]
    
    def get_agent_by_id(self, agent_id):
        """Get agent by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
            agent = cursor.fetchone()
            return dict(agent) if agent else None
    
    def get_active_agents_count(self):
        """Get count of active agents"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM agents WHERE status = ?', ('active',))
            return cursor.fetchone()[0]
    
    def get_total_agents_count(self):
        """Get total count of agents"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM agents')
            return cursor.fetchone()[0]
    
    def update_agent_status(self, agent_id, status):
        """Update agent status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agents 
                SET status = ?, last_heartbeat = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, datetime.now().isoformat(), agent_id))
            return cursor.rowcount > 0
    
    def insert_agent(self, agent_data):
        """Insert new agent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO agents (id, name, role, web, status, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                agent_data.get('id'),
                agent_data.get('name'),
                agent_data.get('role'),
                agent_data.get('web'),
                agent_data.get('status', 'inactive'),
                agent_data.get('last_heartbeat', datetime.now().isoformat())
            ))
            return cursor.rowcount > 0
    
    def log_system_event(self, level, message):
        """Log system event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (level, message, timestamp)
                VALUES (?, ?, ?)
            ''', (level, message, datetime.now().isoformat()))
    
    def get_recent_logs(self, limit=50):
        """Get recent logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM system_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            logs = cursor.fetchall()
            return [dict(log) for log in logs]
    
    def save_config(self, key, value):
        """Save configuration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, json.dumps(value), datetime.now().isoformat()))
    
    def get_config(self, key):
        """Get configuration"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
    
    def get_agents_dict(self):
        """Get agents in dictionary format (compatible with existing code)"""
        agents = self.get_all_agents()
        return {
            "total_agents": len(agents),
            "agents": agents
        }
    
    def set_max_agents(self, count):
        """Set maximum agents configuration"""
        config = self.get_config('system') or {}
        config['max_ajan_sayisi'] = count
        self.save_config('system', config)
    
    def get_max_agents(self):
        """Get maximum agents configuration"""
        config = self.get_config('system') or {}
        return config.get('max_ajan_sayisi', 200)
    
    def insert_behavior_data(self, behavior_data):
        """Insert user behavior analytics record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_behavior_analytics 
                (session_id, product_id, category, click_count, dwell_time_seconds, region, inferred_persona, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                behavior_data.get('session_id'),
                behavior_data.get('product_id'),
                behavior_data.get('category'),
                behavior_data.get('click_count', 0),
                behavior_data.get('dwell_time_seconds', 0),
                behavior_data.get('region', 'yurtici'),
                behavior_data.get('inferred_persona'),
                behavior_data.get('timestamp', datetime.now().isoformat())
            ))
            return cursor.lastrowid
    
    def update_behavior_data(self, record_id, behavior_data):
        """Update user behavior analytics record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_behavior_analytics 
                SET click_count = ?, dwell_time_seconds = ?, inferred_persona = ?, timestamp = ?
                WHERE id = ?
            ''', (
                behavior_data.get('click_count', 0),
                behavior_data.get('dwell_time_seconds', 0),
                behavior_data.get('inferred_persona'),
                datetime.now().isoformat(),
                record_id
            ))
            return cursor.rowcount > 0
    
    def get_behavior_by_session(self, session_id):
        """Get all behavior records for a session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_behavior_analytics 
                WHERE session_id = ? 
                ORDER BY timestamp DESC
            ''', (session_id,))
            records = cursor.fetchall()
            return [dict(r) for r in records]
    
    def get_behavior_by_product(self, product_id):
        """Get all behavior records for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_behavior_analytics 
                WHERE product_id = ? 
                ORDER BY timestamp DESC
            ''', (product_id,))
            records = cursor.fetchall()
            return [dict(r) for r in records]
    
    def get_all_behavior_data(self, limit=100, offset=0):
        """Get all behavior data with pagination"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_behavior_analytics 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            records = cursor.fetchall()
            return [dict(r) for r in records]
    
    def get_behavior_persona_distribution(self):
        """Get persona distribution statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT inferred_persona, COUNT(*) as count,
                       AVG(click_count) as avg_clicks,
                       AVG(dwell_time_seconds) as avg_dwell_time
                FROM user_behavior_analytics
                WHERE inferred_persona IS NOT NULL
                GROUP BY inferred_persona
                ORDER BY count DESC
            ''')
            records = cursor.fetchall()
            return [dict(r) for r in records]
    
    def get_behavior_summary_stats(self):
        """Get overall behavior summary statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(DISTINCT product_id) as unique_products,
                    SUM(click_count) as total_clicks,
                    AVG(dwell_time_seconds) as avg_dwell_time,
                    SUM(CASE WHEN region = 'yurtici' THEN 1 ELSE 0 END) as yurtici_count,
                    SUM(CASE WHEN region = 'yurtdisi' THEN 1 ELSE 0 END) as yurtdisi_count
                FROM user_behavior_analytics
            ''')
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_recent_behavior_with_personas(self, limit=50):
        """Get recent behavior records with inferred personas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, session_id, product_id, category, click_count, 
                       dwell_time_seconds, region, inferred_persona, timestamp
                FROM user_behavior_analytics
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            records = cursor.fetchall()
            return [dict(r) for r in records]
    
    def delete_behavior_by_session(self, session_id):
        """Delete all behavior records for a session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_behavior_analytics WHERE session_id = ?', (session_id,))
            return cursor.rowcount

# Test usage
if __name__ == "__main__":
    db = DatabaseManager()
    print("[Database] Database manager test completed")
