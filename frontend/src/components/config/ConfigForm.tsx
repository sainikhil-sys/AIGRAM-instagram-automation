import React, { useEffect } from 'react';
import { Settings, Save } from 'lucide-react';
import { z } from 'zod';
import { useConfig, useUpdateConfig } from '../../hooks/configHooks';
import SecretInput from './SecretInput';
import { SystemConfig } from '../../services/configService';
import toast from 'react-hot-toast';

const configSchema = z.object({
  meta_access_token: z.string().min(1, 'Meta Access Token is required'),
  instagram_account_id: z.string().min(1, 'Instagram Account ID is required').regex(/^\d+$/, 'Account ID must be numeric'),
  gemini_api_key: z.string().min(1, 'Gemini API Key is required'),
  news_api_key: z.string().optional(),
  research_hour: z.number().min(0).max(23),
  research_minute: z.number().min(0).max(59),
  publish_hour: z.number().min(0).max(23),
  publish_minute: z.number().min(0).max(59),
});

export default function ConfigForm() {
  const { data: config, isLoading } = useConfig();
  const updateMutation = useUpdateConfig();

  const [formConfig, setFormConfig] = React.useState<Partial<SystemConfig>>({
    meta_access_token: '',
    instagram_account_id: '',
    gemini_api_key: '',
    news_api_key: '',
    research_hour: 8,
    research_minute: 0,
    publish_hour: 9,
    publish_minute: 0
  });

  const [errors, setErrors] = React.useState<Record<string, string>>({});

  useEffect(() => {
    if (config) {
      setFormConfig(config);
    }
  }, [config]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate with Zod
    const result = configSchema.safeParse(formConfig);
    if (!result.success) {
      const formatted = result.error.format();
      const newErrors: Record<string, string> = {};
      
      if (formatted.meta_access_token?._errors[0]) newErrors.meta_access_token = formatted.meta_access_token._errors[0];
      if (formatted.instagram_account_id?._errors[0]) newErrors.instagram_account_id = formatted.instagram_account_id._errors[0];
      if (formatted.gemini_api_key?._errors[0]) newErrors.gemini_api_key = formatted.gemini_api_key._errors[0];
      
      setErrors(newErrors);
      toast.error('Please fix the validation errors in the form.');
      return;
    }

    setErrors({});
    
    // Prepare payload (don't send masked secrets if they haven't changed)
    const payload = { ...formConfig };
    if (payload.meta_access_token === '***') delete payload.meta_access_token;
    if (payload.instagram_account_id === '***') delete payload.instagram_account_id;
    if (payload.gemini_api_key === '***') delete payload.gemini_api_key;
    if (payload.news_api_key === '***') delete payload.news_api_key;

    if (window.confirm("Are you sure you want to save and deploy these credentials to production?")) {
      updateMutation.mutate(payload);
    }
  };

  if (isLoading) {
    return <div style={{ color: 'var(--text-muted)' }}>Loading settings...</div>;
  }

  return (
    <div className="glass-card config-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <Settings size={20} className="text-accent" />
        <h3 style={{ fontSize: '18px' }}>System Settings</h3>
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
        <SecretInput
          label="Meta Access Token"
          value={formConfig.meta_access_token || ''}
          onChange={(val) => setFormConfig({ ...formConfig, meta_access_token: val })}
          placeholder="EAA..."
          error={errors.meta_access_token}
        />

        <SecretInput
          label="Instagram Account ID"
          value={formConfig.instagram_account_id || ''}
          onChange={(val) => setFormConfig({ ...formConfig, instagram_account_id: val })}
          placeholder="178414..."
          error={errors.instagram_account_id}
        />

        <SecretInput
          label="Gemini 2.0 API Key"
          value={formConfig.gemini_api_key || ''}
          onChange={(val) => setFormConfig({ ...formConfig, gemini_api_key: val })}
          placeholder="AI content generator key"
          error={errors.gemini_api_key}
        />

        <SecretInput
          label="NewsAPI.org Key (Optional)"
          value={formConfig.news_api_key || ''}
          onChange={(val) => setFormConfig({ ...formConfig, news_api_key: val })}
          placeholder="News aggregator key (falls back to RSS)"
        />

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
          disabled={updateMutation.isPending}
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center', marginTop: '12px' }}
        >
          <Save size={18} />
          {updateMutation.isPending ? 'Saving Configurations...' : 'Save Config Overrides'}
        </button>
      </form>
    </div>
  );
}
