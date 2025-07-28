#!/usr/bin/env python3
"""
Log Storage Module
Handles encrypted logs, snapshots, and metadata storage
"""

import json
import time
import hashlib
import hmac
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import threading
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class LogStorage:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.encryption_key = config.get('encryption_key', 'your-secret-key-here')
        self.incidents_path = Path(config.get('incidents_path', 'data/incidents'))
        self.logs_path = Path(config.get('logs_path', 'data/logs'))
        
        # Create directories
        self.incidents_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.fernet = self.initialize_encryption()
        
        # Initialize database
        self.db_path = self.logs_path / 'security_logs.db'
        self.initialize_database()
        
        # Threading
        self.log_queue = []
        self.log_lock = threading.Lock()
        
        print("Log storage module initialized")
    
    def initialize_encryption(self) -> Optional[Fernet]:
        """Initialize encryption with the provided key"""
        try:
            # Generate a key from the password
            salt = b'security_salt_123'  # In production, use a random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            return Fernet(key)
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            return None
    
    def initialize_database(self):
        """Initialize SQLite database for logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create incidents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    type TEXT,
                    confidence REAL,
                    module TEXT,
                    details TEXT,
                    encrypted_data TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    level TEXT,
                    module TEXT,
                    message TEXT,
                    encrypted_data TEXT
                )
            ''')
            
            # Create snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    timestamp REAL,
                    incident_id TEXT,
                    snapshot_type TEXT,
                    file_path TEXT,
                    metadata TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✓ Database initialized")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """Encrypt data using Fernet"""
        if not self.fernet:
            return data if isinstance(data, str) else data.decode('utf-8')
        
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            encrypted = self.fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"Error encrypting data: {e}")
            return data if isinstance(data, str) else data.decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet"""
        if not self.fernet:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return encrypted_data
    
    def log_incident(self, incident: Dict[str, Any]):
        """Log an incident to the database"""
        try:
            incident_id = incident.get('id', f"incident_{int(time.time())}")
            timestamp = incident.get('timestamp', time.time())
            incident_type = incident.get('type', 'unknown')
            confidence = incident.get('confidence', 0.0)
            module = incident.get('module', 'unknown')
            details = json.dumps(incident.get('details', {}))
            
            # Encrypt sensitive data
            encrypted_details = self.encrypt_data(details)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO incidents 
                (id, timestamp, type, confidence, module, details, encrypted_data, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident_id,
                timestamp,
                incident_type,
                confidence,
                module,
                details,
                encrypted_details,
                json.dumps(incident.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            
            print(f"Logged incident: {incident_id} ({incident_type})")
            
        except Exception as e:
            print(f"Error logging incident: {e}")
    
    def save_incident(self, incident: Dict[str, Any]) -> str:
        """Save incident data to file"""
        try:
            incident_id = incident.get('id', f"incident_{int(time.time())}")
            timestamp = incident.get('timestamp', time.time())
            
            # Create incident directory
            incident_dir = self.incidents_path / incident_id
            incident_dir.mkdir(exist_ok=True)
            
            # Save incident data
            incident_file = incident_dir / f"{incident_id}_data.json"
            
            # Encrypt sensitive data before saving
            incident_copy = incident.copy()
            if 'frame_data' in incident_copy:
                # Don't save large frame data to JSON
                incident_copy['frame_data'] = {
                    'has_frame_data': True,
                    'frame_count': len(incident_copy['frame_data'].get('all_faces', []))
                }
            
            with open(incident_file, 'w') as f:
                json.dump(incident_copy, f, indent=2)
            
            # Create metadata
            metadata = {
                'incident_id': incident_id,
                'timestamp': timestamp,
                'type': incident.get('type', 'unknown'),
                'confidence': incident.get('confidence', 0.0),
                'module': incident.get('module', 'unknown'),
                'file_path': str(incident_file),
                'created_at': datetime.fromtimestamp(timestamp).isoformat()
            }
            
            # Save metadata
            metadata_file = incident_dir / f"{incident_id}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Log to database
            self.log_incident(incident)
            
            print(f"Saved incident: {incident_id}")
            return incident_id
            
        except Exception as e:
            print(f"Error saving incident: {e}")
            return None
    
    def save_snapshot(self, incident_id: str, snapshot_data: Dict[str, Any], 
                     snapshot_type: str = 'frame') -> Optional[str]:
        """Save a snapshot (image, audio, etc.)"""
        try:
            snapshot_id = f"{incident_id}_{snapshot_type}_{int(time.time())}"
            
            # Create snapshot directory
            snapshot_dir = self.incidents_path / incident_id / 'snapshots'
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Save snapshot based on type
            if snapshot_type == 'frame' and 'frame' in snapshot_data:
                import cv2
                frame = snapshot_data['frame']
                snapshot_path = snapshot_dir / f"{snapshot_id}.jpg"
                cv2.imwrite(str(snapshot_path), frame)
                
            elif snapshot_type == 'audio' and 'audio' in snapshot_data:
                import wave
                audio_data = snapshot_data['audio']
                snapshot_path = snapshot_dir / f"{snapshot_id}.wav"
                
                with wave.open(str(snapshot_path), 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_data.tobytes())
            
            else:
                # Save as JSON for other types
                snapshot_path = snapshot_dir / f"{snapshot_id}.json"
                with open(snapshot_path, 'w') as f:
                    json.dump(snapshot_data, f, indent=2)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO snapshots 
                (id, timestamp, incident_id, snapshot_type, file_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                time.time(),
                incident_id,
                snapshot_type,
                str(snapshot_path),
                json.dumps(snapshot_data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            
            print(f"Saved snapshot: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return None
    
    def get_incidents(self, limit: int = 100, offset: int = 0, 
                     incident_type: str = None, module: str = None) -> List[Dict[str, Any]]:
        """Get incidents from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            
            if incident_type:
                query += " AND type = ?"
                params.append(incident_type)
            
            if module:
                query += " AND module = ?"
                params.append(module)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            incidents = []
            for row in rows:
                incident = {
                    'id': row[0],
                    'timestamp': row[1],
                    'type': row[2],
                    'confidence': row[3],
                    'module': row[4],
                    'details': json.loads(row[5]) if row[5] else {},
                    'metadata': json.loads(row[7]) if row[7] else {}
                }
                incidents.append(incident)
            
            conn.close()
            return incidents
            
        except Exception as e:
            print(f"Error getting incidents: {e}")
            return []
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific incident by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM incidents WHERE id = ?', (incident_id,))
            row = cursor.fetchone()
            
            if row:
                incident = {
                    'id': row[0],
                    'timestamp': row[1],
                    'type': row[2],
                    'confidence': row[3],
                    'module': row[4],
                    'details': json.loads(row[5]) if row[5] else {},
                    'metadata': json.loads(row[7]) if row[7] else {}
                }
                
                # Get snapshots
                cursor.execute('SELECT * FROM snapshots WHERE incident_id = ?', (incident_id,))
                snapshots = []
                for snapshot_row in cursor.fetchall():
                    snapshots.append({
                        'id': snapshot_row[0],
                        'timestamp': snapshot_row[1],
                        'type': snapshot_row[3],
                        'file_path': snapshot_row[4],
                        'metadata': json.loads(snapshot_row[5]) if snapshot_row[5] else {}
                    })
                
                incident['snapshots'] = snapshots
                
                conn.close()
                return incident
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error getting incident: {e}")
            return None
    
    def add_log(self, level: str, module: str, message: str, 
                encrypted_data: str = None):
        """Add a log entry"""
        try:
            timestamp = time.time()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs (timestamp, level, module, message, encrypted_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, level, module, message, encrypted_data))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error adding log: {e}")
    
    def get_logs(self, level: str = None, module: str = None, 
                 limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get logs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            if module:
                query += " AND module = ?"
                params.append(module)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            logs = []
            for row in rows:
                log = {
                    'id': row[0],
                    'timestamp': row[1],
                    'level': row[2],
                    'module': row[3],
                    'message': row[4],
                    'encrypted_data': row[5]
                }
                logs.append(log)
            
            conn.close()
            return logs
            
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old incidents and logs"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old incidents
            cursor.execute('DELETE FROM incidents WHERE timestamp < ?', (cutoff_time,))
            incidents_deleted = cursor.rowcount
            
            # Delete old logs
            cursor.execute('DELETE FROM logs WHERE timestamp < ?', (cutoff_time,))
            logs_deleted = cursor.rowcount
            
            # Delete old snapshots
            cursor.execute('DELETE FROM snapshots WHERE timestamp < ?', (cutoff_time,))
            snapshots_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"Cleaned up: {incidents_deleted} incidents, {logs_deleted} logs, {snapshots_deleted} snapshots")
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count incidents by type
            cursor.execute('SELECT type, COUNT(*) FROM incidents GROUP BY type')
            incidents_by_type = dict(cursor.fetchall())
            
            # Count incidents by module
            cursor.execute('SELECT module, COUNT(*) FROM incidents GROUP BY module')
            incidents_by_module = dict(cursor.fetchall())
            
            # Count logs by level
            cursor.execute('SELECT level, COUNT(*) FROM logs GROUP BY level')
            logs_by_level = dict(cursor.fetchall())
            
            # Total counts
            cursor.execute('SELECT COUNT(*) FROM incidents')
            total_incidents = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM logs')
            total_logs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM snapshots')
            total_snapshots = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_incidents': total_incidents,
                'total_logs': total_logs,
                'total_snapshots': total_snapshots,
                'incidents_by_type': incidents_by_type,
                'incidents_by_module': incidents_by_module,
                'logs_by_level': logs_by_level
            }
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    config = {
        'encryption_key': 'your-secret-key-here',
        'incidents_path': 'data/incidents',
        'logs_path': 'data/logs'
    }
    
    log_storage = LogStorage(config)
    
    # Test incident logging
    test_incident = {
        'id': 'test_incident_001',
        'timestamp': time.time(),
        'type': 'suspicious_activity',
        'confidence': 0.85,
        'module': 'activity_detect',
        'details': {
            'activity_type': 'fighting',
            'location': [100, 200, 300, 400]
        }
    }
    
    incident_id = log_storage.save_incident(test_incident)
    print(f"Saved incident: {incident_id}")
    
    # Test log entry
    log_storage.add_log('INFO', 'test_module', 'Test log message')
    
    # Get statistics
    stats = log_storage.get_statistics()
    print(f"Statistics: {stats}") 