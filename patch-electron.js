// patch-electron.js - Run this before loading the main module
// This patches the electron npm package to return the built-in modules when running inside Electron

const Module = require('module');

// Clear any existing cache for electron
const electronCacheKey = require.resolve('electron');
if (require.cache[electronCacheKey]) {
  delete require.cache[electronCacheKey];
}

// Also clear the npm package's index.js cache
try {
  const indexPath = require.resolve('electron/index.js');
  if (require.cache[indexPath]) {
    delete require.cache[indexPath];
  }
} catch (e) {}

// Now load the built-in electron module and cache it
// The built-in module should be available via the internal binding
try {
  // Use process.binding to access the internal electron module
  const binding = process.binding('electron');
  if (binding && typeof binding === 'object') {
    require.cache[electronCacheKey] = { exports: binding, loaded: true };
    console.log('Loaded electron from process.binding');
  } else {
    // Try Module._load with the internal module name
    const builtinElectron = Module._load('electron', module, false);
    if (builtinElectron && typeof builtinElectron === 'object' && builtinElectron.app) {
      require.cache[electronCacheKey] = { exports: builtinElectron, loaded: true };
      console.log('Loaded electron via Module._load');
    } else {
      console.log('Built-in electron not available via Module._load');
    }
  }
} catch (e) {
  console.error('Failed to load built-in electron module:', e.message);
}