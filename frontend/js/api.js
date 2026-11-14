class APIClient {
  constructor() {
    this.baseUrl = null;
    this.token = null;
    this.initialized = false;
    this.cache = new Map(); // In-memory cache
    this.cacheTTL = 5 * 60 * 1000; // 5 minutes
    this.offlineMode = false;
    this.maxCacheAge = 24 * 60 * 60 * 1000; // 24 hours max cache age
  }

  async init() {
    if (this.initialized) return;
    
    // Try Electron IPC first (for Electron app mode)
    if (window.api && typeof window.api.getConfig === 'function') {
      try {
        const config = await window.api.getConfig();
        this.baseUrl = config.baseUrl;
        this.token = config.token;
        this.initialized = true;
        console.log('[APIClient] Initialized via Electron IPC');
        return;
      } catch (err) {
        console.warn('[APIClient] Electron IPC failed, falling back to browser mode:', err);
      }
    }

    // Browser mode fallback: read from localStorage (set by launch script)
    try {
      const storedConfig = localStorage.getItem('gah_api_config');
      if (storedConfig) {
        const config = JSON.parse(storedConfig);
        if (config.baseUrl && config.token) {
          this.baseUrl = config.baseUrl;
          this.token = config.token;
          this.initialized = true;
          console.log('[APIClient] Initialized via localStorage (browser mode)');
          return;
        }
      }
    } catch (err) {
      console.warn('[APIClient] localStorage read failed:', err);
    }

    // Last resort: try to get base URL from meta tag (for cases where token is in localStorage separately)
    try {
      const baseUrlMeta = document.querySelector('meta[name="gah-api-base-url"]');
      const tokenMeta = document.querySelector('meta[name="gah-api-token"]');
      if (baseUrlMeta && tokenMeta) {
        this.baseUrl = baseUrlMeta.content;
        this.token = tokenMeta.content;
        this.initialized = true;
        console.log('[APIClient] Initialized via meta tags');
        return;
      }
    } catch (err) {
      console.warn('[APIClient] meta tag read failed:', err);
    }

    throw new Error('Failed to initialize API client: no valid configuration source found. Ensure you are running via the launcher script.');
  }

  _getCacheKey(endpoint, options) {
    return `${options.method || 'GET'}:${endpoint}:${JSON.stringify(options.body || {})}`;
  }

  _getFromCache(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    const age = Date.now() - cached.timestamp;
    if (age > this.maxCacheAge) {
      this.cache.delete(key);
      return null;
    }
    
    return cached;
  }

  _setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  _isStale(cached) {
    const age = Date.now() - cached.timestamp;
    return age > this.cacheTTL;
  }

  async request(endpoint, options = {}) {
    await this.init();
    const url = `${this.baseUrl}${endpoint}`;
    const cacheKey = this._getCacheKey(endpoint, options);
    const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method || 'GET');
    
    // Check cache for GET requests
    const cached = this._getFromCache(cacheKey);
    if (cached && !isMutation) {
      // Return cached data immediately, refresh in background if stale
      if (this._isStale(cached)) {
        this._refreshInBackground(endpoint, options, cacheKey);
      }
      return { ...cached.data, _stale: this._isStale(cached), _cached: true };
    }

    const headers = {
      'Content-Type': 'application/json',
      'X-Local-API-Token': this.token,
      ...options.headers,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(url, {
        method: options.method || 'GET',
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error?.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Mark as online
      this.offlineMode = false;
      window.dispatchEvent(new CustomEvent('api-status', { detail: { online: true } }));
      
      // Cache successful GET responses
      if (!isMutation) {
        this._setCache(cacheKey, data);
      }
      
      return data;
    } catch (err) {
      clearTimeout(timeoutId);
      
      if (err.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      
      // Network error - try to serve stale cache
      if (cached && !isMutation) {
        this.offlineMode = true;
        window.dispatchEvent(new CustomEvent('api-status', { detail: { online: false } }));
        console.warn(`[APIClient] Network error, serving stale cache for ${endpoint}:`, err.message);
        return { ...cached.data, _stale: true, _cached: true, _offline: true };
      }
      
      throw err;
    }
  }

  _refreshInBackground(endpoint, options, cacheKey) {
    // Fire and forget background refresh
    this.request(endpoint, options).then(data => {
      this._setCache(cacheKey, data);
    }).catch(() => {
      // Ignore background refresh errors
    });
  }

  async health() {
    return this.request('/api/v1/health');
  }

  async dashboard() {
    return this.request('/api/v1/dashboard');
  }

  async campaigns(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    return this.request(`/api/v1/campaigns${query ? `?${query}` : ''}`);
  }

  async campaign(id) {
    return this.request(`/api/v1/campaigns/${encodeURIComponent(id)}`);
  }

  async scan(sources) {
    return this.request('/api/v1/discovery/scans', {
      method: 'POST',
      body: { sources },
    });
  }

  async saveCampaign(id) {
    return this.request(`/api/v1/campaigns/${encodeURIComponent(id)}/save`, {
      method: 'POST',
    });
  }

  async backup() {
    return this.request('/api/v1/backup', { method: 'POST' });
  }

  async sources() {
    return this.request('/api/v1/sources');
  }

  async sourceHealth(sourceId) {
    return this.request(`/api/v1/sources/${encodeURIComponent(sourceId)}/health`);
  }

  // Tracking methods
  async trackedCampaigns() {
    return this.request('/api/v1/eligibility/tracked');
  }

  async trackCampaign(campaignId) {
    return this.request(`/api/v1/eligibility/campaigns/${encodeURIComponent(campaignId)}/track`, {
      method: 'POST',
    });
  }

  async updateProgress(campaignId, data) {
    return this.request(`/api/v1/eligibility/campaigns/${encodeURIComponent(campaignId)}/progress`, {
      method: 'POST',
      body: data,
    });
  }

  async notificationPrefs(campaignId) {
    return this.request(`/api/v1/eligibility/campaigns/${encodeURIComponent(campaignId)}/notification-prefs`);
  }

  async updateNotificationPrefs(campaignId, data) {
    return this.request(`/api/v1/eligibility/campaigns/${encodeURIComponent(campaignId)}/notification-prefs`, {
      method: 'PATCH',
      body: data,
    });
  }

  // Offline support methods
  isOffline() {
    return this.offlineMode;
  }

  clearCache() {
    this.cache.clear();
  }

  getCacheStats() {
    return {
      entries: this.cache.size,
      offlineMode: this.offlineMode,
    };
  }
}

window.apiClient = new APIClient();