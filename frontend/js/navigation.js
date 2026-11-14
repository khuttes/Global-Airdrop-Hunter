class Navigation {
  constructor() {
    this.currentModule = 'dashboard';
    this.modules = [
      'dashboard',
      'campaigns',
      'discovery',
      'tracking',
      'settings',
    ];
  }

  init() {
    this.bindEvents();
    this.showModule('dashboard');
  }

  bindEvents() {
    document.querySelectorAll('.nav-item[data-module]').forEach(item => {
      item.addEventListener('click', () => {
        const module = item.dataset.module;
        this.showModule(module);
      });
    });

    document.getElementById('view-all-campaigns')?.addEventListener('click', () => {
      this.showModule('campaigns');
    });

    document.getElementById('view-all-deadlines')?.addEventListener('click', () => {
      this.showModule('tracking');
    });
  }

  showModule(moduleName) {
    if (!this.modules.includes(moduleName)) {
      console.warn(`Unknown module: ${moduleName}`);
      return;
    }

    document.querySelectorAll('.module').forEach(el => {
      el.classList.remove('active');
    });

    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.remove('active');
      el.removeAttribute('aria-current');
    });

    const moduleEl = document.getElementById(`module-${moduleName}`);
    const navItem = document.querySelector(`.nav-item[data-module="${moduleName}"]`);

    if (moduleEl) {
      moduleEl.classList.add('active');
    }

    if (navItem) {
      navItem.classList.add('active');
      navItem.setAttribute('aria-current', 'page');
    }

    this.currentModule = moduleName;

    window.dispatchEvent(new CustomEvent('module-change', { detail: { module: moduleName } }));
  }

  getCurrentModule() {
    return this.currentModule;
  }
}

window.navigation = new Navigation();