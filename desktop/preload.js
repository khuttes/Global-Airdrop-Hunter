const { contextBridge, ipcRenderer } = require('electron');

const validApiConfigKeys = ['baseUrl', 'token'];

contextBridge.exposeInMainWorld('api', {
  getConfig: () => ipcRenderer.invoke('get-api-config'),

  async request(endpoint, options = {}) {
    const config = await this.getConfig();
    const url = `${config.baseUrl}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      'X-Local-API-Token': config.token,
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

      return response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw err;
    }
  },

  health: () => this.request('/api/v1/health'),

  dashboard: () => this.request('/api/v1/dashboard'),

  campaigns: {
    list: (params = {}) => {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const query = searchParams.toString();
      return this.request(`/api/v1/campaigns${query ? `?${query}` : ''}`);
    },
    get: (id) => this.request(`/api/v1/campaigns/${encodeURIComponent(id)}`),
    save: (id) => this.request(`/api/v1/campaigns/${encodeURIComponent(id)}/save`, {
      method: 'POST',
    }),
  },

  discovery: {
    scan: (sources) => this.request('/api/v1/discovery/scans', {
      method: 'POST',
      body: { sources },
    }),
  },

  backup: {
    create: () => this.request('/api/v1/backup', { method: 'POST' }),
  },
});

contextBridge.exposeInMainWorld('shell', {
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
});

contextBridge.exposeInMainWorld('app', {
  getVersion: () => ipcRenderer.invoke('get-app-version'),
});

contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: {
    invoke: (channel, ...args) => {
      const allowedChannels = ['get-api-config', 'open-external', 'get-app-version'];
      if (allowedChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args);
      }
      throw new Error(`Unauthorized IPC channel: ${channel}`);
    },
  },
});

console.log('[Preload] Secure context bridge initialized');