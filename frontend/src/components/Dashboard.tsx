import { useState } from 'react';
import { Activity, Image as ImageIcon, Clock, AlertTriangle, Loader2, Play, Sparkles, CheckCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface DashboardProps {
  apiUrl: string;
}

export default function Dashboard({ apiUrl }: DashboardProps) {
  const queryClient = useQueryClient();
  const [isTriggering, setIsTriggering] = useState(false);

  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['status'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/status`);
      return res.data.data;
    },
    refetchInterval: 5000,
  });

  const { data: news = [] } = useQuery({
    queryKey: ['news'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/news`);
      return res.data.data || [];
    },
    refetchInterval: 5000,
  });

  const { data: postsData, isLoading: postsLoading, error: postsError } = useQuery({
    queryKey: ['posts'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/posts?limit=5`);
      return res.data;
    },
    refetchInterval: 5000,
  });

  const posts = postsData?.posts || [];

  const triggerMutation = useMutation({
    mutationFn: async (endpoint: string) => {
      const res = await axios.post(`${apiUrl}/api/${endpoint}`);
      return res.data;
    },
    onMutate: () => setIsTriggering(true),
    onSuccess: (_, endpoint) => {
      alert(`Pipeline (${endpoint}) started successfully!`);
      queryClient.invalidateQueries({ queryKey: ['status'] });
    },
    onError: (error: any) => {
      alert(`Error starting pipeline: ${error.message}`);
    },
    onSettled: () => setIsTriggering(false),
  });

  const getSystemPill = (isActive: boolean, label: string) => (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '4px',
      fontSize: '11px',
      fontWeight: 600,
      padding: '2px 8px',
      borderRadius: '20px',
      background: isActive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
      color: isActive ? 'var(--success)' : 'var(--error)',
      border: `1px solid ${isActive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
    }}>
      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: isActive ? 'var(--success)' : 'var(--error)' }} />
      {label}
    </span>
  );

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>Real-time overview of your Instagram media factory</p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end', maxWidth: '400px' }}>
          {getSystemPill(!!status?.instagram_configured, "Instagram")}
          {getSystemPill(!!status?.gemini_configured, "Gemini AI")}
          {getSystemPill(!!status?.cloudinary_configured, "Cloudinary")}
          {getSystemPill(!!status?.redis_configured, "Redis Cache")}
        </div>
      </div>

      <div className="grid-cols-3">
        <div className="glass-card stat-card delay-1 animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--accent-secondary)' }}>
            <Activity size={22} />
            <span className="stat-label">Pipeline Status</span>
          </div>
          <div className="stat-value" style={{ color: status?.pipeline_active ? 'var(--success)' : 'var(--text-main)' }}>
            {statusLoading ? '...' : (status?.pipeline_active ? 'Processing' : 'Idle')}
          </div>
        </div>

        <div className="glass-card stat-card delay-2 animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--accent-primary)' }}>
            <ImageIcon size={22} />
            <span className="stat-label">Posts Generated</span>
          </div>
          <div className="stat-value">{posts.length}</div>
        </div>

        <div className="glass-card stat-card delay-3 animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--warning)' }}>
            <Clock size={22} />
            <span className="stat-label">Next Publication</span>
          </div>
          <div className="stat-value" style={{ fontSize: '28px', marginTop: 'auto' }}>
            {status?.schedule?.publish || "09:00"}
          </div>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '20px', marginTop: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Manual Controls Override</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
            Manually trigger parts of the pipeline immediately. This overrides the automatic scheduling constraints.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => triggerMutation.mutate('run-research')}
            disabled={isTriggering || status?.pipeline_active}
            className="btn-secondary"
            style={{ fontSize: '13px', padding: '8px 16px' }}
          >
            Run Research Only
          </button>
          <button
            onClick={() => triggerMutation.mutate('run-publish')}
            disabled={isTriggering || status?.pipeline_active}
            className="btn-secondary"
            style={{ fontSize: '13px', padding: '8px 16px' }}
          >
            Publish Queued Posts
          </button>
          <button
            onClick={() => triggerMutation.mutate('run-all')}
            disabled={isTriggering || status?.pipeline_active}
            className="btn-primary"
            style={{ fontSize: '13px', padding: '8px 16px' }}
          >
            <Play size={14} />
            Run Full Pipeline
          </button>
        </div>
      </div>

      <div className="grid-cols-2" style={{ gridTemplateColumns: '1fr 1fr', marginTop: '32px', gap: '30px' }}>
        
        <div>
          <h2 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={18} style={{ color: 'var(--warning)' }} />
            Today's AI News Research
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {news.length === 0 ? (
              <div className="glass-card" style={{ padding: '30px', textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No news researched yet. Run pipeline to fetch today's trending updates.</p>
              </div>
            ) : (
              news.map((item: any, idx: number) => (
                <div key={idx} className="glass-card" style={{ padding: '16px', position: 'relative', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ 
                      fontSize: '10px', 
                      background: 'rgba(255,255,255,0.05)', 
                      padding: '2px 6px', 
                      borderRadius: '4px',
                      color: 'var(--accent-secondary)',
                      fontWeight: 600
                    }}>
                      {item.source}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--warning)' }}>
                      Score: {item.score}
                    </span>
                  </div>
                  <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', lineHeight: 1.4 }}>
                    {item.title}
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.summary}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        <div>
          <h2 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <CheckCircle size={18} style={{ color: 'var(--success)' }} />
            Publishing Queue
          </h2>

          {postsLoading ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
              <Loader2 className="animate-spin" size={24} style={{ color: 'var(--accent-primary)', margin: '0 auto' }} />
              <p style={{ color: 'var(--text-muted)', marginTop: '8px', fontSize: '13px' }}>Loading posts queue...</p>
            </div>
          ) : postsError ? (
            <div className="glass-card" style={{ padding: '30px', textAlign: 'center', borderColor: 'var(--error)' }}>
              <AlertTriangle size={24} style={{ color: 'var(--error)', margin: '0 auto' }} />
              <p style={{ color: 'var(--text-muted)', marginTop: '8px', fontSize: '13px' }}>{postsError.message}</p>
            </div>
          ) : posts.length === 0 ? (
            <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No queued content items. Trigger the pipeline to generate slides.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {posts.map((post: any) => (
                <div key={post.id} className="glass-card" style={{ padding: '16px', display: 'flex', gap: '16px', alignItems: 'center' }}>
                  <div style={{ width: '70px', height: '70px', borderRadius: '8px', overflow: 'hidden', background: '#000', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {post.image_urls && post.image_urls.length > 0 ? (
                      <img 
                        src={post.image_urls[0].startsWith('http') ? post.image_urls[0] : `${apiUrl}${post.image_urls[0]}`}
                        alt="Slide Thumbnail" 
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                      />
                    ) : (
                      <ImageIcon size={24} style={{ color: 'var(--text-dim)' }} />
                    )}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                        Rank #{post.rank} · {post.run_date}
                      </span>
                      <span className={`badge ${post.status}`}>
                        {post.status}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {post.headline}
                    </h4>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
