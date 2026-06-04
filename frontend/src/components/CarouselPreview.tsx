import { useState } from 'react';
import { ChevronLeft, ChevronRight, Send, AlertCircle, Sparkles, Image as ImageIcon } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface CarouselPreviewProps {
  apiUrl: string;
}

export default function CarouselPreview({ apiUrl }: CarouselPreviewProps) {
  const queryClient = useQueryClient();
  const [selectedPostIndex, setSelectedPostIndex] = useState(0);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);

  const { data: posts = [], isLoading } = useQuery({
    queryKey: ['posts'],
    queryFn: async () => {
      const res = await axios.get(`${apiUrl}/api/posts?limit=10`);
      return res.data.data || [];
    },
  });

  const publishMutation = useMutation({
    mutationFn: async (postId: number) => {
      const res = await axios.post(`${apiUrl}/api/publish/${postId}`);
      return res.data;
    },
    onSuccess: () => {
      alert("Publish pipeline started in background! Check logs for real-time status.");
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['posts'] });
      }, 3000);
    },
    onError: (error: any) => {
      alert(`Error triggering publish: ${error.message}`);
    }
  });

  const activePost = posts[selectedPostIndex];
  const slideUrls = activePost?.image_urls || [];

  const handleNextSlide = () => {
    if (activeSlideIndex < slideUrls.length - 1) {
      setActiveSlideIndex(prev => prev + 1);
    }
  };

  const handlePrevSlide = () => {
    if (activeSlideIndex > 0) {
      setActiveSlideIndex(prev => prev - 1);
    }
  };

  if (isLoading) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center', marginTop: '24px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading generated carousels...</p>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="glass-card animate-fade-in" style={{ padding: '40px', textAlign: 'center', marginTop: '24px' }}>
        <AlertCircle size={36} style={{ color: 'var(--warning)', margin: '0 auto 12px' }} />
        <h3>No Carousel Posts Found</h3>
        <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>
          Run the AI news research pipeline first to generate slides.
        </p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">Carousel Preview</h1>
      <p className="page-subtitle">Inspect generated slides and publish manual override posts</p>

      <div className="grid-cols-2" style={{ gridTemplateColumns: '1fr 2fr', alignItems: 'start' }}>
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h3 style={{ fontSize: '16px', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            Generated Posts ({posts.length})
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '420px', overflowY: 'auto', paddingRight: '4px' }}>
            {posts.map((post: any, index: number) => (
              <button
                key={post.id}
                onClick={() => {
                  setSelectedPostIndex(index);
                  setActiveSlideIndex(0);
                }}
                className={`nav-item ${selectedPostIndex === index ? 'active' : ''}`}
                style={{ 
                  textAlign: 'left', 
                  flexDirection: 'column', 
                  alignItems: 'flex-start',
                  padding: '12px',
                  background: selectedPostIndex === index ? 'linear-gradient(90deg, rgba(139, 92, 246, 0.1), transparent)' : 'rgba(255,255,255,0.02)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', fontSize: '11px', color: 'var(--text-dim)', marginBottom: '4px' }}>
                  <span>{post.run_date}</span>
                  <span className={`badge ${post.status}`}>{post.status}</span>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', lineBreak: 'anywhere' }}>
                  #{post.rank} {post.headline}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '30px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div className="phone-mockup">
              <div className="phone-screen">
                <div className="phone-header">
                  @ai_daily_news · Carousel Preview
                </div>
                <div className="phone-content">
                  {slideUrls.length > 0 ? (
                    <img 
                      src={slideUrls[activeSlideIndex].startsWith('http') ? slideUrls[activeSlideIndex] : `${apiUrl}${slideUrls[activeSlideIndex]}`}
                      alt={`Slide ${activeSlideIndex + 1}`} 
                      className="phone-slide-img"
                      onError={(e: any) => {
                        e.target.onerror = null;
                        e.target.src = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop&q=60";
                      }}
                    />
                  ) : (
                    <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '20px' }}>
                      <ImageIcon size={48} style={{ margin: '0 auto 12px' }} />
                      <p style={{ fontSize: '12px' }}>No slides compiled</p>
                    </div>
                  )}

                  {slideUrls.length > 1 && (
                    <>
                      {activeSlideIndex > 0 && (
                        <button 
                          onClick={handlePrevSlide}
                          className="btn-icon" 
                          style={{ position: 'absolute', left: '8px', zIndex: 5, background: 'rgba(0,0,0,0.6)' }}
                        >
                          <ChevronLeft size={18} />
                        </button>
                      )}
                      {activeSlideIndex < slideUrls.length - 1 && (
                        <button 
                          onClick={handleNextSlide}
                          className="btn-icon" 
                          style={{ position: 'absolute', right: '8px', zIndex: 5, background: 'rgba(0,0,0,0.6)' }}
                        >
                          <ChevronRight size={18} />
                        </button>
                      )}
                    </>
                  )}
                </div>
                <div className="phone-footer">
                  <div className="phone-caption">
                    <strong>ai_daily_news</strong> {activePost?.caption || "Loading caption..."}
                  </div>
                </div>
              </div>
            </div>

            {slideUrls.length > 0 && (
              <div className="carousel-dots">
                {slideUrls.map((_: any, i: number) => (
                  <div key={i} className={`carousel-dot ${activeSlideIndex === i ? 'active' : ''}`} />
                ))}
              </div>
            )}
            
            <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '12px' }}>
              Slide {activeSlideIndex + 1} of {slideUrls.length}
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <span className="stat-label">Article Source</span>
              <h4 style={{ color: 'var(--accent-secondary)', marginTop: '4px' }}>
                <a href={activePost?.source_url} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {activePost?.source || "Unknown Source"}
                  <Sparkles size={14} />
                </a>
              </h4>
            </div>

            <div>
              <span className="stat-label">Virality Score</span>
              <div className="stat-value" style={{ color: 'var(--warning)', fontSize: '28px', marginTop: '4px' }}>
                {activePost?.virality_score ? activePost.virality_score.toFixed(1) : 'N/A'}/100
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
              <span className="stat-label">Full Caption & Tags</span>
              <textarea
                readOnly
                value={activePost?.caption || ''}
                className="form-input"
                style={{ flex: 1, minHeight: '180px', marginTop: '8px', resize: 'none', fontSize: '13px', lineHeight: 1.5, background: 'rgba(0,0,0,0.15)' }}
              />
            </div>

            <button
              onClick={() => {
                if (activePost) {
                  publishMutation.mutate(activePost.id);
                }
              }}
              disabled={publishMutation.isPending || activePost?.status === 'published'}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <Send size={18} />
              {publishMutation.isPending ? 'Publishing...' : activePost?.status === 'published' ? 'Published!' : 'Publish Override Now'}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
