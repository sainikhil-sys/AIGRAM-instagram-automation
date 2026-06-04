import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface LogsProps {
  apiUrl: string;
}

export default function Logs({ apiUrl }: LogsProps) {
  const terminalRef = useRef<HTMLDivElement>(null);

  const { data: logs = [] } = useQuery({
    queryKey: ['logs'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/logs?limit=100`);
      return res.data.data || [];
    },
    refetchInterval: 3000,
  });

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColorClass = (msg: string) => {
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
          logs.map((log: string, i: number) => (
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
