"""
Load testing framework for Goose Slackbot
Tests system performance under various load conditions
"""

import asyncio
import aiohttp
import time
import json
import statistics
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import get_settings
from database import get_database_manager, UserMappingRepository, UserSessionRepository
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load tests"""
    # Test parameters
    concurrent_users: int = 10
    queries_per_user: int = 5
    ramp_up_time: int = 30  # seconds
    test_duration: int = 300  # seconds
    
    # API endpoints
    api_base_url: str = "http://localhost:8000"
    slack_webhook_url: str = "http://localhost:3000/slack/events"
    
    # Database settings
    database_url: str = "postgresql://test:test@localhost:5432/goose_slackbot_test"
    
    # Test data
    sample_questions: List[str] = None
    user_pool_size: int = 100
    
    # Performance thresholds
    max_response_time: float = 10.0  # seconds
    max_error_rate: float = 0.05  # 5%
    min_throughput: float = 1.0  # requests per second


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    user_id: str
    start_time: float
    end_time: float
    response_time: float
    success: bool
    error_message: Optional[str] = None
    response_size: Optional[int] = None
    status_code: Optional[int] = None


@dataclass
class LoadTestResults:
    """Aggregated load test results"""
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    # Performance metrics
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Throughput metrics
    requests_per_second: float
    error_rate: float
    
    # Resource usage
    peak_memory_usage: Optional[float] = None
    avg_cpu_usage: Optional[float] = None
    
    # Test results
    results: List[TestResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'results': [asdict(r) for r in (self.results or [])]
        }


class SlackEventSimulator:
    """Simulates Slack events for load testing"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message_event(self, user_id: str, channel_id: str, text: str) -> TestResult:
        """Send a simulated Slack message event"""
        test_id = f"msg_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        start_time = time.time()
        
        event_payload = {
            "token": "test_token",
            "team_id": "T123456789",
            "api_app_id": "A123456789",
            "event": {
                "type": "message",
                "user": user_id,
                "text": text,
                "ts": str(start_time),
                "channel": channel_id,
                "channel_type": "im" if channel_id.startswith("D") else "channel"
            },
            "type": "event_callback",
            "event_id": test_id,
            "event_time": int(start_time)
        }
        
        try:
            async with self.session.post(
                self.webhook_url,
                json=event_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                response_text = await response.text()
                
                return TestResult(
                    test_id=test_id,
                    user_id=user_id,
                    start_time=start_time,
                    end_time=end_time,
                    response_time=end_time - start_time,
                    success=response.status == 200,
                    status_code=response.status,
                    response_size=len(response_text),
                    error_message=None if response.status == 200 else f"HTTP {response.status}: {response_text[:200]}"
                )
        
        except Exception as e:
            end_time = time.time()
            return TestResult(
                test_id=test_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                response_time=end_time - start_time,
                success=False,
                error_message=str(e)
            )
    
    async def send_app_mention_event(self, user_id: str, channel_id: str, text: str) -> TestResult:
        """Send a simulated app mention event"""
        test_id = f"mention_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        start_time = time.time()
        
        event_payload = {
            "token": "test_token",
            "team_id": "T123456789",
            "api_app_id": "A123456789",
            "event": {
                "type": "app_mention",
                "user": user_id,
                "text": f"<@B123456789> {text}",
                "ts": str(start_time),
                "channel": channel_id
            },
            "type": "event_callback",
            "event_id": test_id,
            "event_time": int(start_time)
        }
        
        try:
            async with self.session.post(
                self.webhook_url,
                json=event_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                response_text = await response.text()
                
                return TestResult(
                    test_id=test_id,
                    user_id=user_id,
                    start_time=start_time,
                    end_time=end_time,
                    response_time=end_time - start_time,
                    success=response.status == 200,
                    status_code=response.status,
                    response_size=len(response_text),
                    error_message=None if response.status == 200 else f"HTTP {response.status}: {response_text[:200]}"
                )
        
        except Exception as e:
            end_time = time.time()
            return TestResult(
                test_id=test_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                response_time=end_time - start_time,
                success=False,
                error_message=str(e)
            )


class DatabaseLoadTester:
    """Tests database performance under load"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.db_manager = None
    
    async def setup(self):
        """Setup database connection"""
        from database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(dsn=self.database_url)
        self.db_manager = DatabaseManager(config)
        await self.db_manager.initialize()
    
    async def cleanup(self):
        """Cleanup database connection"""
        if self.db_manager:
            await self.db_manager.close()
    
    async def test_concurrent_user_operations(self, concurrent_users: int, operations_per_user: int) -> List[TestResult]:
        """Test concurrent user operations"""
        user_repo = UserMappingRepository(self.db_manager)
        session_repo = UserSessionRepository(self.db_manager)
        
        async def user_operations(user_num: int) -> List[TestResult]:
            results = []
            user_id = f"load_user_{user_num}"
            slack_user_id = f"U{user_num:09d}"
            
            for op_num in range(operations_per_user):
                test_id = f"db_op_{user_num}_{op_num}"
                start_time = time.time()
                
                try:
                    # Create/update user mapping
                    await user_repo.create_or_update_mapping(
                        slack_user_id=slack_user_id,
                        internal_user_id=user_id,
                        email=f"{user_id}@company.com",
                        roles=["analyst"],
                        permissions=["query_execute"]
                    )
                    
                    # Create session
                    session_id = await session_repo.create_session(
                        user_id=user_id,
                        slack_user_id=slack_user_id,
                        channel_id=f"C{user_num:09d}"
                    )
                    
                    # Update session activity
                    await session_repo.update_session_activity(session_id)
                    
                    end_time = time.time()
                    
                    results.append(TestResult(
                        test_id=test_id,
                        user_id=user_id,
                        start_time=start_time,
                        end_time=end_time,
                        response_time=end_time - start_time,
                        success=True
                    ))
                
                except Exception as e:
                    end_time = time.time()
                    results.append(TestResult(
                        test_id=test_id,
                        user_id=user_id,
                        start_time=start_time,
                        end_time=end_time,
                        response_time=end_time - start_time,
                        success=False,
                        error_message=str(e)
                    ))
            
            return results
        
        # Run concurrent user operations
        tasks = [user_operations(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_results = []
        for user_result in user_results:
            all_results.extend(user_result)
        
        return all_results


class LoadTestRunner:
    """Main load test runner"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.sample_questions = config.sample_questions or self._get_default_questions()
    
    def _get_default_questions(self) -> List[str]:
        """Get default test questions"""
        return [
            "What was our revenue last month?",
            "How many users signed up this week?",
            "Show me top 10 customers by sales",
            "What's our average order value?",
            "How many active users do we have?",
            "What are our most popular products?",
            "Show me conversion rates by channel",
            "What's our customer churn rate?",
            "How many orders were placed today?",
            "What's our monthly recurring revenue?",
            "Show me user engagement metrics",
            "What are our peak usage hours?",
            "How many support tickets were opened?",
            "What's our average response time?",
            "Show me sales by region",
            "What's our customer lifetime value?",
            "How many new signups yesterday?",
            "What are our top performing campaigns?",
            "Show me inventory levels",
            "What's our profit margin this quarter?"
        ]
    
    async def setup_test_users(self) -> List[str]:
        """Setup test users in database"""
        db_tester = DatabaseLoadTester(self.config.database_url)
        await db_tester.setup()
        
        try:
            user_repo = UserMappingRepository(db_tester.db_manager)
            user_ids = []
            
            for i in range(self.config.user_pool_size):
                user_id = f"load_test_user_{i}"
                slack_user_id = f"U{i:09d}"
                
                await user_repo.create_or_update_mapping(
                    slack_user_id=slack_user_id,
                    internal_user_id=user_id,
                    email=f"{user_id}@company.com",
                    full_name=f"Load Test User {i}",
                    roles=["analyst"],
                    permissions=["query_execute", "query_view"]
                )
                
                user_ids.append(slack_user_id)
            
            logger.info(f"Created {len(user_ids)} test users")
            return user_ids
        
        finally:
            await db_tester.cleanup()
    
    async def run_slack_load_test(self, user_ids: List[str]) -> List[TestResult]:
        """Run Slack API load test"""
        results = []
        
        async with SlackEventSimulator(self.config.slack_webhook_url) as simulator:
            
            async def user_session(user_id: str) -> List[TestResult]:
                """Simulate a user session"""
                session_results = []
                channel_id = f"D{user_id[1:]}"  # Convert to DM channel
                
                # Ramp up delay
                await asyncio.sleep(random.uniform(0, self.config.ramp_up_time))
                
                for i in range(self.config.queries_per_user):
                    question = random.choice(self.sample_questions)
                    
                    # Send message event
                    result = await simulator.send_message_event(user_id, channel_id, question)
                    session_results.append(result)
                    
                    # Wait between queries
                    await asyncio.sleep(random.uniform(1, 5))
                
                return session_results
            
            # Run concurrent user sessions
            selected_users = random.sample(user_ids, min(self.config.concurrent_users, len(user_ids)))
            tasks = [user_session(user_id) for user_id in selected_users]
            
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for user_result in user_results:
                if isinstance(user_result, Exception):
                    logger.error(f"User session failed: {user_result}")
                else:
                    results.extend(user_result)
        
        return results
    
    async def run_database_load_test(self) -> List[TestResult]:
        """Run database load test"""
        db_tester = DatabaseLoadTester(self.config.database_url)
        await db_tester.setup()
        
        try:
            results = await db_tester.test_concurrent_user_operations(
                self.config.concurrent_users,
                self.config.queries_per_user
            )
            return results
        finally:
            await db_tester.cleanup()
    
    def analyze_results(self, results: List[TestResult]) -> LoadTestResults:
        """Analyze test results"""
        if not results:
            raise ValueError("No test results to analyze")
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        response_times = [r.response_time for r in successful_results]
        
        if not response_times:
            response_times = [0.0]
        
        # Calculate metrics
        total_time = max(r.end_time for r in results) - min(r.start_time for r in results)
        
        return LoadTestResults(
            config=self.config,
            start_time=datetime.fromtimestamp(min(r.start_time for r in results), timezone.utc),
            end_time=datetime.fromtimestamp(max(r.end_time for r in results), timezone.utc),
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0],
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 1 else response_times[0],
            requests_per_second=len(results) / total_time if total_time > 0 else 0,
            error_rate=len(failed_results) / len(results) if results else 0,
            results=results
        )
    
    def check_performance_thresholds(self, results: LoadTestResults) -> Dict[str, bool]:
        """Check if results meet performance thresholds"""
        checks = {
            "max_response_time": results.p95_response_time <= self.config.max_response_time,
            "error_rate": results.error_rate <= self.config.max_error_rate,
            "min_throughput": results.requests_per_second >= self.config.min_throughput
        }
        
        return checks
    
    def generate_report(self, results: LoadTestResults) -> str:
        """Generate load test report"""
        checks = self.check_performance_thresholds(results)
        
        report = f"""
# Load Test Report

## Test Configuration
- Concurrent Users: {self.config.concurrent_users}
- Queries per User: {self.config.queries_per_user}
- Test Duration: {(results.end_time - results.start_time).total_seconds():.1f}s
- Ramp-up Time: {self.config.ramp_up_time}s

## Results Summary
- Total Requests: {results.total_requests}
- Successful Requests: {results.successful_requests}
- Failed Requests: {results.failed_requests}
- Error Rate: {results.error_rate:.2%}

## Performance Metrics
- Average Response Time: {results.avg_response_time:.3f}s
- Min Response Time: {results.min_response_time:.3f}s
- Max Response Time: {results.max_response_time:.3f}s
- 95th Percentile: {results.p95_response_time:.3f}s
- 99th Percentile: {results.p99_response_time:.3f}s
- Throughput: {results.requests_per_second:.2f} req/s

## Performance Thresholds
- Max Response Time (≤{self.config.max_response_time}s): {'✅ PASS' if checks['max_response_time'] else '❌ FAIL'}
- Error Rate (≤{self.config.max_error_rate:.1%}): {'✅ PASS' if checks['error_rate'] else '❌ FAIL'}
- Min Throughput (≥{self.config.min_throughput} req/s): {'✅ PASS' if checks['min_throughput'] else '❌ FAIL'}

## Overall Result
{'✅ ALL TESTS PASSED' if all(checks.values()) else '❌ SOME TESTS FAILED'}
"""
        
        if results.failed_requests > 0:
            failed_results = [r for r in results.results if not r.success]
            error_summary = {}
            
            for result in failed_results:
                error = result.error_message or "Unknown error"
                error_summary[error] = error_summary.get(error, 0) + 1
            
            report += "\n## Error Summary\n"
            for error, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
                report += f"- {error}: {count} occurrences\n"
        
        return report
    
    async def run_full_load_test(self) -> LoadTestResults:
        """Run complete load test suite"""
        logger.info("Starting load test setup...")
        
        # Setup test users
        user_ids = await self.setup_test_users()
        
        logger.info(f"Running Slack load test with {self.config.concurrent_users} concurrent users...")
        
        # Run Slack load test
        slack_results = await self.run_slack_load_test(user_ids)
        
        logger.info(f"Completed {len(slack_results)} Slack API requests")
        
        # Analyze results
        results = self.analyze_results(slack_results)
        
        logger.info("Load test completed")
        
        return results


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Goose Slackbot Load Testing")
    parser.add_argument("--concurrent-users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--queries-per-user", type=int, default=5, help="Number of queries per user")
    parser.add_argument("--ramp-up-time", type=int, default=30, help="Ramp-up time in seconds")
    parser.add_argument("--slack-webhook-url", default="http://localhost:3000/slack/events", help="Slack webhook URL")
    parser.add_argument("--database-url", default="postgresql://test:test@localhost:5432/goose_slackbot_test", help="Database URL")
    parser.add_argument("--output-file", help="Output file for results (JSON)")
    parser.add_argument("--report-file", help="Output file for report (Markdown)")
    
    args = parser.parse_args()
    
    # Create configuration
    config = LoadTestConfig(
        concurrent_users=args.concurrent_users,
        queries_per_user=args.queries_per_user,
        ramp_up_time=args.ramp_up_time,
        slack_webhook_url=args.slack_webhook_url,
        database_url=args.database_url
    )
    
    # Run load test
    runner = LoadTestRunner(config)
    results = await runner.run_full_load_test()
    
    # Generate report
    report = runner.generate_report(results)
    print(report)
    
    # Save results
    if args.output_file:
        with open(args.output_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
        print(f"\nResults saved to {args.output_file}")
    
    if args.report_file:
        with open(args.report_file, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.report_file}")
    
    # Exit with appropriate code
    checks = runner.check_performance_thresholds(results)
    if all(checks.values()):
        print("\n✅ All performance thresholds met")
        sys.exit(0)
    else:
        print("\n❌ Some performance thresholds not met")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
