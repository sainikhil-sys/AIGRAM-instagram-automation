/* =====================================================
   app.js — AI Instagram Automation Dashboard Logic
   ===================================================== */

const API = 'http://localhost:8000';

// ── State ──────────────────────────────────────────────
let currentPosts = [];
let currentNews = [];
let currentModalPost = null;
let currentSlide = 0;
let engagementChart = null;
let performanceChart = null;
let statusInterval = null;
let logInterval = null;

// ── Init ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  loadStatus();
  loadPosts();
  loadLogs();
  startAutoRefresh();
  updatePipelineDate();
  loadConfig();
});

function startAutoRefresh() {
  // Refresh status every 5 seconds
  statusInterval = setInterval(() => {
    loadStatus();
    loadLogs();
  }, 5000);

  // Refresh posts every 15 seconds
  setInterval(() => {
    loadPosts();
  }, 15000);
}

// ── Section Navigation ─────────────────────────────────
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const section = document.getElementById(`section-${name}`);
  const navBtn = document.getElementById(`nav-${name}`);

  if (section) section.classList.add('active');
  if (navBtn) navBtn.classList.add('active');

  // Load section-specific data
  if (name === 'news') loadNews();
  if (name === 'posts') loadPosts();
  if (name === 'queue') loadQueue();
  if (name === 'analytics') loadAnalytics();
  if (name === 'logs') loadLogs();
  if (name === 'settings') loadConfig();
}

// ── API Helpers ────────────────────────────────────────
async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(API + path, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error(`API Error [${path}]:`, e);
    throw e;
  }
}

// ── Status ─────────────────────────────────────────────
async function loadStatus() {
  try {
    const data = await apiFetch('/api/status');

    // Status indicator
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (data.pipeline_active) {
      dot.className = 'status-dot busy';
      text.textContent = '⚡ Pipeline Running...';
    } else {
      dot.className = 'status-dot';
      text.textContent = 'System Online';
    }

    // System info panel
    updateBadge('inf-backend', 'Online', 'green');
    updateBadge('inf-instagram', data.instagram_configured ? 'Connected' : 'Not set', data.instagram_configured ? 'green' : 'gray');
    updateBadge('inf-gemini', data.gemini_configured ? 'Active' : 'Not set', data.gemini_configured ? 'green' : 'gray');
    updateBadge('inf-newsapi', data.newsapi_configured ? 'Active' : 'Optional', data.newsapi_configured ? 'green' : 'gray');
    updateBadge('inf-scheduler', 'Active', 'green');

    // Schedule in next run badge
    const scheduleEl = document.getElementById('next-run-text');
    if (scheduleEl) scheduleEl.textContent = `Research: ${data.schedule.research} IST`;

    // Run now button state
    const btn = document.getElementById('btn-run-now');
    if (btn) btn.disabled = data.pipeline_active;

  } catch (e) {
    const dot = document.getElementById('status-dot');
    if (dot) dot.className = 'status-dot offline';
    const text = document.getElementById('status-text');
    if (text) text.textContent = 'Backend Offline';
    updateBadge('inf-backend', 'Offline', 'red');
  }
}

function updateBadge(id, text, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = `badge-${type}`;
}

// ── Pipeline Date ──────────────────────────────────────
function updatePipelineDate() {
  const el = document.getElementById('pipeline-date');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

// ── News ───────────────────────────────────────────────
async function loadNews() {
  try {
    const data = await apiFetch('/api/news');
    currentNews = data.news || [];

    const badge = document.getElementById('news-badge');
    if (badge) badge.textContent = currentNews.length || '';

    renderDashboardNews(currentNews);
    renderNewsGrid(currentNews);
  } catch (e) {
    console.error('Failed to load news:', e);
  }
}

function renderDashboardNews(news) {
  const list = document.getElementById('dashboard-news-list');
  if (!list) return;

  if (!news.length) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">📡</div><p>Run research to see today's top AI news</p></div>`;
    return;
  }

  list.innerHTML = news.slice(0, 5).map((item, i) => `
    <div class="news-item" onclick="openNewsLink('${escapeAttr(item.url)}')">
      <div class="news-rank">#${i + 1}</div>
      <div class="news-content">
        <div class="news-title">${escapeHtml(item.title)}</div>
        <div class="news-meta">
          <span class="news-source">${escapeHtml(item.source)}</span>
          <span class="news-score">⚡ ${item.score || 0} pts</span>
        </div>
      </div>
    </div>
  `).join('');
}

