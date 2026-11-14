class App {
  constructor() {
    this.initialized = false;
    this.backendConnected = false;
  }

  async init() {
    if (this.initialized) return;

    try {
      this.setupEventListeners();
      await this.checkBackendHealth();
      await this.loadAppVersion();
      this.initialized = true;
      this.showToast('Application initialized', 'success');
    } catch (err) {
      console.error('App initialization failed:', err);
      this.showToast(`Initialization failed: ${err.message}`, 'error');
      this.setBackendStatus('error', 'Failed to connect');
    }
  }

  setupEventListeners() {
    document.getElementById('refresh-btn')?.addEventListener('click', () => this.refresh());
    document.getElementById('scan-btn')?.addEventListener('click', () => this.startScan());
    document.getElementById('backup-btn')?.addEventListener('click', () => this.createBackup());
    document.getElementById('diagnostics-btn')?.addEventListener('click', () => this.runDiagnostics());
    document.getElementById('setting-theme')?.addEventListener('change', (e) => this.setTheme(e.target.value));

    document.getElementById('filter-type')?.addEventListener('change', () => this.loadCampaigns());
    document.getElementById('filter-network')?.addEventListener('change', () => this.loadCampaigns());
    document.getElementById('filter-status')?.addEventListener('change', () => this.loadCampaigns());
    document.getElementById('filter-risk')?.addEventListener('change', () => this.loadCampaigns());

    // Discovery module events
    document.getElementById('discovery-scan-btn')?.addEventListener('click', () => this.startDiscoveryScan());
    document.getElementById('source-select-all')?.addEventListener('change', (e) => this.toggleAllSources(e.target.checked));

    document.getElementById('global-search')?.addEventListener('input', (e) => this.handleSearch(e.target.value));
    document.getElementById('global-search')?.addEventListener('focus', () => this.showSearchResults());
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-container')) {
        this.hideSearchResults();
      }
    });

    document.getElementById('modal-close')?.addEventListener('click', () => this.closeModal());
    document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) this.closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeModal();
    });

    // Listen for module changes
    window.addEventListener('module-change', (e) => {
      if (e.detail.module === 'discovery') {
        this.loadSources();
      }
      if (e.detail.module === 'tracking') {
        this.loadTracking();
      }
    });

    window.navigation.init();
  }

  async checkBackendHealth() {
    this.setBackendStatus('connecting', 'Connecting...');
    try {
      const health = await window.apiClient.health();
      this.backendConnected = true;
      this.setBackendStatus('connected', 'Connected');
      return health;
    } catch (err) {
      this.backendConnected = false;
      this.setBackendStatus('error', 'Disconnected');
      throw err;
    }
  }

  setBackendStatus(status, text) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    if (indicator) {
      indicator.className = 'status-indicator ' + status;
    }
    if (statusText) {
      statusText.textContent = text;
    }
  }

  async loadAppVersion() {
    try {
      const version = await window.app.getVersion();
      const versionEl = document.getElementById('app-version');
      const settingVersion = document.getElementById('setting-version');
      if (versionEl) versionEl.textContent = `v${version}`;
      if (settingVersion) settingVersion.textContent = version;

      const electronVersion = document.getElementById('setting-electron-version');
      const nodeVersion = document.getElementById('setting-node-version');
      if (electronVersion) electronVersion.textContent = process.versions.electron || 'Unknown';
      if (nodeVersion) nodeVersion.textContent = process.versions.node || 'Unknown';
    } catch (err) {
      console.error('Failed to load app version:', err);
    }
  }

  async refresh() {
    if (!this.backendConnected) {
      await this.checkBackendHealth();
      if (!this.backendConnected) return;
    }

    this.showToast('Refreshing data...', 'info');
    try {
      await this.loadDashboard();
      await this.loadCampaigns();
      this.showToast('Data refreshed', 'success');
    } catch (err) {
      this.showToast(`Refresh failed: ${err.message}`, 'error');
    }
  }

  async loadDashboard() {
    try {
      const data = await window.apiClient.dashboard();
      this.updateDashboardStats(data);
      this.updateRecentCampaigns(data.recent_campaigns || []);
      this.updateDeadlines(data.upcoming_deadlines || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  }

  updateDashboardStats(data) {
    const stats = {
      'stat-campaigns': data.total_campaigns || 0,
      'stat-tracking': data.tracked_campaigns || 0,
      'stat-verified': data.verified_campaigns || 0,
      'stat-high-risk': data.high_risk_campaigns || 0,
    };

    Object.entries(stats).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    });
  }

  updateRecentCampaigns(campaigns) {
    const tbody = document.getElementById('recent-campaigns-body');
    if (!tbody) return;

    if (!campaigns.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="6">No campaigns discovered yet. Click "Scan" to start discovery.</td></tr>';
      return;
    }

    tbody.innerHTML = campaigns.map(c => `
      <tr>
        <td class="cell-name">
          <div class="name-main">${this.escapeHtml(c.name || 'Unknown')}</div>
          <div class="name-meta">${this.escapeHtml(c.project || '')}</div>
        </td>
        <td class="cell-type"><span class="badge badge-${c.type || 'airdrop'}">${this.escapeHtml(c.type || 'Airdrop')}</span></td>
        <td class="cell-network">${this.escapeHtml(c.network || 'N/A')}</td>
        <td class="cell-status"><span class="badge badge-${c.status || 'active'}">${this.escapeHtml(c.status || 'Active')}</span></td>
        <td class="cell-risk"><span class="badge badge-${c.risk_level || 'medium'}">${this.escapeHtml(c.risk_level || 'Medium')}</span></td>
        <td class="cell-date">${this.formatDate(c.discovered_at)}</td>
      </tr>
    `).join('');
  }

  updateDeadlines(deadlines) {
    const container = document.getElementById('deadline-list');
    if (!container) return;

    if (!deadlines.length) {
      container.innerHTML = `
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <p>No upcoming deadlines</p>
        </div>
      `;
      return;
    }

    container.innerHTML = deadlines.map(d => `
      <div class="deadline-item">
        <div class="deadline-info">
          <div class="deadline-name">${this.escapeHtml(d.name || 'Unknown')}</div>
          <div class="deadline-meta">
            <span class="deadline-date ${this.getUrgencyClass(d.days_remaining)}">${this.formatDate(d.deadline)}</span>
            <span>${d.days_remaining !== undefined ? `${d.days_remaining} days` : ''}</span>
          </div>
        </div>
        <span class="badge badge-${d.risk_level || 'medium'}">${this.escapeHtml(d.risk_level || 'Medium')}</span>
      </div>
    `).join('');
  }

  getUrgencyClass(days) {
    if (days === undefined) return '';
    if (days <= 3) return 'urgent';
    if (days <= 7) return 'warning';
    return '';
  }

  async loadCampaigns() {
    try {
      const filters = {
        page: 1,
        page_size: 50,
        type: document.getElementById('filter-type')?.value || undefined,
        network: document.getElementById('filter-network')?.value || undefined,
        status: document.getElementById('filter-status')?.value || undefined,
        risk_level: document.getElementById('filter-risk')?.value || undefined,
      };
      const data = await window.apiClient.campaigns(filters);
      this.updateCampaignsTable(data.items || []);
      this.updatePagination(data);
      this.updateNetworkFilter(data.items || []);
    } catch (err) {
      console.error('Failed to load campaigns:', err);
    }
  }

  updateCampaignsTable(campaigns) {
    const tbody = document.getElementById('campaigns-body');
    if (!tbody) return;

    if (!campaigns.length) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="9">No campaigns found. Start a discovery scan.</td></tr>';
      return;
    }

    tbody.innerHTML = campaigns.map(c => `
      <tr data-id="${this.escapeHtml(c.id)}" style="cursor: pointer;">
        <td><input type="checkbox" class="campaign-select" value="${this.escapeHtml(c.id)}"></td>
        <td class="cell-name">
          <div class="name-main">${this.escapeHtml(c.name || 'Unknown')}</div>
          <div class="name-meta">${this.escapeHtml(c.project || '')}</div>
        </td>
        <td class="cell-type"><span class="badge badge-${c.type || 'airdrop'}">${this.escapeHtml(c.type || 'Airdrop')}</span></td>
        <td class="cell-network">${this.escapeHtml(c.network || 'N/A')}</td>
        <td class="cell-status"><span class="badge badge-${c.status || 'active'}">${this.escapeHtml(c.status || 'Active')}</span></td>
        <td class="cell-verification"><span class="badge badge-${c.verification_status || 'unverified'}">${this.escapeHtml(c.verification_status || 'Unverified')}</span></td>
        <td class="cell-risk"><span class="badge badge-${c.risk_level || 'medium'}">${this.escapeHtml(c.risk_level || 'Medium')}</span></td>
        <td class="cell-date">${this.formatDate(c.deadline)}</td>
        <td class="cell-date">${this.formatDate(c.discovered_at)}</td>
      </tr>
    `).join('');

    // Add click handlers for row click (excluding checkbox)
    tbody.querySelectorAll('tr[data-id]').forEach(row => {
      row.addEventListener('click', (e) => {
        if (e.target.type !== 'checkbox') {
          this.showCampaignDetail(row.dataset.id);
        }
      });
    });
  }

  updatePagination(data) {
    const container = document.getElementById('campaigns-pagination');
    if (!container) return;

    const page = data.page || 1;
    const totalPages = data.total_pages || 1;
    const totalItems = data.total_items || 0;

    if (totalPages <= 1) {
      container.innerHTML = `<span class="page-info">Showing ${totalItems} campaigns</span>`;
      return;
    }

    let html = `<span class="page-info">Page ${page} of ${totalPages} (${totalItems} total)</span>`;
    html += `<button class="btn btn-ghost btn-sm" ${page === 1 ? 'disabled' : ''} data-page="${page - 1}">Prev</button>`;

    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
        html += `<button class="btn btn-ghost btn-sm ${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
      } else if (i === page - 2 || i === page + 2) {
        html += `<span class="page-info">...</span>`;
      }
    }

    html += `<button class="btn btn-ghost btn-sm" ${page === totalPages ? 'disabled' : ''} data-page="${page + 1}">Next</button>`;
    container.innerHTML = html;

    container.querySelectorAll('button[data-page]').forEach(btn => {
      btn.addEventListener('click', () => this.loadCampaignsPage(parseInt(btn.dataset.page)));
    });
  }

  updateNetworkFilter(campaigns) {
    const select = document.getElementById('filter-network');
    if (!select) return;

    const networks = new Set();
    campaigns.forEach(c => {
      if (c.network) networks.add(c.network);
    });

    const currentValue = select.value;
    select.innerHTML = '<option value="">All Networks</option>';
    Array.from(networks).sort().forEach(network => {
      const option = document.createElement('option');
      option.value = network;
      option.textContent = network;
      select.appendChild(option);
    });

    if (networks.has(currentValue)) {
      select.value = currentValue;
    }
  }

  async loadCampaignsPage(page) {
    try {
      const filters = {
        page,
        page_size: 50,
        type: document.getElementById('filter-type')?.value || undefined,
        network: document.getElementById('filter-network')?.value || undefined,
        status: document.getElementById('filter-status')?.value || undefined,
        risk_level: document.getElementById('filter-risk')?.value || undefined,
      };
      const data = await window.apiClient.campaigns(filters);
      this.updateCampaignsTable(data.items || []);
      this.updatePagination(data);
    } catch (err) {
      console.error('Failed to load campaigns page:', err);
    }
  }

  async startScan() {
    if (!this.backendConnected) {
      this.showToast('Backend not connected', 'error');
      return;
    }

    this.showToast('Starting discovery scan...', 'info');
    try {
      const result = await window.apiClient.scan([]);
      this.showToast(`Scan completed: ${result.campaigns_found || 0} campaigns found`, 'success');
      await this.refresh();
    } catch (err) {
      this.showToast(`Scan failed: ${err.message}`, 'error');
    }
  }

  async loadSources() {
    try {
      const sources = await window.apiClient.sources();
      this.renderSources(sources);
    } catch (err) {
      console.error('Failed to load sources:', err);
    }
  }

  renderSources(sources) {
    const container = document.getElementById('source-list');
    if (!container) return;

    if (!sources.length) {
      container.innerHTML = `
        <div class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p>No sources configured. Add sources to start discovery.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = sources.map(s => `
      <div class="source-item">
        <div class="source-info">
          <div class="source-header">
            <input type="checkbox" class="source-select" value="${this.escapeHtml(s.id)}" ${s.enabled ? 'checked' : ''}>
            <span class="source-name">${this.escapeHtml(s.name)}</span>
            <span class="badge badge-${s.type}">${this.escapeHtml(s.type)}</span>
            <span class="source-status ${s.enabled ? 'enabled' : 'disabled'}">${s.enabled ? 'Enabled' : 'Disabled'}</span>
          </div>
          <div class="source-meta">
            <span>URL: ${this.escapeHtml(s.base_url)}</span>
            <span>Rate limit: ${s.rate_limit}/min</span>
            <span>Timeout: ${s.timeout}s</span>
            ${s.last_health_check ? `<span>Last check: ${this.formatDate(s.last_health_check)}</span>` : ''}
            ${s.last_scan ? `<span>Last scan: ${this.formatDate(s.last_scan)}</span>` : ''}
            <span>Scans: ${s.total_scans}</span>
            <span>Records: ${s.total_records}</span>
          </div>
        </div>
        <div class="source-actions">
          <button class="btn btn-ghost btn-sm source-health-btn" data-source-id="${this.escapeHtml(s.id)}" ${!s.enabled ? 'disabled' : ''}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            Check
          </button>
        </div>
      </div>
    `).join('');

    // Add health check handlers
    container.querySelectorAll('.source-health-btn').forEach(btn => {
      btn.addEventListener('click', () => this.checkSourceHealth(btn.dataset.sourceId));
    });

    // Add source selection handlers
    container.querySelectorAll('.source-select').forEach(checkbox => {
      checkbox.addEventListener('change', () => this.updateSourceSelection());
    });
  }

  updateSourceSelection() {
    const checkboxes = document.querySelectorAll('.source-select');
    const selectAll = document.getElementById('source-select-all');
    const checked = document.querySelectorAll('.source-select:checked');
    if (selectAll) {
      selectAll.checked = checkboxes.length === checked.length;
      selectAll.indeterminate = checked.length > 0 && checked.length < checkboxes.length;
    }
  }

  toggleAllSources(checked) {
    document.querySelectorAll('.source-select').forEach(cb => {
      cb.checked = checked;
    });
    this.updateSourceSelection();
  }

  async loadTracking() {
    try {
      const tracked = await window.apiClient.trackedCampaigns();
      this.renderTracking(tracked);
    } catch (err) {
      console.error('Failed to load tracking:', err);
    }
  }

  renderTracking(campaigns) {
    const container = document.getElementById('module-tracking');
    if (!container) return;

    const trackingPanel = container.querySelector('.tracking-panel');
    if (!trackingPanel) return;

    if (!campaigns || campaigns.length === 0) {
      trackingPanel.innerHTML = `
        <div class="card">
          <header class="card-header">
            <h2>Tracked Campaigns</h2>
          </header>
          <div class="card-body">
            <div class="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <p>No campaigns tracked yet. Add campaigns from the Campaigns module.</p>
            </div>
          </div>
        </div>
      `;
      return;
    }

    trackingPanel.innerHTML = `
      <div class="card">
        <header class="card-header">
          <h2>Tracked Campaigns (${campaigns.length})</h2>
        </header>
        <div class="card-body">
          <div class="tracking-table-container">
            <table class="tracking-table" role="grid">
              <thead>
                <tr>
                  <th scope="col">Campaign</th>
                  <th scope="col">Type</th>
                  <th scope="col">Network</th>
                  <th scope="col">Progress</th>
                  <th scope="col">Next Deadline</th>
                  <th scope="col">Status</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${campaigns.map(c => `
                  <tr data-id="${this.escapeHtml(c.id)}">
                    <td class="cell-name">
                      <div class="name-main">${this.escapeHtml(c.name || 'Unknown')}</div>
                      <div class="name-meta">${this.escapeHtml(c.project || '')}</div>
                    </td>
                    <td class="cell-type"><span class="badge badge-${c.type || 'airdrop'}">${this.escapeHtml(c.type || 'Airdrop')}</span></td>
                    <td class="cell-network">${this.escapeHtml(c.network || 'N/A')}</td>
                    <td class="cell-progress">
                      <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${c.progress_percentage || 0}%"></div>
                      </div>
                      <span class="progress-text">${c.completed_requirements || 0}/${c.total_requirements || 0}</span>
                    </td>
                    <td class="cell-deadline">${c.next_deadline ? this.formatDate(c.next_deadline) : 'No deadline'}</td>
                    <td class="cell-status"><span class="badge badge-${c.status || 'active'}">${this.escapeHtml(c.status || 'Active')}</span></td>
                    <td class="cell-actions">
                      <button class="btn btn-ghost btn-sm" onclick="window.app.showCampaignDetail('${this.escapeHtml(c.id)}')" aria-label="View details">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button class="btn btn-ghost btn-sm" onclick="window.app.updateProgress('${this.escapeHtml(c.id)}')" aria-label="Update progress">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    // Add click handlers for row click
    trackingPanel.querySelectorAll('tbody tr[data-id]').forEach(row => {
      row.addEventListener('click', (e) => {
        if (!e.target.closest('button')) {
          this.showCampaignDetail(row.dataset.id);
        }
      });
    });
  }

  async checkSourceHealth(sourceId) {
    try {
      this.showToast('Checking source health...', 'info');
      const result = await window.apiClient.sourceHealth(sourceId);
      if (result.healthy) {
        this.showToast('Source is healthy', 'success');
      } else {
        this.showToast('Source health check failed', 'error');
      }
      // Reload sources to update status
      await this.loadSources();
    } catch (err) {
      this.showToast(`Health check failed: ${err.message}`, 'error');
    }
  }

  async startDiscoveryScan() {
    if (!this.backendConnected) {
      this.showToast('Backend not connected', 'error');
      return;
    }

    const selectedSources = Array.from(document.querySelectorAll('.source-select:checked')).map(cb => cb.value);
    if (selectedSources.length === 0) {
      this.showToast('Please select at least one source', 'warning');
      return;
    }

    this.showToast('Starting discovery scan...', 'info');
    try {
      const result = await window.apiClient.scan(selectedSources);
      this.showToast(`Scan completed: ${result.campaigns_found || 0} campaigns found (${result.campaigns_new || 0} new, ${result.campaigns_updated || 0} updated)`, 'success');
      if (result.errors && result.errors.length > 0) {
        this.showToast(`Errors: ${result.errors.join(', ')}`, 'warning');
      }
      await this.refresh();
      await this.loadSources(); // Refresh source stats
    } catch (err) {
      this.showToast(`Scan failed: ${err.message}`, 'error');
    }
  }

  async createBackup() {
    this.showToast('Creating backup...', 'info');
    try {
      await window.apiClient.backup();
      this.showToast('Backup created successfully', 'success');
    } catch (err) {
      this.showToast(`Backup failed: ${err.message}`, 'error');
    }
  }

  async runDiagnostics() {
    this.showToast('Running diagnostics...', 'info');
    try {
      const health = await window.apiClient.health();
      this.showToast(`Diagnostics: ${JSON.stringify(health)}`, 'success');
    } catch (err) {
      this.showToast(`Diagnostics failed: ${err.message}`, 'error');
    }
  }

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  handleSearch(query) {
    const results = document.getElementById('search-results');
    if (!results) return;

    if (query.length < 2) {
      this.hideSearchResults();
      return;
    }

    // Debounced search would go here
    // For now, just show placeholder
    results.innerHTML = `
      <div class="search-result-item" style="padding: var(--spacing-3) var(--spacing-4); color: var(--color-text-secondary);">
        Search for "${this.escapeHtml(query)}" - feature coming soon
      </div>
    `;
    this.showSearchResults();
  }

  showSearchResults() {
    document.getElementById('search-results')?.classList.add('active');
  }

  hideSearchResults() {
    document.getElementById('search-results')?.classList.remove('active');
  }

  showToast(message, type = 'info', title = '') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
      success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
      error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
      warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || icons.info}</div>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${this.escapeHtml(title)}</div>` : ''}
        <div class="toast-message">${this.escapeHtml(message)}</div>
      </div>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
  }

  showModal(title, body, footer) {
    const overlay = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalFooter = document.getElementById('modal-footer');

    if (modalTitle) modalTitle.textContent = title;
    if (modalBody) modalBody.innerHTML = body;
    if (modalFooter) modalFooter.innerHTML = footer || '';

    overlay?.classList.add('active');
    overlay?.removeAttribute('hidden');
  }

  closeModal() {
    const overlay = document.getElementById('modal-overlay');
    overlay?.classList.remove('active');
    setTimeout(() => overlay?.setAttribute('hidden', ''), 200);
  }

  async showCampaignDetail(campaignId) {
    try {
      this.showModal('Loading...', '<div class="loading-overlay"><div class="loading-spinner"></div><div class="loading-text">Loading campaign details...</div></div>');
      const campaign = await window.apiClient.campaign(campaignId);
      this.renderCampaignDetail(campaign);
    } catch (err) {
      this.showToast(`Failed to load campaign: ${err.message}`, 'error');
      this.closeModal();
    }
  }

  renderCampaignDetail(campaign) {
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalFooter = document.getElementById('modal-footer');

    if (modalTitle) modalTitle.textContent = campaign.name;

    const riskBadgeClass = this.getRiskBadgeClass(campaign.risk_level);
    const verificationBadgeClass = this.getVerificationBadgeClass(campaign.verification_status);
    const statusBadgeClass = this.getStatusBadgeClass(campaign.status);

    let html = `
      <div class="campaign-detail">
        <div class="detail-header">
          <div class="detail-main">
            <h2>${this.escapeHtml(campaign.name)}</h2>
            <div class="detail-meta">
              <span class="badge ${statusBadgeClass}">${this.escapeHtml(campaign.status)}</span>
              <span class="badge ${verificationBadgeClass}">${this.escapeHtml(campaign.verification_status)}</span>
              <span class="badge ${riskBadgeClass}">${this.escapeHtml(campaign.risk_level)} (${campaign.risk_score}/100)</span>
            </div>
          </div>
          <div class="detail-project">${this.escapeHtml(campaign.project || 'Unknown Project')}</div>
        </div>

        <div class="detail-grid">
          <div class="detail-section">
            <h3>Basic Information</h3>
            <dl class="detail-list">
              <dt>Type</dt><dd><span class="badge badge-${campaign.type}">${this.escapeHtml(campaign.type)}</span></dd>
              <dt>Network</dt><dd>${this.escapeHtml(campaign.network || 'N/A')}</dd>
              <dt>Discovered</dt><dd>${this.formatDate(campaign.discovered_at)}</dd>
              <dt>Last Seen</dt><dd>${this.formatDate(campaign.last_seen_at)}</dd>
              ${campaign.deadline ? `<dt>Deadline</dt><dd>${this.formatDate(campaign.deadline)}</dd>` : ''}
              ${campaign.snapshot_date ? `<dt>Snapshot Date</dt><dd>${this.formatDate(campaign.snapshot_date)}</dd>` : ''}
            </dl>
          </div>

          <div class="detail-section">
            <h3>Links</h3>
            <dl class="detail-list">
              ${campaign.official_url ? `<dt>Official URL</dt><dd><a href="${this.escapeHtml(campaign.official_url)}" target="_blank">${this.escapeHtml(campaign.official_url)}</a></dd>` : ''}
              ${campaign.campaign_url ? `<dt>Campaign URL</dt><dd><a href="${this.escapeHtml(campaign.campaign_url)}" target="_blank">${this.escapeHtml(campaign.campaign_url)}</a></dd>` : ''}
            </dl>
          </div>

          ${campaign.description ? `
          <div class="detail-section full-width">
            <h3>Description</h3>
            <p>${this.escapeHtml(campaign.description)}</p>
          </div>
          ` : ''}

