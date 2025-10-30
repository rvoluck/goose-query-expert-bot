"""
Stress testing scenarios for Goose Slackbot
Tests system behavior under extreme load conditions
"""

import asyncio
import aiohttp
import time
import random
import json
import psutil
import gc
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.load.load_test_runner import LoadTestConfig, TestResult, LoadTestRunner, SlackEventSimulator
from database import get_database_manager, UserMappingRepository
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class StressTestConfig(LoadTestConfig):
    """Extended configuration for stress tests"""
    # Stress test specific parameters
    spike_multiplier: int = 5  # Multiply concurrent users during spike
    spike_duration: int = 60  # Duration of spike in seconds
    memory_limit_mb: int = 1024  # Memory limit for testing
    cpu_limit_percent: int = 80  # CPU limit for testing
    
    # Failure simulation
    simulate_network_failures: bool = False
    network_failure_rate: float = 0.1  # 10% failure rate
    simulate_database_slowdown: bool = False
    database_slowdown_factor: float = 2.0  # 2x slower


class ResourceMonitor:
    """Monitors system resources during stress tests"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.process = psutil.Process()
    
    async def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring"""
        self.monitoring = True
        self.metrics = []
        
        while self.monitoring:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                
                # Get process metrics
                process_memory = self.process.memory_info()
                process_cpu = self.process.cpu_percent()
                
                metric = {
                    'timestamp': time.time(),
                    'system_cpu_percent': cpu_percent,
                    'system_memory_percent': memory.percent,
                    'system_memory_available_mb': memory.available / 1024 / 1024,
                    'process_memory_rss_mb': process_memory.rss / 1024 / 1024,
                    'process_memory_vms_mb': process_memory.vms / 1024 / 1024,
                    'process_cpu_percent': process_cpu,
                    'open_file_descriptors': len(self.process.open_files()),
                    'thread_count': self.process.num_threads()
                }
                
                self.metrics.append(metric)
                
            except Exception as e:
                logger.warning(f"Error collecting metrics: {e}")
            
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
    
    def get_peak_metrics(self) -> Dict[str, float]:
        """Get peak resource usage metrics"""
        if not self.metrics:
            return {}
        
        return {
            'peak_system_cpu': max(m['system_cpu_percent'] for m in self.metrics),
            'peak_system_memory': max(m['system_memory_percent'] for m in self.metrics),
            'peak_process_memory_mb': max(m['process_memory_rss_mb'] for m in self.metrics),
            'peak_process_cpu': max(m['process_cpu_percent'] for m in self.metrics),
            'max_open_files': max(m['open_file_descriptors'] for m in self.metrics),
            'max_threads': max(m['thread_count'] for m in self.metrics)
        }
    
    def check_resource_limits(self, config: StressTestConfig) -> Dict[str, bool]:
        """Check if resource limits were exceeded"""
        if not self.metrics:
            return {}
        
        peak_metrics = self.get_peak_metrics()
        
        return {
            'memory_limit_ok': peak_metrics.get('peak_process_memory_mb', 0) <= config.memory_limit_mb,
            'cpu_limit_ok': peak_metrics.get('peak_process_cpu', 0) <= config.cpu_limit_percent
        }


class NetworkFailureSimulator:
    """Simulates network failures for stress testing"""
    
    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate
        self.original_post = None
    
    def should_fail(self) -> bool:
        """Determine if this request should fail"""
        return random.random() < self.failure_rate
    
    async def simulate_failure(self):
        """Simulate a network failure"""
        failure_types = [
            aiohttp.ClientTimeout(),
            aiohttp.ClientConnectionError("Simulated connection failure"),
            aiohttp.ClientResponseError(None, None, status=503, message="Service Unavailable")
        ]
        
        raise random.choice(failure_types)


