"""
Load testing with Locust for Goose Slackbot
Simulates realistic user behavior and query patterns
"""

from locust import HttpUser, task, between, events
import random
import json
import time
from datetime import datetime, timedelta


class SlackBotUser(HttpUser):
    """Simulates a Slack user interacting with the bot"""
    
    wait_time = between(5, 15)  # Wait 5-15 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = f"U{random.randint(100000, 999999)}"
        self.channel_id = f"C{random.randint(100000, 999999)}"
        self.session_id = None
        
        # Authenticate
        self.authenticate()
    
    def authenticate(self):
        """Authenticate user"""
        response = self.client.post("/api/auth/login", json={
            "slack_user_id": self.user_id,
            "channel_id": self.channel_id
        })
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
    
    @task(10)
    def simple_query(self):
        """Execute a simple query"""
        queries = [
            "Show me total sales",
            "What are the top 10 customers?",
            "Display revenue by month",
            "List all products",
            "Show user activity today"
        ]
        
        query = random.choice(queries)
        
        self.client.post("/api/query", json={
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "query": query
        }, name="/api/query [simple]")
    
    @task(5)
    def complex_query(self):
        """Execute a complex query"""
        queries = [
            "Show me sales trends for the last 6 months broken down by region and product category",
            "What is the customer lifetime value for users who signed up in Q1 2024?",
            "Compare revenue growth year over year for each product line",
            "Analyze conversion rates by traffic source and landing page",
            "Show me the cohort retention analysis for the past year"
        ]
        
        query = random.choice(queries)
        
        self.client.post("/api/query", json={
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "query": query
        }, name="/api/query [complex]")
    
    @task(3)
    def get_query_history(self):
        """Retrieve query history"""
        self.client.get(f"/api/history/{self.user_id}", params={
            "limit": 10
        }, name="/api/history")
    
    @task(2)
    def get_popular_queries(self):
        """Get popular queries"""
        self.client.get("/api/queries/popular", params={
            "days": 7,
            "limit": 10
        }, name="/api/queries/popular")
    
    @task(1)
    def health_check(self):
        """Check service health"""
        self.client.get("/health", name="/health")
    
    @task(1)
    def get_metrics(self):
        """Get service metrics"""
        self.client.get("/metrics", name="/metrics")


class HeavyUser(HttpUser):
    """Simulates a power user with high query volume"""
    
    wait_time = between(1, 3)  # Faster queries
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = f"U_HEAVY_{random.randint(1, 100)}"
        self.channel_id = f"C{random.randint(100000, 999999)}"
        self.session_id = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate user"""
        response = self.client.post("/api/auth/login", json={
            "slack_user_id": self.user_id,
            "channel_id": self.channel_id
        })
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
    
    @task(20)
    def rapid_queries(self):
        """Execute queries rapidly"""
        query = f"SELECT * FROM table_{random.randint(1, 100)} LIMIT {random.randint(10, 1000)}"
        
        self.client.post("/api/query", json={
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "session_id": self.session_id,
            "query": query
        }, name="/api/query [rapid]")


class BurstUser(HttpUser):
    """Simulates burst traffic patterns"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = f"U_BURST_{random.randint(1, 1000)}"
        self.channel_id = f"C{random.randint(100000, 999999)}"
        self.session_id = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate user"""
        response = self.client.post("/api/auth/login", json={
            "slack_user_id": self.user_id,
            "channel_id": self.channel_id
        })
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
    
    @task
    def burst_query(self):
        """Execute burst of queries"""
        for _ in range(random.randint(3, 10)):
            query = f"Query burst {random.randint(1, 1000)}"
            
            self.client.post("/api/query", json={
                "user_id": self.user_id,
                "channel_id": self.channel_id,
                "session_id": self.session_id,
                "query": query
            }, name="/api/query [burst]")
            
            time.sleep(0.1)  # Small delay between burst queries


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called on each request"""
    if exception:
        print(f"Request failed: {name} - {exception}")


# Custom load shapes for different scenarios
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern: gradually increase users
    """
    
    step_time = 60  # seconds
    step_load = 10  # users per step
    spawn_rate = 2
    time_limit = 600  # 10 minutes
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time > self.time_limit:
            return None
        
        current_step = run_time // self.step_time
        return (current_step * self.step_load, self.spawn_rate)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern: sudden traffic spikes
    """
    
    time_limit = 600
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time > self.time_limit:
            return None
        
        # Create spikes every 2 minutes
        if run_time % 120 < 30:  # 30 second spike
            return (100, 10)  # High load
        else:
            return (20, 2)  # Normal load


class WaveLoadShape(LoadTestShape):
    """
    Wave load pattern: gradual increase and decrease
    """
    
    time_limit = 600
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time > self.time_limit:
            return None
        
        # Sine wave pattern
        import math
        amplitude = 50
        period = 120
        offset = 50
        
        user_count = int(amplitude * math.sin(2 * math.pi * run_time / period) + offset)
        return (max(user_count, 1), 2)


if __name__ == "__main__":
    import os
    import subprocess
    
    # Run locust with web interface
    host = os.getenv("TARGET_HOST", "http://localhost:3000")
    
    print(f"Starting Locust load test against {host}")
    print("Open http://localhost:8089 to view the web interface")
    
    subprocess.run([
        "locust",
        "-f", __file__,
        "--host", host,
        "--web-host", "0.0.0.0",
        "--web-port", "8089"
    ])
