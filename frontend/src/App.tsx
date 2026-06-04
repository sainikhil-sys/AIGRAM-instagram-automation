import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Settings, Terminal, Radio, PlayCircle, Eye, Sparkles } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Logs from './components/Logs';
import CarouselPreview from './components/CarouselPreview';
import ConfigPanel from './components/ConfigPanel';

// Determine backend URL dynamically based on environment
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Check if we are running in local Vite development server
  const ports = ['3000', '5173', '5174'];
  if (ports.includes(window.location.port)) {
    return 'http://localhost:8000';
  }
  // If compiled and served directly from backend or identical origin
  return '';
};

const API_URL = getApiUrl();

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);

  // Poll status to keep track of pipeline state
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/api/status`);
        const data = await res.json();
        setIsPipelineRunning(data.data?.pipeline_active || false);
      } catch (e) {
        console.error("API link inactive:", e);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const runPipeline = async () => {
    setIsPipelineRunning(true);
    try {
      const res = await fetch(`${API_URL}/api/run-all`, { method: 'POST' });
      if (res.ok) {
        alert("Full pipeline execution started in background! Check logs for progress.");
      } else {
        alert("Failed to start pipeline.");
      }
    } catch (e) {
      alert("Failed to connect to backend: " + e.message);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar glass-panel">
        <div className="brand">
          <Radio size={28} className="text-accent" style={{ color: 'var(--accent-primary)' }} />
          AIGRAM Engine
        </div>

        <nav className="nav-menu">
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} />
            Dashboard
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
          >
            <Eye size={18} />
            Carousel Preview
          </button>

          <button 
            className={`nav-item ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            <Settings size={18} />
            Configuration
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            <Terminal size={18} />
            System Logs
          </button>
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <button 
            className="btn-primary" 
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={runPipeline}
            disabled={isPipelineRunning}
          >
            <PlayCircle size={20} />
            {isPipelineRunning ? 'Running Pipeline...' : 'Trigger Pipeline'}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'dashboard' && <Dashboard apiUrl={API_URL} />}
        {activeTab === 'preview' && <CarouselPreview apiUrl={API_URL} />}
        {activeTab === 'config' && <ConfigPanel apiUrl={API_URL} />}
        {activeTab === 'logs' && <Logs apiUrl={API_URL} />}
      </main>
    </div>
  );
}

export default App;