${campaign.evidence && campaign.evidence.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Evidence (${campaign.evidence.length})</h3>
             <ul class="evidence-list">
               ${campaign.evidence.map(e => `
                 <li>
                   <a href="${this.escapeHtml(e.url)}" target="_blank">${this.escapeHtml(e.title || e.url)}</a>
                   <span class="evidence-meta">${e.source_type} • ${this.formatDate(e.fetched_at)} ${e.verified ? '✓ Verified' : ''}</span>
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}

           ${campaign.risk_findings && campaign.risk_findings.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Risk Findings (${campaign.risk_findings.length})</h3>
             <ul class="risk-findings-list">
               ${campaign.risk_findings.map(r => `
                 <li class="risk-finding risk-${r.severity}">
                   <span class="risk-rule">${this.escapeHtml(r.rule_id)} v${r.rule_version}</span>
                   <span class="risk-finding-text">${this.escapeHtml(r.finding)}</span>
                   <span class="risk-severity badge badge-${r.severity}">${this.escapeHtml(r.severity)}</span>
                   ${r.description ? `<p class="risk-description">${this.escapeHtml(r.description)}</p>` : ''}
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}

           ${campaign.eligibility && campaign.eligibility.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Eligibility Requirements (${campaign.eligibility.length})</h3>
             <ul class="eligibility-list">
               ${campaign.eligibility.map(e => `
                 <li class="eligibility-item eligibility-${e.status}">
                   <span class="eligibility-category">${this.escapeHtml(e.category)}</span>
                   <span class="eligibility-requirement">${this.escapeHtml(e.requirement)}</span>
                   <span class="eligibility-status badge badge-${e.status}">${this.escapeHtml(e.status)}</span>
                   ${e.source ? `<span class="eligibility-source">Source: ${this.escapeHtml(e.source)}</span>` : ''}
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}

           ${campaign.geo_restrictions && campaign.geo_restrictions.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Geographic Restrictions</h3>
             <ul class="geo-restrictions-list">
               ${campaign.geo_restrictions.map(g => `
                 <li class="geo-restriction geo-${g.type}">
                   <span class="geo-country">${this.escapeHtml(g.country)}</span>
                   <span class="geo-type badge badge-${g.type}">${this.escapeHtml(g.type)}</span>
                   ${g.notes ? `<span class="geo-notes">${this.escapeHtml(g.notes)}</span>` : ''}
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}

           ${campaign.category_data ? this.renderCategoryData(campaign.category_data) : ''}

           ${campaign.user_progress && campaign.user_progress.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Your Progress (${campaign.user_progress.length})</h3>
             <ul class="progress-list">
               ${campaign.user_progress.map(p => `
                 <li class="progress-item progress-${p.status}">
                   <span class="progress-requirement">${this.escapeHtml(p.requirement)}</span>
                   <span class="progress-status badge badge-${p.status}">${this.escapeHtml(p.status)}</span>
                   ${p.notes ? `<span class="progress-notes">${this.escapeHtml(p.notes)}</span>` : ''}
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}

           ${campaign.events && campaign.events.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Upcoming Events (${campaign.events.length})</h3>
             <ul class="events-list">
               ${campaign.events.map(e => `
                 <li class="event-item event-${e.type}">
                   <span class="event-title">${this.escapeHtml(e.title)}</span>
                   <span class="event-date">${this.formatDate(e.date)}</span>
                   <span class="event-type badge badge-${e.type}">${this.escapeHtml(e.type)}</span>
                   ${e.description ? `<span class="event-description">${this.escapeHtml(e.description)}</span>` : ''}
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}

           ${campaign.claims && campaign.claims.length > 0 ? `
           <div class="detail-section full-width">
             <h3>Reward Claims (${campaign.claims.length})</h3>
             <ul class="claims-list">
               ${campaign.claims.map(c => `
                 <li class="claim-item claim-${c.status}">
                   <span class="claim-type">${this.escapeHtml(c.type)}</span>
                   <span class="claim-status badge badge-${c.status}">${this.escapeHtml(c.status)}</span>
                   ${c.transaction_hash ? `<span class="claim-tx"><a href="https://etherscan.io/tx/${this.escapeHtml(c.transaction_hash)}" target="_blank">View on Explorer</a></span>` : ''}
                   ${c.notes ? `<span class="claim-notes">${this.escapeHtml(c.notes)}</span>` : ''}
                 </li>
               `).join('')}
             </ul>
           </div>
           ` : ''}
        </div>
      </div>
    `;

    if (modalBody) modalBody.innerHTML = html;

    if (modalFooter) {
      modalFooter.innerHTML = `
        <button class="btn btn-secondary" onclick="window.app.closeModal()">Close</button>
        <button class="btn btn-primary" onclick="window.app.openCampaignUrl('${this.escapeHtml(campaign.campaign_url || campaign.official_url || '')}')">Open Campaign</button>
        ${campaign.id ? `
        <button class="btn btn-secondary" onclick="window.app.trackCampaign('${this.escapeHtml(campaign.id)}')">Track Campaign</button>
        <button class="btn btn-secondary" onclick="window.app.addEligibilityProgress('${this.escapeHtml(campaign.id)}')">Update Progress</button>
        ` : ''}
      `;
    }
  }

  renderCategoryData(categoryData) {
    if (!categoryData) return '';
    
    const type = categoryData.campaign_type;
    let html = `<div class="detail-section full-width"><h3>${this.capitalizeFirst(type)} Details</h3>`;
    
    if (type === 'nft' && categoryData.nft) {
      const nft = categoryData.nft;
      html += `
        <dl class="detail-list">
          ${nft.collection_name ? `<dt>Collection</dt><dd>${this.escapeHtml(nft.collection_name)}</dd>` : ''}
          ${nft.collection_slug ? `<dt>Slug</dt><dd>${this.escapeHtml(nft.collection_slug)}</dd>` : ''}
          ${nft.contract_address ? `<dt>Contract</dt><dd><code>${this.escapeHtml(nft.contract_address)}</code></dd>` : ''}
          ${nft.chain ? `<dt>Chain</dt><dd>${this.escapeHtml(nft.chain)}</dd>` : ''}
          ${nft.mint_price ? `<dt>Mint Price</dt><dd>${this.escapeHtml(nft.mint_price)}</dd>` : ''}
          ${nft.mint_date ? `<dt>Mint Date</dt><dd>${this.formatDate(nft.mint_date)}</dd>` : ''}
          ${nft.total_supply ? `<dt>Total Supply</dt><dd>${this.escapeHtml(nft.total_supply.toLocaleString())}</dd>` : ''}
          ${nft.max_per_wallet ? `<dt>Max per Wallet</dt><dd>${this.escapeHtml(nft.max_per_wallet.toLocaleString())}</dd>` : ''}
          ${nft.royalty_percentage ? `<dt>Royalty</dt><dd>${this.escapeHtml(nft.royalty_percentage)}%</dd>` : ''}
          ${nft.allowlist ? `<dt>Allowlist</dt><dd>${this.escapeHtml(nft.allowlist)}</dd>` : ''}
        </dl>
      `;
    } else if (type === 'testnet' && categoryData.testnet) {
      const tn = categoryData.testnet;
      html += `
        <dl class="detail-list">
          ${tn.network_name ? `<dt>Network</dt><dd>${this.escapeHtml(tn.network_name)}</dd>` : ''}
          ${tn.chain_id ? `<dt>Chain ID</dt><dd>${this.escapeHtml(tn.chain_id)}</dd>` : ''}
          ${tn.faucet_url ? `<dt>Faucet</dt><dd><a href="${this.escapeHtml(tn.faucet_url)}" target="_blank">${this.escapeHtml(tn.faucet_url)}</a></dd>` : ''}
          ${tn.explorer_url ? `<dt>Explorer</dt><dd><a href="${this.escapeHtml(tn.explorer_url)}" target="_blank">${this.escapeHtml(tn.explorer_url)}</a></dd>` : ''}
          ${tn.docs_url ? `<dt>Docs</dt><dd><a href="${this.escapeHtml(tn.docs_url)}" target="_blank">${this.escapeHtml(tn.docs_url)}</a></dd>` : ''}
          ${tn.is_incentivized !== undefined ? `<dt>Incentivized</dt><dd>${tn.is_incentivized ? 'Yes' : 'No'}</dd>` : ''}
          ${tn.reward_token ? `<dt>Reward Token</dt><dd>${this.escapeHtml(tn.reward_token)}</dd>` : ''}
          ${tn.mainnet_launch ? `<dt>Mainnet Launch</dt><dd>${this.formatDate(tn.mainnet_launch)}</dd>` : ''}
        </dl>
      `;
    } else if (type === 'reward' && categoryData.reward) {
      const rw = categoryData.reward;
      html += `
        <dl class="detail-list">
          ${rw.token_symbol ? `<dt>Token</dt><dd>${this.escapeHtml(rw.token_symbol)}</dd>` : ''}
          ${rw.token_address ? `<dt>Contract</dt><dd><code>${this.escapeHtml(rw.token_address)}</code></dd>` : ''}
          ${rw.chain ? `<dt>Chain</dt><dd>${this.escapeHtml(rw.chain)}</dd>` : ''}
          ${rw.total_allocation ? `<dt>Total Allocation</dt><dd>${this.escapeHtml(rw.total_allocation.toLocaleString())}</dd>` : ''}
          ${rw.claim_start ? `<dt>Claim Starts</dt><dd>${this.formatDate(rw.claim_start)}</dd>` : ''}
          ${rw.claim_end ? `<dt>Claim Ends</dt><dd>${this.formatDate(rw.claim_end)}</dd>` : ''}
          ${rw.claim_url ? `<dt>Claim URL</dt><dd><a href="${this.escapeHtml(rw.claim_url)}" target="_blank">${this.escapeHtml(rw.claim_url)}</a></dd>` : ''}
          ${rw.vesting_schedule ? `<dt>Vesting</dt><dd>${this.escapeHtml(rw.vesting_schedule)}</dd>` : ''}
          ${rw.is_confirmed !== undefined ? `<dt>Confirmed</dt><dd>${rw.is_confirmed ? 'Yes ✓' : 'Pending'}</dd>` : ''}
          ${rw.distribution_method ? `<dt>Distribution</dt><dd>${this.escapeHtml(rw.distribution_method)}</dd>` : ''}
        </dl>
      `;
    }
    
    html += '</div>';
    return html;
  }

  capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  getRiskBadgeClass(riskLevel) {
    switch (riskLevel) {
      case 'low': return 'badge-low';
      case 'medium': return 'badge-medium';
      case 'high': return 'badge-high';
      case 'critical': return 'badge-critical';
      default: return 'badge-medium';
    }
  }

  getVerificationBadgeClass(verificationStatus) {
    switch (verificationStatus) {
      case 'officially_corroborated': return 'badge-official';
      case 'independently_corroborated': return 'badge-independent';
      case 'unverified': return 'badge-unverified';
      case 'suspicious': return 'badge-suspicious';
      case 'expired': return 'badge-expired';
      case 'withdrawn': return 'badge-withdrawn';
      default: return 'badge-unverified';
    }
  }

  getStatusBadgeClass(status) {
    switch (status) {
      case 'active': return 'badge-active';
      case 'upcoming': return 'badge-upcoming';
      case 'ended': return 'badge-ended';
      case 'expired': return 'badge-expired-status';
      case 'withdrawn': return 'badge-withdrawn';
      default: return 'badge-active';
    }
  }

  openCampaignUrl(url) {
    if (url) {
      window.shell.openExternal(url);
    }
  }

  formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return 'Invalid date';
    }
  }

  escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
      .replace(/&/g, '&')
      .replace(/</g, '<')
      .replace(/>/g, '>')
      .replace(/"/g, '"')
      .replace(/'/g, '&#039;');
  }

  async trackCampaign(campaignId) {
    try {
      this.showToast('Adding to tracking...', 'info');
      await window.apiClient.trackCampaign(campaignId);
      this.showToast('Campaign added to tracking', 'success');
      await this.loadTracking();
    } catch (err) {
      this.showToast(`Failed to track campaign: ${err.message}`, 'error');
    }
  }

  async addEligibilityProgress(campaignId) {
    try {
      const campaign = await window.apiClient.campaign(campaignId);
      this.showProgressModal(campaign);
    } catch (err) {
      this.showToast(`Failed to load campaign: ${err.message}`, 'error');
    }
  }

  async updateProgress(campaignId) {
    try {
      const campaign = await window.apiClient.campaign(campaignId);
      this.showProgressModal(campaign);
    } catch (err) {
      this.showToast(`Failed to load campaign: ${err.message}`, 'error');
    }
  }

  showProgressModal(campaign) {
    const requirements = campaign.eligibility || [];
    const userProgress = campaign.user_progress || [];
    
    let html = `
      <div class="progress-modal">
        <h3>Update Progress: ${this.escapeHtml(campaign.name)}</h3>
        <form id="progress-form">
          ${requirements.map((req, idx) => {
            const progress = userProgress.find(p => p.requirement === req.requirement);
            const currentStatus = progress?.status || 'not_met';
            const currentNotes = progress?.notes || '';
            return `
              <div class="progress-requirement">
                <label>
                  <input type="checkbox" name="req_${idx}" value="${this.escapeHtml(req.requirement)}" ${currentStatus === 'met' ? 'checked' : ''} data-requirement="${this.escapeHtml(req.requirement)}">
                  <span class="req-text">${this.escapeHtml(req.requirement)}</span>
                  <span class="req-category">${this.escapeHtml(req.category)}</span>
                </label>
                <textarea name="notes_${idx}" placeholder="Notes (optional)" class="progress-notes">${this.escapeHtml(currentNotes)}</textarea>
              </div>
            `;
          }).join('')}
          <div class="progress-form-actions">
            <button type="button" class="btn btn-secondary" onclick="window.app.closeModal()">Cancel</button>
            <button type="submit" class="btn btn-primary">Save Progress</button>
          </div>
        </form>
      </div>
    `;

    this.showModal('Update Progress', html, '');

    // Handle form submission
    setTimeout(() => {
      const form = document.getElementById('progress-form');
      if (form) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const formData = new FormData(form);
          
          for (const [name, value] of formData.entries()) {
            if (name.startsWith('req_')) {
              const idx = name.replace('req_', '');
              const requirement = value;
              const isChecked = form.querySelector(`input[name="req_${idx}"]`).checked;
              const notes = form.querySelector(`textarea[name="notes_${idx}"]`)?.value || '';
              
              try {
                await window.apiClient.updateProgress(campaign.id, {
                  requirement,
                  status: isChecked ? 'met' : 'not_met',
                  notes
                });
              } catch (err) {
                console.error('Failed to update progress:', err);
              }
            }
          }
          
          this.showToast('Progress updated', 'success');
          this.closeModal();
          await this.loadTracking();
        });
      }
    }, 0);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
  window.app.init();
});