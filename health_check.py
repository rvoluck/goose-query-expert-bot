#!/usr/bin/env python3
"""
Health Check Module for Goose Slackbot
Provides comprehensive health checking for all application components
"""

import asyncio
import json
import sys
import time
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import logging

import asyncpg
import aioredis
import httpx
import psutil
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


class HealthCheckResult:
    """Health check result container"""
    
    def __init__(self, name: str, status: str, message: str = "", 
                 duration_ms: float = 0, metadata: Dict = None):
        self.name = name
        self.status = status  # "healthy", "unhealthy", "warning"
        self.message = message
        self.duration_ms = duration_ms
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def is_healthy(self) -> bool:
        return self.status == "healthy"


class HealthChecker:
    """Comprehensive health checker for all application components"""
    
    def __init__(self):
        self.checks = []
        self.timeout = 30  # seconds
    
    async def check_database(self) -> HealthCheckResult:
        """Check PostgreSQL database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Parse database URL
            db_url = settings.database_url
            
            # Test connection
            conn = await asyncpg.connect(db_url, timeout=10)
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database query returned unexpected result")
            
            # Test application tables exist
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('user_sessions', 'query_history', 'user_mappings', 'audit_logs')
            """
            tables = await conn.fetch(tables_query)
            expected_tables = {'user_sessions', 'query_history', 'user_mappings', 'audit_logs'}
            found_tables = {row['table_name'] for row in tables}
            
            if not expected_tables.issubset(found_tables):
                missing_tables = expected_tables - found_tables
                raise Exception(f"Missing required tables: {missing_tables}")
            
            # Test database performance
            perf_start = time.time()
            await conn.fetchval("SELECT COUNT(*) FROM user_sessions")
            perf_duration = (time.time() - perf_start) * 1000
            
            await conn.close()
            
            duration_ms = (time.time() - start_time) * 1000
            
            metadata = {
                "tables_found": len(found_tables),
                "query_performance_ms": perf_duration,
                "connection_time_ms": duration_ms
            }
            
            return HealthCheckResult(
                "database",
                "healthy",
                "Database connection and queries successful",
                duration_ms,
                metadata
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return HealthCheckResult(
                "database",
                "unhealthy",
                f"Database check failed: {str(e)}",
                duration_ms,
                {"error": str(e)}
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        try:
            # Connect to Redis
            redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10
            )
            
            # Test basic operations
            test_key = f"health_check_{int(time.time())}"
            test_value = "health_check_value"
            
            # Set and get test value
            await redis.set(test_key, test_value, ex=60)
            retrieved_value = await redis.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Redis set/get operation failed")
            
            # Clean up test key
            await redis.delete(test_key)
            
            # Test Redis info
            info = await redis.info()
            memory_usage = info.get('used_memory_human', 'unknown')
            connected_clients = info.get('connected_clients', 0)
            
            await redis.close()
            
            duration_ms = (time.time() - start_time) * 1000
            
            metadata = {
                "memory_usage": memory_usage,
                "connected_clients": connected_clients,
                "response_time_ms": duration_ms
            }
            
            return HealthCheckResult(
                "redis",
                "healthy",
                "Redis connection and operations successful",
                duration_ms,
                metadata
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return HealthCheckResult(
                "redis",
                "unhealthy",
                f"Redis check failed: {str(e)}",
                duration_ms,
                {"error": str(e)}
            )
    
    async def check_slack_api(self) -> HealthCheckResult:
        """Check Slack API connectivity"""
        start_time = time.time()
        
        try:
            client = AsyncWebClient(token=settings.slack_bot_token)
            
            # Test auth
            auth_response = await client.auth_test()
            
            if not auth_response["ok"]:
                raise Exception(f"Slack auth failed: {auth_response.get('error', 'Unknown error')}")
            
            bot_id = auth_response.get("user_id")
            team_name = auth_response.get("team")
            
            # Test API rate limits (get current user info)
            user_info = await client.users_info(user=bot_id)
            
            if not user_info["ok"]:
                raise Exception(f"Slack API call failed: {user_info.get('error', 'Unknown error')}")
            
            duration_ms = (time.time() - start_time) * 1000
            
            metadata = {
                "bot_id": bot_id,
                "team_name": team_name,
                "api_response_time_ms": duration_ms
            }
            
            return HealthCheckResult(
                "slack_api",
                "healthy",
                "Slack API connection successful",
                duration_ms,
                metadata
            )
            
        except SlackApiError as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Slack API health check failed: {e}")
            
            # Check if it's a rate limit issue
            status = "warning" if e.response.status_code == 429 else "unhealthy"
            
            return HealthCheckResult(
                "slack_api",
                status,
                f"Slack API check failed: {e.response['error']}",
                duration_ms,
                {"error": e.response.get('error', str(e)), "status_code": e.response.status_code}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Slack API health check failed: {e}")
            
            return HealthCheckResult(
                "slack_api",
                "unhealthy",
                f"Slack API check failed: {str(e)}",
                duration_ms,
                {"error": str(e)}
            )
    
    async def check_goose_mcp(self) -> HealthCheckResult:
        """Check Goose MCP server connectivity"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Test basic connectivity
                health_url = f"{settings.goose_mcp_server_url}/health"
                response = await client.get(health_url)
                
                if response.status_code != 200:
                    raise Exception(f"Goose MCP server returned status {response.status_code}")
                
                # Try to parse response
                try:
                    health_data = response.json()
                    server_status = health_data.get("status", "unknown")
                except:
                    server_status = "unknown"
                
                duration_ms = (time.time() - start_time) * 1000
                
                metadata = {
                    "server_url": settings.goose_mcp_server_url,
                    "server_status": server_status,
                    "response_time_ms": duration_ms
                }
                
                return HealthCheckResult(
                    "goose_mcp",
                    "healthy",
                    "Goose MCP server connection successful",
                    duration_ms,
                    metadata
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Goose MCP health check failed: {e}")
            
            return HealthCheckResult(
                "goose_mcp",
                "unhealthy",
                f"Goose MCP check failed: {str(e)}",
                duration_ms,
                {"error": str(e), "server_url": settings.goose_mcp_server_url}
            )
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                load_1min = load_avg[0]
            except:
                load_1min = None
            
            # Network connections
            try:
                connections = len(psutil.net_connections())
            except:
                connections = None
            
            # Determine health status
            status = "healthy"
            warnings = []
            
            if cpu_percent > 90:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory_percent > 90:
                status = "warning"
                warnings.append(f"High memory usage: {memory_percent}%")
            
            if disk_percent > 90:
                status = "warning"
                warnings.append(f"High disk usage: {disk_percent}%")
            
            if memory_available_gb < 0.5:
                status = "unhealthy"
                warnings.append(f"Low available memory: {memory_available_gb:.2f}GB")
            
            if disk_free_gb < 1.0:
                status = "unhealthy"
                warnings.append(f"Low disk space: {disk_free_gb:.2f}GB")
            
            duration_ms = (time.time() - start_time) * 1000
            
            metadata = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": round(memory_available_gb, 2),
                "disk_percent": disk_percent,
                "disk_free_gb": round(disk_free_gb, 2),
                "load_1min": load_1min,
                "network_connections": connections
            }
            
            message = "System resources within normal limits"
            if warnings:
                message = f"System resource warnings: {'; '.join(warnings)}"
            
            return HealthCheckResult(
                "system_resources",
                status,
                message,
                duration_ms,
                metadata
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"System resources health check failed: {e}")
            
            return HealthCheckResult(
                "system_resources",
                "unhealthy",
                f"System resources check failed: {str(e)}",
                duration_ms,
                {"error": str(e)}
            )
    
    async def run_all_checks(self) -> Tuple[bool, Dict]:
        """Run all health checks and return overall status"""
        start_time = time.time()
        
        # Define all checks
        check_functions = [
            self.check_database,
            self.check_redis,
            self.check_slack_api,
            self.check_goose_mcp,
            self.check_system_resources
        ]
        
        # Run checks concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[check() for check in check_functions], return_exceptions=True),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error("Health checks timed out")
            return False, {
                "status": "unhealthy",
                "message": "Health checks timed out",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": []
            }
        
        # Process results
        check_results = []
        overall_healthy = True
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check exception: {result}")
                check_results.append(HealthCheckResult(
                    "unknown",
                    "unhealthy",
                    f"Check failed with exception: {str(result)}",
                    0,
                    {"error": str(result)}
                ))
                overall_healthy = False
            else:
                check_results.append(result)
                if not result.is_healthy():
                    overall_healthy = False
        
        total_duration = (time.time() - start_time) * 1000
        
        # Build response
        response = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "message": "All checks passed" if overall_healthy else "One or more checks failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_duration_ms": total_duration,
            "checks": [check.to_dict() for check in check_results],
            "summary": {
                "total_checks": len(check_results),
                "healthy_checks": sum(1 for check in check_results if check.is_healthy()),
                "unhealthy_checks": sum(1 for check in check_results if not check.is_healthy())
            }
        }
        
        return overall_healthy, response


# Health check endpoints for web framework integration
class HealthEndpoints:
    """Health check endpoints for integration with web frameworks"""
    
    def __init__(self):
        self.checker = HealthChecker()
    
    async def health_check(self) -> Tuple[int, Dict]:
        """Main health check endpoint"""
        try:
            is_healthy, result = await self.checker.run_all_checks()
            status_code = 200 if is_healthy else 503
            return status_code, result
        except Exception as e:
            logger.error(f"Health check endpoint failed: {e}")
            return 500, {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def readiness_check(self) -> Tuple[int, Dict]:
        """Readiness check - lighter weight check for Kubernetes"""
        try:
            # Only check critical dependencies for readiness
            checker = HealthChecker()
            
            # Run only essential checks
            db_check = await checker.check_database()
            redis_check = await checker.check_redis()
            
            is_ready = db_check.is_healthy() and redis_check.is_healthy()
            
            result = {
                "status": "ready" if is_ready else "not_ready",
                "message": "Service is ready" if is_ready else "Service is not ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": [db_check.to_dict(), redis_check.to_dict()]
            }
            
            status_code = 200 if is_ready else 503
            return status_code, result
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return 500, {
                "status": "not_ready",
                "message": f"Readiness check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def liveness_check(self) -> Tuple[int, Dict]:
        """Liveness check - minimal check to verify process is alive"""
        try:
            # Simple check that the process is responsive
            start_time = time.time()
            
            # Basic system check
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            duration_ms = (time.time() - start_time) * 1000
            
            result = {
                "status": "alive",
                "message": "Service is alive and responsive",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": duration_ms,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent
                }
            }
            
            return 200, result
            
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return 500, {
                "status": "dead",
                "message": f"Liveness check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# CLI interface for health checks
async def main():
    """CLI interface for running health checks"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Goose Slackbot Health Checker")
    parser.add_argument("--check", choices=["health", "readiness", "liveness"], 
                       default="health", help="Type of health check to run")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--exit-code", action="store_true", 
                       help="Exit with non-zero code if unhealthy")
    
    args = parser.parse_args()
    
    endpoints = HealthEndpoints()
    
    try:
        if args.check == "health":
            status_code, result = await endpoints.health_check()
        elif args.check == "readiness":
            status_code, result = await endpoints.readiness_check()
        elif args.check == "liveness":
            status_code, result = await endpoints.liveness_check()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            if 'checks' in result:
                print(f"Checks: {len(result['checks'])} total")
                for check in result['checks']:
                    status_icon = "✅" if check['status'] == 'healthy' else "❌"
                    print(f"  {status_icon} {check['name']}: {check['message']}")
        
        if args.exit_code and status_code != 200:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Health check CLI failed: {e}")
        if args.json:
            print(json.dumps({
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
        else:
            print(f"Error: {e}")
        
        if args.exit_code:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
