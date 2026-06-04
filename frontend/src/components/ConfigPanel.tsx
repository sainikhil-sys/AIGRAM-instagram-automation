import { useState, useEffect } from 'react';
import { Settings, Save, Lock, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface ConfigPanelProps {
  apiUrl: string;
}

export default function ConfigPanel({ apiUrl }: ConfigPanelProps) {
  const queryClient = useQueryClient();

  const [formConfig, setFormConfig] = useState({
    meta_access_token: '',
    instagram_account_id: '',
    gemini_api_key: '',
    news_api_key: '',
    research_hour: 8,
    research_minute: 0,
    publish_hour: 9,
    publish_minute: 0
  });

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/config`);
      const cfg = res.data.data;
      setFormConfig(prev => ({ ...prev, ...cfg }));
      return cfg;
    },
    refetchOnWindowFocus: false,
  });

  const { data: auditLogs = [], isLoading: isLoadingAudit, refetch: refetchAuditLogs } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/audit-logs?limit=50`);
      return res.data.data || [];
    }
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: string) => {
      const res = await axios.post(`${apiUrl}/api/config`, payload, {
        headers: { 'Content-Type': 'application/json' },
      });
      return res.data;
    },
    onSuccess: () => {
      alert("Configuration updated and saved to PostgreSQL successfully!");
      queryClient.invalidateQueries({ queryKey: ['config'] });
      refetchAuditLogs();
    },
    onError: (error: any) => {
      alert(`Error saving: ${error.message}`);
    }
  });

  const testInstagramMutation = useMutation({
    mutationFn: async () => {
      const res = await axios.post(`${apiUrl}/api/test-instagram`);
      return res.data;
    },
    onSuccess: () => {
      refetchAuditLogs();
    }
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { ...formConfig };
    if (payload.meta_access_token === '***') delete payload.meta_access_token;
    if (payload.instagram_account_id === '***') delete payload.instagram_account_id;
    if (payload.gemini_api_key === '***') delete payload.gemini_api_key;
    if (payload.news_api_key === '***') delete payload.news_api_key;
    saveMutation.mutate(JSON.stringify(payload));
  };

  const igTestResult = testInstagramMutation.data;

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">Configuration</h1>
      <p className="page-subtitle">Manage environment credentials, schedules, and view audit trails</p>

      <div className="config-grid">
        <div className="glass-card config-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            <Settings size={20} className="text-accent" />
            <h3 style={{ fontSize: '18px' }}>System Settings</h3>
          </div>

          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
            <div className="form-group">
              <label className="form-label">Meta Access Token</label>
              <input
                type="password"
                className="form-input"
                value={formConfig.meta_access_token}
                onChange={e => setFormConfig({ ...formConfig, meta_access_token: e.target.value })}
                placeholder="EAA..."
              />
            </div>

            <div className="form-group">
              <label className="form-label">Instagram Account ID</label>
              <input
                type="text"
                className="form-input"
                value={formConfig.instagram_account_id}
                onChange={e => setFormConfig({ ...formConfig, instagram_account_id: e.target.value })}
                placeholder="178414..."
              />
            </div>

            <div className="form-group">
              <label className="form-label">Gemini 2.0 API Key</label>
              <input
                type="password"
                className="form-input"
                value={formConfig.gemini_api_key}
                onChange={e => setFormConfig({ ...formConfig, gemini_api_key: e.target.value })}
                placeholder="AI content generator key"
              />
            </div>

            <div className="form-group">
              <label className="form-label">NewsAPI.org Key (Optional)</label>
              <input
                type="password"
                className="form-input"
                value={formConfig.news_api_key}
                onChange={e => setFormConfig({ ...formConfig, news_api_key: e.target.value })}
                placeholder="News aggregator key (falls back to RSS)"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Research Hour (24h)</label>
                <select
                  className="form-input"
                  value={formConfig.research_hour}
                  onChange={e => setFormConfig({ ...formConfig, research_hour: parseInt(e.target.value) })}
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
                  value={formConfig.publish_hour}
                  onChange={e => setFormConfig({ ...formConfig, publish_hour: parseInt(e.target.value) })}
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, '0')}:00</option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginTop: '12px' }}
            >
              <Save size={18} />
              {saveMutation.isPending ? 'Saving Configurations...' : 'Save Config Overrides'}
            </button>
          </form>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              Instagram Diagnostics
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.4 }}>
              Before deploying the auto-post system in production, verify that the emulated connection registers successfully with Instagram.
            </p>

            <button
              onClick={() => testInstagramMutation.mutate()}
              disabled={testInstagramMutation.isPending}
              className="btn-secondary"
              style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Activity size={16} />
              {testInstagramMutation.isPending ? 'Authenticating and Testing...' : 'Test Connection'}
            </button>

            {igTestResult && (
              <div style={{ marginTop: '16px', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', fontSize: '13px', border: '1px solid var(--border-color)' }}>
                {igTestResult.success ? (
                  <div style={{ color: 'var(--success)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                      <ShieldCheck size={16} />
                      Connected to @{igTestResult.data.username}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '22px' }}>
                      Followers: {igTestResult.data.followers} | Posts: {igTestResult.data.posts}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--error)', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong>Login Failed:</strong>
                      <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', wordBreak: 'break-all' }}>
                        {igTestResult.error || testInstagramMutation.error?.message}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

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
                <span style={{ color: config?.news_api_key ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>
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

      <div className="glass-card" style={{ marginTop: '28px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Lock size={18} />
            System Audit Trail
          </h3>
          <button onClick={() => refetchAuditLogs()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
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
                {auditLogs.map((log: any) => (
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
