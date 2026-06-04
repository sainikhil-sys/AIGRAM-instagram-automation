import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface SecretInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string;
}

export default function SecretInput({ label, value, onChange, placeholder, error }: SecretInputProps) {
  const [show, setShow] = useState(false);

  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <div style={{ position: 'relative' }}>
        <input
          type={show ? 'text' : 'password'}
          className={`form-input ${error ? 'border-red-500' : ''}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          style={{ width: '100%', paddingRight: '40px' }}
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          style={{
            position: 'absolute',
            right: '10px',
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
          aria-label={show ? 'Hide secret' : 'Show secret'}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {error && <span style={{ color: 'var(--error)', fontSize: '12px', marginTop: '4px' }}>{error}</span>}
    </div>
  );
}