function renderNewsGrid(news) {
  const grid = document.getElementById('news-grid');
  if (!grid) return;

  if (!news.length) {
    grid.innerHTML = `<div class="empty-state large">
      <div class="empty-icon">📡</div>
      <h3>No news researched yet</h3>
      <p>Click "Run Research" to fetch today's top AI updates</p>
      <button class="btn-primary mt-2" onclick="runResearch()">Run Research Now</button>
    </div>`;
    return;
  }

  grid.innerHTML = news.map((item, i) => `
    <div class="news-card" onclick="openNewsLink('${escapeAttr(item.url)}')">
      <div class="news-card-rank">
        <span>🔥</span> #${i + 1} Top Story
      </div>
      <div class="news-card-title">${escapeHtml(item.title)}</div>
      <div class="news-card-summary">${escapeHtml((item.summary || '').slice(0, 200))}...</div>
      <div class="news-card-footer">
        <span class="news-card-source">${escapeHtml(item.source)}</span>
        <span class="news-card-score">⚡ ${item.score || 0} virality pts</span>
      </div>
    </div>
  `).join('');
}

function openNewsLink(url) {
  if (url) window.open(url, '_blank');
}

// ── Posts ──────────────────────────────────────────────
async function loadPosts() {
  try {
    const data = await apiFetch('/api/posts?limit=50');
    currentPosts = data.posts || [];

    const badge = document.getElementById('posts-badge');
    if (badge) badge.textContent = currentPosts.length || '';

    // Stats
    const today = new Date().toISOString().split('T')[0];
    const todayPosts = currentPosts.filter(p => p.run_date === today);
    const published = currentPosts.filter(p => p.status === 'published');

    setStatValue('sv-today', todayPosts.length);
    setStatValue('sv-slides', currentPosts.reduce((acc, p) => acc + (p.image_paths?.length || 0), 0));
    setStatValue('sv-published', published.length);

    renderPostsGrid(currentPosts);
    renderQueue(todayPosts);

    // Pipeline steps based on today's posts
    updatePipelineSteps(todayPosts);
  } catch (e) {
    console.error('Failed to load posts:', e);
  }
}

function setStatValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function updatePipelineSteps(todayPosts) {
  const steps = ['research', 'generate', 'design', 'publish'];
  const statuses = {
    research: todayPosts.length > 0 ? 'done' : 'scheduled',
    generate: todayPosts.length > 0 ? 'done' : 'waiting',
    design: todayPosts.some(p => p.image_paths?.length > 0) ? 'done' : 'waiting',
    publish: todayPosts.some(p => p.status === 'published') ? 'done' : (todayPosts.some(p => p.status === 'publishing') ? 'active' : 'waiting'),
  };

  steps.forEach(step => {
    const el = document.getElementById(`step-${step}`);
    const badge = document.getElementById(`badge-${step}`);
    if (!el || !badge) return;

    el.className = `pipeline-step ${statuses[step]}`;

    const labels = {
      done: '✓ Done', active: '⚡ Running', scheduled: '🕐 Scheduled',
      waiting: 'Waiting'
    };
    badge.textContent = labels[statuses[step]] || 'Waiting';
  });
}

