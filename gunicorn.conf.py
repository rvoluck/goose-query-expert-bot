"""
Gunicorn configuration for production deployment
"""
import multiprocessing
import os

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '3000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
timeout = 300
keepalive = 5

# Logging
accesslog = os.getenv('ACCESS_LOG', '/app/logs/access.log')
errorlog = os.getenv('ERROR_LOG', '/app/logs/error.log')
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'goose-slackbot'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = os.getenv('SSL_KEYFILE', None)
certfile = os.getenv('SSL_CERTFILE', None)

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting Goose Slackbot server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading Goose Slackbot server...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Goose Slackbot server is ready. Listening on {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forking new master process...")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker received SIGABRT signal (pid: {worker.pid})")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker exited (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker exit (pid: {worker.pid})")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    print(f"Number of workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down Goose Slackbot server...")