class StressTestRunner(LoadTestRunner):
    """Extended load test runner for stress testing"""
    
    def __init__(self, config: StressTestConfig):
        super().__init__(config)
        self.stress_config = config
        self.resource_monitor = ResourceMonitor()
        self.network_simulator = NetworkFailureSimulator(config.network_failure_rate)
    
    async def run_spike_test(self, user_ids: List[str]) -> List[TestResult]:
        """Run spike load test"""
        logger.info(f"Starting spike test: {self.config.concurrent_users} -> {self.config.concurrent_users * self.stress_config.spike_multiplier} users")
        
        results = []
        
        # Start with normal load
        normal_load_task = asyncio.create_task(
            self._run_continuous_load(user_ids[:self.config.concurrent_users], duration=30)
        )
        
        # Wait for normal load to stabilize
        await asyncio.sleep(10)
        
        # Add spike load
        spike_users = user_ids[self.config.concurrent_users:self.config.concurrent_users * self.stress_config.spike_multiplier]
        spike_load_task = asyncio.create_task(
            self._run_continuous_load(spike_users, duration=self.stress_config.spike_duration)
        )
        
        # Wait for spike to complete
        normal_results, spike_results = await asyncio.gather(normal_load_task, spike_load_task)
        
        results.extend(normal_results)
        results.extend(spike_results)
        
        logger.info(f"Spike test completed: {len(results)} total requests")
        return results
    
    async def _run_continuous_load(self, user_ids: List[str], duration: int) -> List[TestResult]:
        """Run continuous load for specified duration"""
        results = []
        start_time = time.time()
        
        async with SlackEventSimulator(self.config.slack_webhook_url) as simulator:
            
            async def continuous_user_load(user_id: str):
                """Generate continuous load from a single user"""
                user_results = []
                channel_id = f"D{user_id[1:]}"
                
                while time.time() - start_time < duration:
                    question = random.choice(self.sample_questions)
                    
                    # Simulate network failures if enabled
                    if self.stress_config.simulate_network_failures and self.network_simulator.should_fail():
                        test_id = f"fail_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                        result = TestResult(
                            test_id=test_id,
                            user_id=user_id,
                            start_time=time.time(),
                            end_time=time.time(),
                            response_time=0.0,
                            success=False,
                            error_message="Simulated network failure"
                        )
                        user_results.append(result)
                    else:
                        result = await simulator.send_message_event(user_id, channel_id, question)
                        user_results.append(result)
                    
                    # Random delay between requests
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                
                return user_results
            
            # Run continuous load for all users
            tasks = [continuous_user_load(user_id) for user_id in user_ids]
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for user_result in user_results:
                if isinstance(user_result, Exception):
                    logger.error(f"Continuous load failed: {user_result}")
                else:
                    results.extend(user_result)
        
        return results
    
    async def run_memory_stress_test(self, user_ids: List[str]) -> List[TestResult]:
        """Run memory stress test"""
        logger.info("Starting memory stress test")
        
        # Create memory pressure by keeping large objects in memory
        memory_hogs = []
        
        try:
            # Gradually increase memory usage
            for i in range(10):
                # Create 50MB of data
                data = [random.random() for _ in range(50 * 1024 * 1024 // 8)]  # 8 bytes per float
                memory_hogs.append(data)
                
                # Run some load while memory is constrained
                if i % 3 == 0:  # Every 3rd iteration
                    results = await self._run_burst_load(user_ids[:5], burst_size=10)
                    
                    # Check memory usage
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    logger.info(f"Memory usage: {current_memory:.1f} MB")
                    
                    if current_memory > self.stress_config.memory_limit_mb:
                        logger.warning(f"Memory limit exceeded: {current_memory:.1f} MB > {self.stress_config.memory_limit_mb} MB")
                        break
            
            # Final load test under memory pressure
            final_results = await self._run_burst_load(user_ids[:10], burst_size=20)
            
            return final_results
        
        finally:
            # Clean up memory
            memory_hogs.clear()
            gc.collect()
    
    async def _run_burst_load(self, user_ids: List[str], burst_size: int) -> List[TestResult]:
        """Run a burst of concurrent requests"""
        results = []
        
        async with SlackEventSimulator(self.config.slack_webhook_url) as simulator:
            
            async def burst_request(user_id: str, request_num: int):
                """Single burst request"""
                channel_id = f"D{user_id[1:]}"
                question = random.choice(self.sample_questions)
                return await simulator.send_message_event(user_id, channel_id, question)
            
            # Create burst of requests
            tasks = []
            for i in range(burst_size):
                user_id = random.choice(user_ids)
                task = burst_request(user_id, i)
                tasks.append(task)
            
            # Execute burst
            burst_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in burst_results:
                if isinstance(result, Exception):
                    logger.error(f"Burst request failed: {result}")
                else:
                    results.append(result)
        
        return results
    
    async def run_database_stress_test(self) -> List[TestResult]:
        """Run database stress test"""
        logger.info("Starting database stress test")
        
        from database import DatabaseManager, DatabaseConfig, UserMappingRepository, UserSessionRepository
        
        # Create multiple database connections
        db_managers = []
        try:
            # Create multiple connection pools
            for i in range(5):
                config = DatabaseConfig(dsn=self.config.database_url, max_size=20)
                db_manager = DatabaseManager(config)
                await db_manager.initialize()
                db_managers.append(db_manager)
            
            results = []
            
            async def database_stress_worker(worker_id: int, db_manager: DatabaseManager):
                """Worker that creates database stress"""
                worker_results = []
                user_repo = UserMappingRepository(db_manager)
                session_repo = UserSessionRepository(db_manager)
                
                for i in range(100):  # 100 operations per worker
                    test_id = f"db_stress_{worker_id}_{i}"
                    start_time = time.time()
                    
                    try:
                        user_id = f"stress_user_{worker_id}_{i}"
                        slack_user_id = f"U{worker_id:03d}{i:06d}"
                        
                        # Simulate database slowdown if enabled
                        if self.stress_config.simulate_database_slowdown:
                            await asyncio.sleep(0.1 * self.stress_config.database_slowdown_factor)
                        
                        # Create user mapping
                        await user_repo.create_or_update_mapping(
                            slack_user_id=slack_user_id,
                            internal_user_id=user_id,
                            email=f"{user_id}@stress.test",
                            roles=["stress_tester"],
                            permissions=["query_execute"]
                        )
                        
                        # Create session
                        session_id = await session_repo.create_session(
                            user_id=user_id,
                            slack_user_id=slack_user_id,
                            channel_id=f"C{worker_id:03d}{i:06d}"
                        )
                        
                        # Update session multiple times
                        for j in range(5):
                            await session_repo.update_session_activity(
                                session_id, 
                                context={"stress_test": True, "iteration": j}
                            )
                        
                        end_time = time.time()
                        
                        worker_results.append(TestResult(
                            test_id=test_id,
                            user_id=user_id,
                            start_time=start_time,
                            end_time=end_time,
                            response_time=end_time - start_time,
                            success=True
                        ))
                    
                    except Exception as e:
                        end_time = time.time()
                        worker_results.append(TestResult(
                            test_id=test_id,
                            user_id=f"stress_user_{worker_id}_{i}",
                            start_time=start_time,
                            end_time=end_time,
                            response_time=end_time - start_time,
                            success=False,
                            error_message=str(e)
                        ))
                
                return worker_results
            
            # Run concurrent database workers
            tasks = [database_stress_worker(i, db_managers[i]) for i in range(len(db_managers))]
            worker_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for worker_result in worker_results:
                if isinstance(worker_result, Exception):
                    logger.error(f"Database stress worker failed: {worker_result}")
                else:
                    results.extend(worker_result)
            
            return results
        
        finally:
            # Cleanup database connections
            for db_manager in db_managers:
                await db_manager.close()
    
    async def run_full_stress_test(self) -> Dict[str, Any]:
        """Run complete stress test suite"""
        logger.info("Starting comprehensive stress test...")
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())
        
        try:
            # Setup test users
            user_ids = await self.setup_test_users()
            
            stress_results = {}
            
            # 1. Spike Load Test
            logger.info("Running spike load test...")
            spike_results = await self.run_spike_test(user_ids)
            stress_results['spike_test'] = self.analyze_results(spike_results)
            
            # 2. Memory Stress Test
            logger.info("Running memory stress test...")
            memory_results = await self.run_memory_stress_test(user_ids)
            stress_results['memory_test'] = self.analyze_results(memory_results)
            
            # 3. Database Stress Test
            logger.info("Running database stress test...")
            db_results = await self.run_database_stress_test()
            stress_results['database_test'] = self.analyze_results(db_results)
            
            # 4. Combined Stress Test
            logger.info("Running combined stress test...")
            combined_tasks = [
                self._run_continuous_load(user_ids[:10], duration=60),
                self.run_memory_stress_test(user_ids[10:15]),
                self.run_database_stress_test()
            ]
            
            combined_results_list = await asyncio.gather(*combined_tasks, return_exceptions=True)
            combined_results = []
            for result_list in combined_results_list:
                if isinstance(result_list, Exception):
                    logger.error(f"Combined stress test component failed: {result_list}")
                else:
                    combined_results.extend(result_list)
            
            stress_results['combined_test'] = self.analyze_results(combined_results)
            
            return stress_results
        
        finally:
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()
            monitor_task.cancel()
            
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    def generate_stress_report(self, stress_results: Dict[str, Any]) -> str:
        """Generate comprehensive stress test report"""
        peak_metrics = self.resource_monitor.get_peak_metrics()
        resource_limits = self.resource_monitor.check_resource_limits(self.stress_config)
        
        report = f"""
# Stress Test Report

## Test Configuration
- Base Concurrent Users: {self.config.concurrent_users}
- Spike Multiplier: {self.stress_config.spike_multiplier}x
- Spike Duration: {self.stress_config.spike_duration}s
- Memory Limit: {self.stress_config.memory_limit_mb} MB
- CPU Limit: {self.stress_config.cpu_limit_percent}%

## Resource Usage
- Peak System CPU: {peak_metrics.get('peak_system_cpu', 0):.1f}%
- Peak System Memory: {peak_metrics.get('peak_system_memory', 0):.1f}%
- Peak Process Memory: {peak_metrics.get('peak_process_memory_mb', 0):.1f} MB
- Peak Process CPU: {peak_metrics.get('peak_process_cpu', 0):.1f}%
- Max Open Files: {peak_metrics.get('max_open_files', 0)}
- Max Threads: {peak_metrics.get('max_threads', 0)}

## Resource Limit Compliance
- Memory Limit: {'✅ OK' if resource_limits.get('memory_limit_ok', True) else '❌ EXCEEDED'}
- CPU Limit: {'✅ OK' if resource_limits.get('cpu_limit_ok', True) else '❌ EXCEEDED'}

## Test Results Summary

"""
        
        for test_name, results in stress_results.items():
            if hasattr(results, 'total_requests'):
                report += f"""
### {test_name.replace('_', ' ').title()}
- Total Requests: {results.total_requests}
- Success Rate: {(results.successful_requests / results.total_requests * 100):.1f}%
- Average Response Time: {results.avg_response_time:.3f}s
- 95th Percentile: {results.p95_response_time:.3f}s
- Throughput: {results.requests_per_second:.2f} req/s
"""
        
        # Overall assessment
        all_passed = all(resource_limits.values())
        for results in stress_results.values():
            if hasattr(results, 'error_rate'):
                all_passed = all_passed and results.error_rate < 0.1  # 10% error threshold for stress tests
        
        report += f"""
## Overall Assessment
{'✅ SYSTEM STABLE UNDER STRESS' if all_passed else '⚠️  SYSTEM SHOWED STRESS INDICATORS'}

## Recommendations
"""
        
        if not resource_limits.get('memory_limit_ok', True):
            report += "- Consider increasing memory allocation or optimizing memory usage\n"
        
        if not resource_limits.get('cpu_limit_ok', True):
            report += "- Consider CPU optimization or horizontal scaling\n"
        
        for test_name, results in stress_results.items():
            if hasattr(results, 'error_rate') and results.error_rate > 0.05:
                report += f"- Investigate errors in {test_name} (error rate: {results.error_rate:.1%})\n"
        
        return report


async def main():
    """Main entry point for stress testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Goose Slackbot Stress Testing")
    parser.add_argument("--concurrent-users", type=int, default=20, help="Base number of concurrent users")
    parser.add_argument("--spike-multiplier", type=int, default=5, help="Spike load multiplier")
    parser.add_argument("--spike-duration", type=int, default=60, help="Spike duration in seconds")
    parser.add_argument("--memory-limit-mb", type=int, default=1024, help="Memory limit in MB")
    parser.add_argument("--cpu-limit-percent", type=int, default=80, help="CPU limit percentage")
    parser.add_argument("--simulate-failures", action="store_true", help="Simulate network failures")
    parser.add_argument("--failure-rate", type=float, default=0.1, help="Network failure rate")
    parser.add_argument("--slack-webhook-url", default="http://localhost:3000/slack/events")
    parser.add_argument("--database-url", default="postgresql://test:test@localhost:5432/goose_slackbot_test")
    parser.add_argument("--output-file", help="Output file for results")
    
    args = parser.parse_args()
    
    # Create stress test configuration
    config = StressTestConfig(
        concurrent_users=args.concurrent_users,
        spike_multiplier=args.spike_multiplier,
        spike_duration=args.spike_duration,
        memory_limit_mb=args.memory_limit_mb,
        cpu_limit_percent=args.cpu_limit_percent,
        simulate_network_failures=args.simulate_failures,
        network_failure_rate=args.failure_rate,
        slack_webhook_url=args.slack_webhook_url,
        database_url=args.database_url
    )
    
    # Run stress tests
    runner = StressTestRunner(config)
    stress_results = await runner.run_full_stress_test()
    
    # Generate report
    report = runner.generate_stress_report(stress_results)
    print(report)
    
    # Save results
    if args.output_file:
        output_data = {
            'config': config.__dict__,
            'peak_metrics': runner.resource_monitor.get_peak_metrics(),
            'stress_results': {
                name: results.to_dict() if hasattr(results, 'to_dict') else str(results)
                for name, results in stress_results.items()
            },
            'report': report
        }
        
        with open(args.output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\nResults saved to {args.output_file}")


if __name__ == "__main__":
    asyncio.run(main())
