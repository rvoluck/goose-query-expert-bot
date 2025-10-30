#!/usr/bin/env python3
"""
Health Check HTTP Endpoints for Kubernetes/Docker
Provides /health, /ready, and /metrics endpoints
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Tuple

from aiohttp import web
import structlog

from health_check import HealthEndpoints
from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class HealthCheckServer:
    """HTTP server for health check endpoints"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 3000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.health_endpoints = HealthEndpoints()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/ready', self.readiness_handler)
        self.app.router.add_get('/live', self.liveness_handler)
        self.app.router.add_get('/metrics', self.metrics_handler)
        self.app.router.add_get('/info', self.info_handler)
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """
        Main health check endpoint
        Returns 200 if healthy, 503 if unhealthy
        """
        try:
            status_code, result = await self.health_endpoints.health_check()
            
            return web.Response(
                text=json.dumps(result, indent=2),
                status=status_code,
                content_type='application/json'
            )
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return web.Response(
                text=json.dumps({
                    "status": "unhealthy",
                    "message": f"Health check error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }),
                status=500,
                content_type='application/json'
            )
    
    async def readiness_handler(self, request: web.Request) -> web.Response:
        """
        Readiness probe endpoint for Kubernetes
        Checks if service is ready to accept traffic
        """
        try:
            status_code, result = await self.health_endpoints.readiness_check()
            
            return web.Response(
                text=json.dumps(result, indent=2),
                status=status_code,
                content_type='application/json'
            )
        except Exception as e:
            logger.error("Readiness check failed", error=str(e))
            return web.Response(
                text=json.dumps({
                    "status": "not_ready",
                    "message": f"Readiness check error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }),
                status=503,
                content_type='application/json'
            )
    
    async def liveness_handler(self, request: web.Request) -> web.Response:
        """
        Liveness probe endpoint for Kubernetes
        Checks if service is alive (minimal check)
        """
        try:
            status_code, result = await self.health_endpoints.liveness_check()
            
            return web.Response(
                text=json.dumps(result, indent=2),
                status=status_code,
                content_type='application/json'
            )
        except Exception as e:
            logger.error("Liveness check failed", error=str(e))
            return web.Response(
                text=json.dumps({
                    "status": "dead",
                    "message": f"Liveness check error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }),
                status=500,
                content_type='application/json'
            )
    
    async def metrics_handler(self, request: web.Request) -> web.Response:
        """
        Prometheus metrics endpoint
        Returns metrics in Prometheus format
        """
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            
            metrics = generate_latest()
            
            return web.Response(
                body=metrics,
                content_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error("Metrics endpoint failed", error=str(e))
            return web.Response(
                text=f"# Error generating metrics: {str(e)}",
                status=500,
                content_type='text/plain'
            )
    
    async def info_handler(self, request: web.Request) -> web.Response:
        """
        Service information endpoint
        Returns version, build info, and configuration
        """
        try:
            import os
            import platform
            import sys
            
            info = {
                "service": "goose-slackbot",
                "version": os.getenv("VERSION", "unknown"),
                "build_date": os.getenv("BUILD_DATE", "unknown"),
                "git_commit": os.getenv("VCS_REF", "unknown"),
                "environment": settings.environment,
                "python_version": sys.version,
                "platform": platform.platform(),
                "hostname": platform.node(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "configuration": {
                    "workers": settings.workers,
                    "debug": settings.debug,
                    "log_level": settings.log_level,
                    "metrics_enabled": settings.metrics_enabled,
                }
            }
            
            return web.Response(
                text=json.dumps(info, indent=2),
                status=200,
                content_type='application/json'
            )
        except Exception as e:
            logger.error("Info endpoint failed", error=str(e))
            return web.Response(
                text=json.dumps({
                    "error": f"Info endpoint error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }),
                status=500,
                content_type='application/json'
            )
    
    async def start(self):
        """Start the health check server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(
            "Health check server started",
            host=self.host,
            port=self.port
        )
    
    def run(self):
        """Run the health check server"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())
        loop.run_forever()


async def main():
    """Main entry point for standalone health check server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health Check Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = HealthCheckServer(host=args.host, port=args.port)
    await server.start()
    
    logger.info("Health check server running", host=args.host, port=args.port)
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down health check server")


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()
    
    asyncio.run(main())
