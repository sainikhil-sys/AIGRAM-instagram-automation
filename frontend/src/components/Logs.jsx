import React, { useEffect, useState, useRef } from 'react';

export default function Logs({ apiUrl }) {
  const [logs, setLogs] = useState([]);
  const terminalRef = useRef(null);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/logs?limit=100`);
      const data = await res.json();
      // Extract the live_logs array from response dictionary
      setLogs(data.live_logs || []);
    } catch (e) {
      console.error("Failed to fetch logs:", e);
    }
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColorClass = (msg) => {
    const msgLower = msg.toLowerCase();
    if (msgLower.includes('error') || msg.includes('❌') || msg.includes('✗')) return 'log-error';
    if (msgLower.includes('success') || msg.includes('✓') || msgLower.includes('complete')) return 'log-success';
    if (msgLower.includes('warning') || msg.includes('⚠')) return 'log-warning';
    return 'log-info';
  };

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">System Logs</h1>
      <p className="page-subtitle">Live output from the distributed AIGRAM backend</p>

      <div className="terminal" ref={terminalRef}>
        {logs.length === 0 ? (
          <div style={{ color: 'var(--text-dim)' }}>Waiting for system events...</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="log-line">
              <span className={getLogColorClass(log)}>
                {log}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
