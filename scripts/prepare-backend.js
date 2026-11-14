/**
 * Prepare backend for packaging.
 * Ensures Python virtual environment is ready and dependencies are installed.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

console.log('=== Preparing Backend for Packaging ===');

const projectRoot = path.join(__dirname, '..');
const backendDir = path.join(projectRoot, 'backend');
const venvDir = path.join(projectRoot, '.venv');
const venvScripts = path.join(venvDir, 'Scripts');
const pythonExe = path.join(venvScripts, 'python.exe');

// Check if virtual environment exists
if (!fs.existsSync(venvDir)) {
    console.log('Virtual environment not found. Creating...');
    const result = spawnSync('python', ['-m', 'venv', '.venv'], {
        cwd: projectRoot,
        stdio: 'inherit',
        shell: true,
        windowsVerbatimArguments: true
    });
    if (result.status !== 0) {
        console.error('Failed to create virtual environment');
        process.exit(1);
    }
}

// Upgrade pip using python -m pip
console.log('Upgrading pip...');
let result = spawnSync(pythonExe, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
    cwd: projectRoot,
    stdio: 'inherit',
    shell: true,
    windowsVerbatimArguments: true
});
if (result.status !== 0) {
    console.warn('Failed to upgrade pip, continuing...');
}

// Install backend dependencies using python -m pip
console.log('Installing backend dependencies...');
result = spawnSync(pythonExe, ['-m', 'pip', 'install', '-r', 'backend/requirements.txt'], {
    cwd: projectRoot,
    stdio: 'inherit',
    shell: true,
    windowsVerbatimArguments: true
});
if (result.status !== 0) {
    console.error('Failed to install backend dependencies');
    process.exit(1);
}

// Verify Python executable exists
if (!fs.existsSync(pythonExe)) {
    console.error('Python executable not found in virtual environment');
    process.exit(1);
}

// Test backend import
console.log('Testing backend imports...');
result = spawnSync(pythonExe, ['-c', `
import sys
sys.path.insert(0, 'backend')
from backend.main import create_app
from backend.config import get_settings
print("Backend imports OK")
`], {
    cwd: projectRoot,
    stdio: 'inherit',
    shell: true,
    windowsVerbatimArguments: true
});
if (result.status !== 0) {
    console.error('Backend import test failed');
    process.exit(1);
}

console.log('=== Backend preparation complete ===');
console.log(`Python executable: ${pythonExe}`);
console.log(`Virtual environment: ${venvDir}`);