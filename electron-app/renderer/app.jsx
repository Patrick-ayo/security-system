import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [incidents, setIncidents] = useState([]);
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({});
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    // Load initial config
    loadConfig();
    
    // Set up event listeners for Python backend communication
    window.electronAPI.onPythonLog((event, message) => {
      setLogs(prev => [...prev, { timestamp: new Date().toISOString(), message }]);
    });

    window.electronAPI.onPythonError((event, error) => {
      setLogs(prev => [...prev, { timestamp: new Date().toISOString(), error: true, message: error }]);
    });

    window.electronAPI.onPythonMessage((event, message) => {
      if (message.type === 'incident') {
        setIncidents(prev => [...prev, message.data]);
      }
    });

    return () => {
      window.electronAPI.removeAllListeners('python-log');
      window.electronAPI.removeAllListeners('python-error');
      window.electronAPI.removeAllListeners('python-message');
    };
  }, []);

  const loadConfig = async () => {
    try {
      const configData = await window.electronAPI.getConfig();
      setConfig(configData);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const startMonitoring = async () => {
    try {
      // Request camera and microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: true
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      // Start Python backend monitoring
      await window.electronAPI.startMonitoring();
      setIsMonitoring(true);
      
      setLogs(prev => [...prev, { 
        timestamp: new Date().toISOString(), 
        message: 'Monitoring started successfully' 
      }]);
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      setLogs(prev => [...prev, { 
        timestamp: new Date().toISOString(), 
        error: true, 
        message: `Failed to start monitoring: ${error.message}` 
      }]);
    }
  };

  const stopMonitoring = async () => {
    try {
      // Stop camera and microphone
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }

      // Stop Python backend monitoring
      await window.electronAPI.stopMonitoring();
      setIsMonitoring(false);
      
      setLogs(prev => [...prev, { 
        timestamp: new Date().toISOString(), 
        message: 'Monitoring stopped' 
      }]);
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
    }
  };

  const loadIncidents = async () => {
    try {
      const incidentsData = await window.electronAPI.getIncidents();
      setIncidents(incidentsData);
    } catch (error) {
      console.error('Failed to load incidents:', error);
    }
  };

  const saveConfig = async (newConfig) => {
    try {
      await window.electronAPI.saveConfig(newConfig);
      setConfig(newConfig);
      setLogs(prev => [...prev, { 
        timestamp: new Date().toISOString(), 
        message: 'Configuration saved successfully' 
      }]);
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Security Monitor</h1>
        <div className="controls">
          <button 
            onClick={isMonitoring ? stopMonitoring : startMonitoring}
            className={isMonitoring ? 'stop-btn' : 'start-btn'}
          >
            {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
          </button>
          <button onClick={loadIncidents} className="secondary-btn">
            Load Incidents
          </button>
        </div>
      </header>

      <div className="main-content">
        <div className="video-section">
          <h2>Live Feed</h2>
          <video 
            ref={videoRef} 
            autoPlay 
            muted 
            className="video-feed"
            style={{ display: isMonitoring ? 'block' : 'none' }}
          />
          {!isMonitoring && (
            <div className="video-placeholder">
              <p>Click "Start Monitoring" to begin</p>
            </div>
          )}
        </div>

        <div className="sidebar">
          <div className="incidents-section">
            <h3>Recent Incidents</h3>
            <div className="incidents-list">
              {incidents.slice(-5).map((incident, index) => (
                <div key={index} className="incident-item">
                  <span className="incident-time">
                    {new Date(incident.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="incident-type">{incident.type}</span>
                  <span className="incident-confidence">
                    {Math.round(incident.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="logs-section">
            <h3>System Logs</h3>
            <div className="logs-list">
              {logs.slice(-10).map((log, index) => (
                <div key={index} className={`log-item ${log.error ? 'error' : ''}`}>
                  <span className="log-time">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .app {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: #1a1a1a;
          color: #ffffff;
        }

        .app-header {
          background: #2d2d2d;
          padding: 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #444;
        }

        .controls {
          display: flex;
          gap: 1rem;
        }

        .start-btn {
          background: #4CAF50;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
        }

        .stop-btn {
          background: #f44336;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
        }

        .secondary-btn {
          background: #2196F3;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
        }

        .main-content {
          flex: 1;
          display: flex;
          gap: 1rem;
          padding: 1rem;
        }

        .video-section {
          flex: 2;
          background: #2d2d2d;
          border-radius: 8px;
          padding: 1rem;
        }

        .video-feed {
          width: 100%;
          max-width: 640px;
          border-radius: 4px;
        }

        .video-placeholder {
          height: 480px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #3d3d3d;
          border-radius: 4px;
        }

        .sidebar {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .incidents-section, .logs-section {
          background: #2d2d2d;
          border-radius: 8px;
          padding: 1rem;
        }

        .incidents-list, .logs-list {
          max-height: 200px;
          overflow-y: auto;
        }

        .incident-item, .log-item {
          display: flex;
          justify-content: space-between;
          padding: 0.5rem;
          border-bottom: 1px solid #444;
          font-size: 0.9rem;
        }

        .log-item.error {
          color: #ff6b6b;
        }

        .incident-time, .log-time {
          color: #888;
          font-size: 0.8rem;
        }

        .incident-type {
          font-weight: bold;
        }

        .incident-confidence {
          color: #4CAF50;
        }
      `}</style>
    </div>
  );
}

export default App; 