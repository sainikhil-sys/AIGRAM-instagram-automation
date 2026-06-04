import React from 'react';
import { useHealthStatus } from '../../hooks/configHooks';

export default function HealthStatusCard() {
  const { data: health, isLoading, isError } = useHealthStatus();

  return (
    <div className="glass-card" style={{ padding: '24px' }}>
      <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '12px' }}>
        System Credentials Status
      </h3>
      {isLoading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading health status...</p>
      ) : isError ? (
        <p style={{ color: 'var(--error)', fontSize: '13px' }}>Failed to fetch health status</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Neon PostgreSQL:</span>
            <span style={{ color: health?.postgres ? 'var(--success)' : 'var(--error)', fontWeight: 600 }}>
              {health?.postgres ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Upstash Redis:</span>
            <span style={{ color: health?.redis ? 'var(--success)' : 'var(--error)', fontWeight: 600 }}>
              {health?.redis ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Cloudinary Integration:</span>
            <span style={{ color: health?.cloudinary ? 'var(--success)' : 'var(--error)', fontWeight: 600 }}>
              {health?.cloudinary ? 'Connected' : 'Missing Keys'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Meta Graph API:</span>
            <span style={{ color: health?.instagram ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>
              {health?.instagram ? 'Connected' : 'Not Configured'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Gemini AI:</span>
            <span style={{ color: health?.gemini ? 'var(--success)' : 'var(--error)', fontWeight: 600 }}>
              {health?.gemini ? 'Connected' : 'Missing Key'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
