import axios from 'axios';

// Get API URL from env or fallback for local dev
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export interface SystemConfig {
  meta_access_token: string;
  instagram_account_id: string;
  gemini_api_key: string;
  news_api_key: string;
  research_hour: number;
  research_minute: number;
  publish_hour: number;
  publish_minute: number;
}

export interface HealthStatus {
  postgres: boolean;
  redis: boolean;
  cloudinary: boolean;
  instagram: boolean;
  gemini: boolean;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  actor: string;
  action: string;
  status: 'success' | 'failure';
  details: string | null;
  ip_address: string | null;
}

export const configService = {
  async getConfig(): Promise<SystemConfig> {
    const res = await axios.get(`${API_URL}/api/config`);
    return res.data.data;
  },

  async updateConfig(payload: Partial<SystemConfig>): Promise<void> {
    await axios.post(`${API_URL}/api/config`, payload, {
      headers: { 'Content-Type': 'application/json' },
    });
  },

  async testInstagram(): Promise<any> {
    const res = await axios.post(`${API_URL}/api/test-instagram`);
    return res.data;
  },

  async getAuditLogs(): Promise<AuditLog[]> {
    const res = await axios.get(`${API_URL}/api/audit-logs?limit=50`);
    return res.data.data;
  },

  async getHealthStatus(): Promise<HealthStatus> {
    const res = await axios.get(`${API_URL}/api/health`);
    return res.data.data;
  }
};