function renderPostsGrid(posts) {
  const grid = document.getElementById('posts-grid');
  if (!grid) return;

  if (!posts.length) {
    grid.innerHTML = `<div class="empty-state large">
      <div class="empty-icon">🎨</div><h3>No posts generated yet</h3>
      <p>Run the pipeline to generate premium carousel posts</p>
      <button class="btn-primary mt-2" onclick="runAll()">Generate Posts</button>
    </div>`;
    return;
  }

  grid.innerHTML = posts.map(post => {
    const firstImg = post.image_urls?.[0] || '';
    const imgHTML = firstImg
      ? `<img src="${escapeAttr(API + firstImg)}" alt="Carousel slide" loading="lazy" />`
      : `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-4);font-size:13px;">No preview</div>`;

    const statusClass = `status-${post.status || 'queued'}`;
    const statusLabel = { queued: '🕐 Queued', published: '✅ Published', failed: '❌ Failed', publishing: '⚡ Publishing' }[post.status] || post.status;

    const canPublish = post.status === 'queued';

    return `
    <div class="post-card">
      <div class="post-thumbnail" onclick="openCarousel(${post.id})">
        ${imgHTML}
        <div class="post-thumbnail-overlay">
          <button class="post-preview-btn">👁 Preview</button>
        </div>
        <div class="slide-count-badge">📸 ${post.image_urls?.length || 0} slides</div>
        <div class="status-chip ${statusClass}">${statusLabel}</div>
      </div>
      <div class="post-info">
        <div class="post-headline">${escapeHtml((post.headline || '').slice(0, 80))}</div>
        <div class="post-meta">
          <span class="post-source">${escapeHtml(post.source || '')} · #${post.rank || 0}</span>
          <div class="post-actions">
            <button class="post-publish-btn" ${canPublish ? '' : 'disabled'} onclick="publishPost(${post.id}, this)">
              ${post.status === 'published' ? '✅ Live' : '📤 Publish'}
            </button>
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
}

// ── Queue ──────────────────────────────────────────────
function loadQueue() {
  loadPosts();
}

function renderQueue(todayPosts) {
  const container = document.getElementById('queue-container');
  if (!container) return;

  if (!todayPosts.length) {
    container.innerHTML = `<div class="empty-state large">
      <div class="empty-icon">📅</div><h3>Queue is empty</h3>
      <p>Run the research pipeline to queue today's posts</p>
    </div>`;
    return;
  }

  container.innerHTML = todayPosts.map((post, i) => {
    const publishTime = `9:0${i * 6} AM`;
    const statusClass = `status-${post.status || 'queued'}`;
    const statusLabel = { queued: '🕐 Queued', published: '✅ Live', failed: '❌ Failed', publishing: '⚡ Publishing' }[post.status] || post.status;
    return `
    <div class="queue-item ${post.status === 'published' ? 'published' : ''}">
      <div class="queue-time">
        <span class="queue-time-main">9:00</span>
        <span class="queue-time-sub">AM IST</span>
      </div>
      <div class="queue-divider"></div>
      <div class="queue-content">
        <div class="queue-title">${escapeHtml((post.headline || '').slice(0, 70))}</div>
        <div class="queue-tags">
          <span class="queue-tag">📸 ${post.image_paths?.length || 0} slides</span>
          <span class="queue-tag">📰 ${escapeHtml(post.source || '')}</span>
          <span class="queue-tag">⚡ Score: ${post.virality_score || 0}</span>
        </div>
      </div>
      <div class="queue-status-lg">
        <div class="status-chip ${statusClass}" style="position:relative;top:auto;left:auto;">${statusLabel}</div>
      </div>
    </div>`;
  }).join('');
}

// ── Carousel Modal ─────────────────────────────────────
function openCarousel(postId) {
  const post = currentPosts.find(p => p.id === postId);
  if (!post) return;

  currentModalPost = post;
  currentSlide = 0;

  document.getElementById('modal-title').textContent = (post.headline || 'Carousel Preview').slice(0, 60);
  document.getElementById('modal-caption').textContent = post.caption || '';

  // Hashtags
  const hashtagsEl = document.getElementById('modal-hashtags');
  const tags = post.hashtags || [];
  hashtagsEl.innerHTML = tags.slice(0, 20).map(t =>
    `<span class="hashtag-chip">#${escapeHtml(t.replace('#', ''))}</span>`
  ).join('');

  // Dots
  const dotsEl = document.getElementById('carousel-dots');
  const imgs = post.image_urls || [];
  dotsEl.innerHTML = imgs.map((_, i) =>
    `<div class="carousel-dot ${i === 0 ? 'active' : ''}" onclick="goToSlide(${i})"></div>`
  ).join('');

  showSlide(0);

  document.getElementById('carousel-modal').classList.add('open');
}

function showSlide(idx) {
  const post = currentModalPost;
  if (!post) return;
  const imgs = post.image_urls || [];
  if (!imgs.length) return;

  idx = Math.max(0, Math.min(idx, imgs.length - 1));
  currentSlide = idx;

  const imgEl = document.getElementById('carousel-slide-img');
  if (imgEl) imgEl.src = API + imgs[idx];

  document.querySelectorAll('.carousel-dot').forEach((d, i) => {
    d.classList.toggle('active', i === idx);
  });
}

function prevSlide() { showSlide(currentSlide - 1); }
function nextSlide() { showSlide(currentSlide + 1); }
function goToSlide(i) { showSlide(i); }

function closeModal() {
  document.getElementById('carousel-modal').classList.remove('open');
  currentModalPost = null;
}

async function publishModalPost() {
  if (!currentModalPost) return;
  await publishPost(currentModalPost.id);
  closeModal();
}

// ── Actions ────────────────────────────────────────────
async function runResearch() {
  try {
    showToast('🔍 Starting AI news research...', 'info');
    await apiFetch('/api/run-research', { method: 'POST' });
    showToast('Research pipeline started! 📡', 'success');
    setTimeout(() => { loadStatus(); loadNews(); loadPosts(); }, 2000);
  } catch (e) {
    showToast('Failed to start research: ' + e.message, 'error');
  }
}

async function runPublish() {
  try {
    showToast('📤 Starting Instagram publishing...', 'info');
    await apiFetch('/api/run-publish', { method: 'POST' });
    showToast('Publishing pipeline started!', 'success');
    setTimeout(() => { loadStatus(); loadPosts(); }, 3000);
  } catch (e) {
    showToast('Failed to start publishing: ' + e.message, 'error');
  }
}

async function runAll() {
  try {
    const btn = document.getElementById('btn-run-now');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Running...'; }
    showToast('🚀 Full pipeline started! Research → Generate → Publish', 'info');
    await apiFetch('/api/run-all', { method: 'POST' });
    setTimeout(() => { loadStatus(); loadNews(); loadPosts(); }, 3000);
  } catch (e) {
    showToast('Pipeline error: ' + e.message, 'error');
    const btn = document.getElementById('btn-run-now');
    if (btn) { btn.disabled = false; btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 3l14 9-14 9V3z" fill="currentColor"/></svg> Run Now'; }
  }
}

async function publishPost(postId, btnEl) {
  try {
    if (btnEl) btnEl.disabled = true;
    showToast(`📤 Publishing post #${postId}...`, 'info');
    await apiFetch(`/api/publish/${postId}`, { method: 'POST' });
    showToast('Post sent to Instagram! ✅', 'success');
    setTimeout(() => loadPosts(), 3000);
  } catch (e) {
    showToast('Publish failed: ' + e.message, 'error');
    if (btnEl) btnEl.disabled = false;
  }
}

async function testInstagram() {
  const resultEl = document.getElementById('ig-test-result');
  if (resultEl) { resultEl.className = 'config-test-result'; resultEl.textContent = 'Testing connection...'; resultEl.style.display = 'block'; }

  try {
    const data = await apiFetch('/api/test-instagram', { method: 'POST' });
    if (data.success) {
      const msg = `✅ Connected as @${data.username} · ${data.followers?.toLocaleString()} followers · ${data.posts} posts`;
      if (resultEl) { resultEl.className = 'config-test-result success'; resultEl.textContent = msg; }
      const usernameEl = document.getElementById('ig-username');
      const statusEl = document.getElementById('ig-status-text');
      if (usernameEl) usernameEl.textContent = `@${data.username}`;
      if (statusEl) statusEl.textContent = `${data.followers?.toLocaleString()} followers`;
      showToast('Instagram connected! ✅', 'success');
    } else {
      if (resultEl) { resultEl.className = 'config-test-result error'; resultEl.textContent = `❌ ${data.error || 'Connection failed'}`; }
      showToast('Connection failed: ' + (data.error || 'Unknown error'), 'error');
    }
  } catch (e) {
    if (resultEl) { resultEl.className = 'config-test-result error'; resultEl.textContent = `❌ ${e.message}`; }
    showToast('Test failed: ' + e.message, 'error');
  }
}

// ── Config ─────────────────────────────────────────────
async function loadConfig() {
  try {
    const data = await apiFetch('/api/config');
    setInputVal('cfg-ig-user', data.instagram_username);
    setInputVal('cfg-ig-pass', '');
    setInputVal('cfg-gemini', '');
    setInputVal('cfg-newsapi', '');
    setInputVal('cfg-research-hour', data.research_hour);
    setInputVal('cfg-research-min', String(data.research_minute).padStart(2, '0'));
    setInputVal('cfg-publish-hour', data.publish_hour);
    setInputVal('cfg-publish-min', String(data.publish_minute).padStart(2, '0'));
    updateAmPm('ampm-research', data.research_hour);
    updateAmPm('ampm-publish', data.publish_hour);
  } catch (e) { /* Backend offline */ }
}

function updateAmPm(id, hour) {
  const el = document.getElementById(id);
  if (el) el.textContent = hour < 12 ? 'AM' : 'PM';
}

function setInputVal(id, val) {
  const el = document.getElementById(id);
  if (el && val !== undefined && val !== null) el.value = val;
}

document.addEventListener('change', e => {
  if (e.target.id === 'cfg-research-hour') updateAmPm('ampm-research', parseInt(e.target.value));
  if (e.target.id === 'cfg-publish-hour') updateAmPm('ampm-publish', parseInt(e.target.value));
});

async function saveConfig() {
  const body = {};
  const igUser = document.getElementById('cfg-ig-user')?.value?.trim();
  const igPass = document.getElementById('cfg-ig-pass')?.value;
  const gemini = document.getElementById('cfg-gemini')?.value?.trim();
  const newsapi = document.getElementById('cfg-newsapi')?.value?.trim();

  if (igUser) body.instagram_username = igUser;
  if (igPass) body.instagram_password = igPass;
  if (gemini) body.gemini_api_key = gemini;
  if (newsapi) body.news_api_key = newsapi;

  try {
    await apiFetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    showToast('Configuration saved! ✅', 'success');
    loadStatus();
  } catch (e) {
    showToast('Save failed: ' + e.message, 'error');
  }
}

async function saveSchedule() {
  const body = {
    research_hour: parseInt(document.getElementById('cfg-research-hour')?.value || 8),
    research_minute: parseInt(document.getElementById('cfg-research-min')?.value || 0),
    publish_hour: parseInt(document.getElementById('cfg-publish-hour')?.value || 9),
    publish_minute: parseInt(document.getElementById('cfg-publish-min')?.value || 0),
  };

  try {
    await apiFetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    showToast(`Schedule updated! Research: ${body.research_hour}:${String(body.research_minute).padStart(2,'0')} / Publish: ${body.publish_hour}:${String(body.publish_minute).padStart(2,'0')} IST ✅`, 'success');
  } catch (e) {
    showToast('Failed to save schedule: ' + e.message, 'error');
  }
}

// ── Analytics ──────────────────────────────────────────
async function loadAnalytics() {
  try {
    const data = await apiFetch('/api/analytics');
    const analytics = data.analytics || [];
    renderAnalyticsTable(analytics);
    updateCharts(analytics);
  } catch (e) {
    console.error('Analytics load failed:', e);
  }
}

function renderAnalyticsTable(analytics) {
  const container = document.getElementById('analytics-table');
  if (!container) return;

  if (!analytics.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Analytics will appear after posts are published</p></div>`;
    return;
  }

  container.innerHTML = `<table>
    <thead><tr>
      <th>Date</th><th>Headline</th><th>Likes</th><th>Comments</th>
      <th>Saves</th><th>Reach</th><th>Engagement</th>
    </tr></thead>
    <tbody>
      ${analytics.map(a => `<tr>
        <td>${a.run_date || '—'}</td>
        <td>${escapeHtml((a.headline || '').slice(0, 50))}</td>
        <td>❤️ ${a.likes || 0}</td>
        <td>💬 ${a.comments || 0}</td>
        <td>🔖 ${a.saves || 0}</td>
        <td>👁 ${a.reach || 0}</td>
        <td>${a.engagement_rate || 0}%</td>
      </tr>`).join('')}
    </tbody>
  </table>`;
}

function initCharts() {
  const ctx1 = document.getElementById('engagementChart')?.getContext('2d');
  const ctx2 = document.getElementById('performanceChart')?.getContext('2d');
  if (!ctx1 || !ctx2) return;

  const chartDefaults = {
    responsive: true,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } } },
    },
    scales: {
      x: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.04)' } },
    },
  };

  engagementChart = new Chart(ctx1, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Likes', data: [], borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.1)',
        fill: true, tension: 0.4, pointBackgroundColor: '#6366f1',
      }, {
        label: 'Saves', data: [], borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.1)',
        fill: true, tension: 0.4, pointBackgroundColor: '#22d3ee',
      }],
    },
    options: { ...chartDefaults },
  });

  performanceChart = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: 'Reach', data: [],
        backgroundColor: 'rgba(139,92,246,0.6)',
        borderColor: '#8b5cf6', borderWidth: 2, borderRadius: 8,
      }],
    },
    options: { ...chartDefaults },
  });
}

function updateCharts(analytics) {
  if (!engagementChart || !performanceChart) return;
  const labels = analytics.slice(-14).map(a => a.run_date?.slice(5) || '');
  const likes = analytics.slice(-14).map(a => a.likes || 0);
  const saves = analytics.slice(-14).map(a => a.saves || 0);
  const reach = analytics.slice(-14).map(a => a.reach || 0);

  engagementChart.data.labels = labels;
  engagementChart.data.datasets[0].data = likes;
  engagementChart.data.datasets[1].data = saves;
  engagementChart.update();

  performanceChart.data.labels = labels;
  performanceChart.data.datasets[0].data = reach;
  performanceChart.update();
}

// ── Logs ───────────────────────────────────────────────
async function loadLogs() {
  try {
    const data = await apiFetch('/api/logs?limit=100');
    const logs = data.live_logs || [];
    renderLogs(logs);
  } catch (e) { /* silent */ }
}

function renderLogs(logs) {
  const feed = document.getElementById('log-feed');
  if (!feed) return;

  if (!logs.length) {
    feed.innerHTML = '<div class="log-empty">No log entries yet. Run the pipeline to see activity.</div>';
    return;
  }

  feed.innerHTML = logs.slice().reverse().map(entry => {
    const level = entry.includes('error') || entry.includes('❌') ? 'error'
      : entry.includes('success') || entry.includes('✅') || entry.includes('✓') ? 'success'
      : entry.includes('warning') || entry.includes('⚠') ? 'warning' : 'info';

    // Parse timestamp if available
    const match = entry.match(/^\[(\d{2}:\d{2}:\d{2})\] (.*)/);
    if (match) {
      return `<div class="log-entry log-${level}">
        <span class="log-time">[${match[1]}]</span> <span class="log-msg">${escapeHtml(match[2])}</span>
      </div>`;
    }
    return `<div class="log-entry log-${level}"><span class="log-msg">${escapeHtml(entry)}</span></div>`;
  }).join('');
}

function clearLogs() {
  const feed = document.getElementById('log-feed');
  if (feed) feed.innerHTML = '<div class="log-empty">Logs cleared.</div>';
}

// ── Toast ──────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: '✅', error: '❌', info: '💬', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span> ${escapeHtml(message)}`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(60px)';
    toast.style.transition = '300ms ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ── Utils ──────────────────────────────────────────────
function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  return escapeHtml(str || '');
}

// Keyboard shortcut to close modal
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if (e.key === 'ArrowLeft') prevSlide();
  if (e.key === 'ArrowRight') nextSlide();
});
