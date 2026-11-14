from fastapi import APIRouter, Depends, Request
from backend.core.models import HealthResponse
from backend.config import get_settings
from backend.core.security import token_manager
import time

router = APIRouter()
start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database="connected",
        uptime_seconds=time.time() - start_time,
    )


@router.get("/launch")
async def launch_page(request: Request):
    """Serve the launch page with API config embedded for browser mode."""
    # Get the token from the token manager
    token = token_manager.get_token()
    if not token:
        # Generate a new token if none exists
        token = token_manager.generate()
    
    base_url = f"http://127.0.0.1:{request.url.port or 8000}"
    
    config_json = f'{{"baseUrl":"{base_url}","token":"{token}"}}'
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Global Airdrop Hunter - Loading</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               display: flex; align-items: center; justify-content: center; height: 100vh; 
               margin: 0; background: #0d1117; color: #e6edf3; }}
        .loader {{ display: flex; flex-direction: column; align-items: center; gap: 1rem; }}
        .spinner {{ width: 32px; height: 32px; border: 3px solid #30363d; border-top-color: #1f6feb; 
                   border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="loader">
        <div class="spinner"></div>
        <div>Initializing Global Airdrop Hunter...</div>
    </div>
    <script>
        (function() {{
            try {{
                var config = {config_json};
                localStorage.setItem('gah_api_config', JSON.stringify(config));
                console.log('[Launcher] API config stored in localStorage');
            }} catch (e) {{
                console.error('[Launcher] Failed to store config:', e);
            }}
            // Redirect to the frontend
            window.location.href = '{base_url}';
        }})();
    </script>
</body>
</html>
"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)