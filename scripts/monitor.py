#!/usr/bin/env python3
"""
Monitoring and health check script
Monitors system health, performance metrics, and alerts
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import time

import asyncpg
import aiohttp
import structlog
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class HealthCheck:
    """Health check result"""
    
    def __init__(self, name: str, status: str, message: str = "", details: Dict = None):
        self.name = name
        self.status = status  # healthy, degraded, unhealthy
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def is_healthy(self) -> bool:
        return self.status == "healthy"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class SystemMonitor:
    """System monitoring and health checks"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
    
    async def check_database(self) -> HealthCheck:
        """Check database connectivity and performance"""
        try:
            start = time.time()
            conn = await asyncpg.connect(settings.database_url)
            
            # Test query
            await conn.fetchval("SELECT 1")
            
            # Get connection stats
            pool_size = await conn.fetchval("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            # Get database size
            db_size = await conn.fetchval("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            
            await conn.close()
            
            latency = (time.time() - start) * 1000  # ms
            
            details = {
                "latency_ms": round(latency, 2),
                "active_connections": pool_size,
                "database_size": db_size
            }
            
            if latency > 1000:
                return HealthCheck("database", "degraded", 
                                 f"High latency: {latency:.0f}ms", details)
            
            return HealthCheck("database", "healthy", "Database operational", details)
            
        except Exception as e:
            return HealthCheck("database", "unhealthy", str(e))
    
    async def check_redis(self) -> HealthCheck:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis
            
            start = time.time()
            client = redis.from_url(settings.redis_url)
            
            # Test ping
            await client.ping()
            
            # Get info
            info = await client.info()
            
            await client.close()
            
            latency = (time.time() - start) * 1000
            
            details = {
                "latency_ms": round(latency, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "uptime_days": info.get("uptime_in_days", 0)
            }
            
            return HealthCheck("redis", "healthy", "Redis operational", details)
            
        except Exception as e:
            return HealthCheck("redis", "unhealthy", str(e))
    
    async def check_goose_service(self) -> HealthCheck:
        """Check Goose MCP service"""
        try:
            start = time.time()
            
            async with aiohttp.ClientSession() as session:
                url = f"{settings.goose_mcp_server_url}/health"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        latency = (time.time() - start) * 1000
                        
                        details = {
                            "latency_ms": round(latency, 2),
                            "version": data.get("version", "unknown"),
                            "uptime": data.get("uptime", "unknown")
                        }
                        
                        return HealthCheck("goose_service", "healthy", 
                                         "Goose service operational", details)
                    else:
                        return HealthCheck("goose_service", "unhealthy", 
                                         f"HTTP {resp.status}")
        
        except asyncio.TimeoutError:
            return HealthCheck("goose_service", "unhealthy", "Connection timeout")
        except Exception as e:
            return HealthCheck("goose_service", "unhealthy", str(e))
    
    async def check_slack_api(self) -> HealthCheck:
        """Check Slack API connectivity"""
        try:
            from slack_sdk.web.async_client import AsyncWebClient
            
            start = time.time()
            client = AsyncWebClient(token=settings.slack_bot_token)
            
            # Test auth
            response = await client.auth_test()
            
            latency = (time.time() - start) * 1000
            
            details = {
                "latency_ms": round(latency, 2),
                "team": response.get("team", "unknown"),
                "user": response.get("user", "unknown")
            }
            
            return HealthCheck("slack_api", "healthy", "Slack API operational", details)
            
        except Exception as e:
            return HealthCheck("slack_api", "unhealthy", str(e))
    
    async def check_disk_space(self) -> HealthCheck:
        """Check disk space"""
        try:
            import shutil
            
            stat = shutil.disk_usage("/")
            
            total_gb = stat.total / (1024**3)
            used_gb = stat.used / (1024**3)
            free_gb = stat.free / (1024**3)
            percent_used = (stat.used / stat.total) * 100
            
            details = {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent_used": round(percent_used, 2)
            }
            
            if percent_used > 90:
                return HealthCheck("disk_space", "unhealthy", 
                                 f"Critical: {percent_used:.1f}% used", details)
            elif percent_used > 80:
                return HealthCheck("disk_space", "degraded", 
                                 f"Warning: {percent_used:.1f}% used", details)
            
            return HealthCheck("disk_space", "healthy", 
                             f"{percent_used:.1f}% used", details)
            
        except Exception as e:
            return HealthCheck("disk_space", "unhealthy", str(e))
    
    async def check_memory(self) -> HealthCheck:
        """Check memory usage"""
        try:
            import psutil
            
            mem = psutil.virtual_memory()
            
            details = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent_used": mem.percent
            }
            
            if mem.percent > 90:
                return HealthCheck("memory", "unhealthy", 
                                 f"Critical: {mem.percent}% used", details)
            elif mem.percent > 80:
                return HealthCheck("memory", "degraded", 
                                 f"Warning: {mem.percent}% used", details)
            
            return HealthCheck("memory", "healthy", 
                             f"{mem.percent}% used", details)
            
        except Exception as e:
            return HealthCheck("memory", "unhealthy", str(e))
    
    async def check_cpu(self) -> HealthCheck:
        """Check CPU usage"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            details = {
                "cpu_count": cpu_count,
                "cpu_percent": cpu_percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
            if cpu_percent > 90:
                return HealthCheck("cpu", "unhealthy", 
                                 f"Critical: {cpu_percent}% used", details)
            elif cpu_percent > 80:
                return HealthCheck("cpu", "degraded", 
                                 f"Warning: {cpu_percent}% used", details)
            
            return HealthCheck("cpu", "healthy", 
                             f"{cpu_percent}% used", details)
            
        except Exception as e:
            return HealthCheck("cpu", "unhealthy", str(e))
    
    async def run_all_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_goose_service(),
            self.check_slack_api(),
            self.check_disk_space(),
            self.check_memory(),
            self.check_cpu(),
            return_exceptions=True
        )
        
        self.checks = [c for c in checks if isinstance(c, HealthCheck)]
        return self.checks
    
    def get_overall_status(self) -> str:
        """Get overall system status"""
        if not self.checks:
            return "unknown"
        
        if any(c.status == "unhealthy" for c in self.checks):
            return "unhealthy"
        elif any(c.status == "degraded" for c in self.checks):
            return "degraded"
        else:
            return "healthy"
    
    def print_report(self):
        """Print health check report"""
        print("\n" + "=" * 80)
        print("SYSTEM HEALTH CHECK REPORT")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Overall Status: {self.get_overall_status().upper()}")
        print("\n" + "-" * 80)
        
        # Prepare table data
        data = []
        for check in self.checks:
            status_icon = {
                "healthy": "✓",
                "degraded": "⚠",
                "unhealthy": "✗"
            }.get(check.status, "?")
            
            data.append([
                f"{status_icon} {check.name}",
                check.status.upper(),
                check.message,
                json.dumps(check.details) if check.details else ""
            ])
        
        headers = ["Component", "Status", "Message", "Details"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print("=" * 80 + "\n")
    
    def to_json(self) -> str:
        """Export report as JSON"""
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.get_overall_status(),
            "checks": [c.to_dict() for c in self.checks]
        }, indent=2)


class MetricsCollector:
    """Collect and display system metrics"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def get_query_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get query execution metrics"""
        conn = await asyncpg.connect(self.database_url)
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Total queries
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM query_history 
            WHERE created_at >= $1
        """, cutoff)
        
        # Successful queries
        successful = await conn.fetchval("""
            SELECT COUNT(*) FROM query_history 
            WHERE created_at >= $1 AND success = true
        """, cutoff)
        
        # Average execution time
        avg_time = await conn.fetchval("""
            SELECT AVG(execution_time) FROM query_history 
            WHERE created_at >= $1 AND success = true
        """, cutoff)
        
        # Top users
        top_users = await conn.fetch("""
            SELECT user_id, COUNT(*) as query_count 
            FROM query_history 
            WHERE created_at >= $1 
            GROUP BY user_id 
            ORDER BY query_count DESC 
            LIMIT 10
        """, cutoff)
        
        await conn.close()
        
        return {
            "total_queries": total,
            "successful_queries": successful,
            "failed_queries": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_execution_time": round(avg_time or 0, 3),
            "top_users": [dict(u) for u in top_users]
        }
    
    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get session metrics"""
        conn = await asyncpg.connect(self.database_url)
        
        # Active sessions
        active = await conn.fetchval("""
            SELECT COUNT(*) FROM user_sessions WHERE is_active = true
        """)
        
        # Total sessions
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM user_sessions
        """)
        
        # Sessions by activity
        recent = await conn.fetchval("""
            SELECT COUNT(*) FROM user_sessions 
            WHERE last_activity >= NOW() - INTERVAL '1 hour'
        """)
        
        await conn.close()
        
        return {
            "active_sessions": active,
            "total_sessions": total,
            "recent_activity": recent
        }
    
    async def print_metrics(self, hours: int = 24):
        """Print metrics report"""
        query_metrics = await self.get_query_metrics(hours)
        session_metrics = await self.get_session_metrics()
        
        print("\n" + "=" * 80)
        print(f"SYSTEM METRICS (Last {hours} hours)")
        print("=" * 80)
        
        print("\nQuery Metrics:")
        print(f"  Total Queries:     {query_metrics['total_queries']}")
        print(f"  Successful:        {query_metrics['successful_queries']}")
        print(f"  Failed:            {query_metrics['failed_queries']}")
        print(f"  Success Rate:      {query_metrics['success_rate']:.1f}%")
        print(f"  Avg Execution:     {query_metrics['avg_execution_time']:.3f}s")
        
        print("\nSession Metrics:")
        print(f"  Active Sessions:   {session_metrics['active_sessions']}")
        print(f"  Total Sessions:    {session_metrics['total_sessions']}")
        print(f"  Recent Activity:   {session_metrics['recent_activity']}")
        
        if query_metrics['top_users']:
            print("\nTop Users:")
            for user in query_metrics['top_users'][:5]:
                print(f"  {user['user_id']}: {user['query_count']} queries")
        
        print("=" * 80 + "\n")


async def continuous_monitor(interval: int = 60):
    """Continuously monitor system health"""
    monitor = SystemMonitor()
    
    print(f"Starting continuous monitoring (interval: {interval}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            await monitor.run_all_checks()
            monitor.print_report()
            
            # Alert on unhealthy status
            if monitor.get_overall_status() == "unhealthy":
                print("⚠️  ALERT: System is unhealthy!")
                # Here you could send alerts via Slack, email, etc.
            
            await asyncio.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="System monitoring and health checks")
    parser.add_argument("command", choices=[
        "check", "metrics", "monitor", "json"
    ], help="Monitoring command")
    parser.add_argument("--interval", type=int, default=60, 
                       help="Monitoring interval in seconds")
    parser.add_argument("--hours", type=int, default=24,
                       help="Hours of metrics to collect")
    parser.add_argument("--database-url", help="Database URL (overrides config)")
    
    args = parser.parse_args()
    
    if args.command == "check":
        monitor = SystemMonitor()
        await monitor.run_all_checks()
        monitor.print_report()
        
        # Exit with error code if unhealthy
        if monitor.get_overall_status() == "unhealthy":
            sys.exit(1)
    
    elif args.command == "json":
        monitor = SystemMonitor()
        await monitor.run_all_checks()
        print(monitor.to_json())
    
    elif args.command == "metrics":
        database_url = args.database_url or settings.database_url
        collector = MetricsCollector(database_url)
        await collector.print_metrics(hours=args.hours)
    
    elif args.command == "monitor":
        await continuous_monitor(interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
