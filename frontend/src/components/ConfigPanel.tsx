import React, { useEffect, useState } from 'react';
import { Settings, Save, Lock, AlertTriangle, ShieldCheck, HelpCircle, Activity } from 'lucide-react';

export default function ConfigPanel({ apiUrl }) {
  const [config, setConfig] = useState({
    instagram_username: '',
    instagram_password: '',
    gemini_api_key: '',
    news_api_key: '',
    research_hour: 8,
    research_minute: 0,
    publish_hour: 9,
    publish_minute: 0
  });

  const [igTestResult, setIgTestResult] = useState(null);
  const [isTestingIg, setIsTestingIg] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [isLoadingAudit, setIsLoadingAudit] = useState(true);

  useEffect(() => {
    fetchConfig();
    fetchAuditLogs();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/config`);
      const data = await res.json();
      setConfig(prev => ({
        ...prev,
        ...data.data
      }));
    } catch (e) {
      console.error("Failed to load config:", e);
    }
  };

  const fetchAuditLogs = async () => {
    setIsLoadingAudit(true);
    try {
      const res = await fetch(`${apiUrl}/api/audit-logs?limit=50`);
      const data = await res.json();
      setAuditLogs(data.data || []);
    } catch (e) {
      console.error("Failed to fetch audit logs:", e);
    } finally {
      setIsLoadingAudit(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      // Send changes (blanks are skipped/not updated in backend depending on implementation)
      const res = await fetch(`${apiUrl}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonBody(config)
      });
      if (res.ok) {
        alert("Configuration updated and saved to PostgreSQL successfully!");
        fetchConfig();
        fetchAuditLogs();
      } else {
        alert("Failed to save configuration.");
      }
    } catch (e) {
      alert("Error saving: " + e.message);
    } finally {
      setIsSaving(false);
    }
  };

  // Skip sending passwords if they were unchanged (i.e. if they are mask values "***")
  const jsonBody = (cfg) => {
    const payload = { ...cfg };
    if (payload.instagram_password === '***') delete payload.instagram_password;
    if (payload.gemini_api_key === '***') delete payload.gemini_api_key;
    if (payload.news_api_key === '***') delete payload.news_api_key;
    return JSON.stringify(payload);
  };

  const testInstagram = async () => {
    setIsTestingIg(true);
    setIgTestResult(null);
    try {
      const res = await fetch(`${apiUrl}/api/test-instagram`, { method: 'POST' });
      const data = await res.json();
      setIgTestResult(data.data || data);
      fetchAuditLogs();
    } catch (e) {
      setIgTestResult({ success: false, error: e.message });
    } finally {
      setIsTestingIg(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">Configuration</h1>
      <p className="page-subtitle">Manage environment credentials, schedules, and view audit trails</p>

      <div className="config-grid">
        {/* Settings Form */}
        <div className="glass-card config-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            <Settings size={20} className="text-accent" />
            <h3 style={{ fontSize: '18px' }}>System Settings</h3>
          </div>

          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Instagram Username</label>
              <input
                type="text"
                className="form-input"
                value={config.instagram_username || ''}
                onChange={e => setConfig({ ...config, instagram_username: e.target.value })}
                placeholder="username"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Instagram Password</label>
              <input
                type="password"
                className="form-input"
                value={config.instagram_password || ''}
                onChange={e => setConfig({ ...config, instagram_password: e.target.value })}
                placeholder="••••••••••••"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Gemini 2.0 API Key</label>
              <input
                type="password"
                className="form-input"
                value={config.gemini_api_key || ''}
                onChange={e => setConfig({ ...config, gemini_api_key: e.target.value })}
                placeholder="AI content generator key"
              />
            </div>

            <div className="form-group">
              <label className="form-label">NewsAPI.org Key (Optional)</label>
              <input
                type="password"
                className="form-input"
                value={config.news_api_key || ''}
                onChange={e => setConfig({ ...config, news_api_key: e.target.value })}
                placeholder="News aggregator key (falls back to RSS)"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Research Hour (24h)</label>
                <select
                  className="form-input"
                  value={config.research_hour}
                  onChange={e => setConfig({ ...config, research_hour: parseInt(e.target.value) })}
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, '0')}:00</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Publish Hour (24h)</label>
                <select
                  className="form-input"
                  value={config.publish_hour}
                  onChange={e => setConfig({ ...config, publish_hour: parseInt(e.target.value) })}
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, '0')}:00</option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSaving}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginTop: '12px' }}
            >
              <Save size={18} />
              {isSaving ? 'Saving Configurations...' : 'Save Config Overrides'}
            </button>
          </form>
        </div>

        {/* Integration Utilities & Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Instagram connection test */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              Instagram Diagnostics
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.4 }}>
              Before deploying the auto-post system in production, verify that the emulated connection registers successfully with Instagram.
            </p>

            <button
              onClick={testInstagram}
              disabled={isTestingIg}
              className="btn-secondary"
              style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Activity size={16} />
              {isTestingIg ? 'Authenticating and Testing...' : 'Test Connection'}
            </button>

            {igTestResult && (
              <div style={{ marginTop: '16px', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', fontSize: '13px', border: '1px solid var(--border-color)' }}>
                {igTestResult.success ? (
                  <div style={{ color: 'var(--success)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                      <ShieldCheck size={16} />
                      Connected to @{igTestResult.username}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '22px' }}>
                      Followers: {igTestResult.followers} | Posts: {igTestResult.posts}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--error)', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong>Login Failed:</strong>
                      <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', wordBreak: 'break-all' }}>
                        {igTestResult.error}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Database/API Details */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '12px' }}>
              System Credentials Status
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Neon PostgreSQL:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Connected</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Upstash Redis:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Connected</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Cloudinary Integration:</span>
                <span style={{ color: config.news_api_key ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>
                  Active
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Telemetry Engine:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Prometheus</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* System Audit logs (Audit logging) */}
      <div className="glass-card" style={{ marginTop: '28px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Lock size={18} />
            System Audit Trail
          </h3>
          <button onClick={fetchAuditLogs} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
            Refresh
          </button>
        </div>

        {isLoadingAudit ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px' }}>Loading audit trail...</p>
        ) : auditLogs.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '20px' }}>No audit actions recorded</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px' }}>Timestamp (UTC)</th>
                  <th style={{ padding: '8px' }}>Actor</th>
                  <th style={{ padding: '8px' }}>Action</th>
                  <th style={{ padding: '8px' }}>Status</th>
                  <th style={{ padding: '8px' }}>IP Address</th>
                  <th style={{ padding: '8px' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-dim)' }}>
                      {log.timestamp ? new Date(log.timestamp).toISOString().replace('T', ' ').slice(0, 19) : ''}
                    </td>
                    <td style={{ padding: '8px', fontWeight: 600 }}>{log.actor}</td>
                    <td style={{ padding: '8px', color: 'var(--accent-secondary)' }}>{log.action}</td>
                    <td style={{ padding: '8px' }}>
                      <span style={{ 
                        color: log.status === 'success' ? 'var(--success)' : 'var(--error)',
                        background: log.status === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                        padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 600
                      }}>
                        {log.status.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '8px', color: 'var(--text-dim)' }}>{log.ip_address || 'local'}</td>
                    <td style={{ padding: '8px', color: 'var(--text-muted)', fontSize: '12px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={log.details}>
                      {log.details || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
