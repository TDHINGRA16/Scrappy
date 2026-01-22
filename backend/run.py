"""
Startup script for Scrappy v2.0 on Windows
This ensures the correct event loop policy is set before uvicorn starts
"""

import sys
import asyncio
import os

# Must be set before importing any async code
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✓ Windows event loop policy set")

if __name__ == "__main__":
    import uvicorn
    
    # Disable reload on Windows to prevent event loop policy issues
    # Use watchfiles or restart manually for development
    reload = False if sys.platform == 'win32' else True
    
    print(f"Starting Scrappy v2.0 (reload: {reload})")
    print("Note: On Windows, reload is disabled to prevent Playwright issues")
    print("      Restart the server manually to see code changes")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        loop="asyncio"
    )
