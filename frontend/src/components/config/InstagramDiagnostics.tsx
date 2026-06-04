import React from 'react';
import { Activity, ShieldCheck, AlertTriangle } from 'lucide-react';
import { useInstagramTest } from '../../hooks/configHooks';

export default function InstagramDiagnostics() {
  const testInstagramMutation = useInstagramTest();
  const igTestResult = testInstagramMutation.data;

  return (
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
        {testInstagramMutation.isPending ? 'Testing Connection...' : 'Test Connection'}
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
                <strong>Connection Failed:</strong>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', wordBreak: 'break-all' }}>
                  {igTestResult.error || testInstagramMutation.error?.message}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
