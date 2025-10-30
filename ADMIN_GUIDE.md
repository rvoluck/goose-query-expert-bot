# Goose Slackbot Administrator Guide

This comprehensive guide covers all administrative aspects of managing the Goose Slackbot, including user management, permissions, monitoring, and maintenance.

## 📋 Table of Contents

1. [Admin Overview](#admin-overview)
2. [User Management](#user-management)
3. [Permission System](#permission-system)
4. [System Configuration](#system-configuration)
5. [Monitoring and Analytics](#monitoring-and-analytics)
6. [Maintenance Tasks](#maintenance-tasks)
7. [Security Management](#security-management)
8. [Troubleshooting](#troubleshooting)
9. [Backup and Recovery](#backup-and-recovery)
10. [Performance Optimization](#performance-optimization)

## 👨‍💼 Admin Overview

### Admin Responsibilities

As a Goose Slackbot administrator, you're responsible for:

- **User Management**: Creating, updating, and deactivating user accounts
- **Permission Control**: Managing access levels and query permissions
- **System Monitoring**: Tracking performance, usage, and health
- **Configuration Management**: Updating settings and feature flags
- **Security Oversight**: Ensuring data security and compliance
- **Maintenance**: Regular updates, backups, and system care

### Admin Access Levels

1. **Super Admin**: Full system access, can manage other admins
2. **Admin**: User and permission management, system monitoring
3. **Support Admin**: Limited access for user support tasks

### Getting Admin Access

To become an admin:
1. Have an existing super admin grant you admin permissions
2. Or use the initial setup script to create the first admin account

```bash
# Create first admin account
python scripts/create_admin.py --slack-id U1234567890 --email admin@company.com
```

## 👥 User Management

### Adding New Users

#### Method 1: Automatic User Creation (Recommended)

Configure automatic user creation for new Slack users:

```bash
# Enable auto-registration in .env
ENABLE_AUTO_USER_REGISTRATION=true
DEFAULT_USER_PERMISSIONS=query_execute
```

#### Method 2: Manual User Creation

Create users manually using the admin interface or CLI:

**Via CLI**:
```bash
python scripts/add_user.py \
  --slack-id U1234567890 \
  --email user@company.com \
  --ldap-id jdoe \
  --permissions query_execute,query_share
```

**Via Admin API**:
```bash
curl -X POST https://your-domain.com/api/admin/users \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slack_user_id": "U1234567890",
    "email": "user@company.com",
    "ldap_id": "jdoe",
    "permissions": ["query_execute", "query_share"],
    "metadata": {
      "department": "engineering",
      "role": "developer"
    }
  }'
```

**Via Python Script**:
```python
import asyncio
from auth import create_auth_system

async def create_user():
    auth = await create_auth_system()
    
    user_id = await auth.create_user(
        slack_user_id="U1234567890",
        email="user@company.com",
        ldap_id="jdoe",
        permissions=["query_execute"],
        metadata={
            "department": "marketing",
            "onboarded_by": "admin@company.com"
        }
    )
    
    print(f"User created with ID: {user_id}")

asyncio.run(create_user())
```

### Bulk User Import

Import multiple users from CSV:

```bash
# Prepare CSV file with columns: slack_user_id,email,ldap_id,permissions,department
python scripts/bulk_import_users.py --file users.csv
```

Example CSV format:
```csv
slack_user_id,email,ldap_id,permissions,department
U1234567890,john@company.com,jdoe,"query_execute,query_share",engineering
U2345678901,jane@company.com,jsmith,query_execute,marketing
```

### Managing Existing Users

#### View User Information

```bash
# List all users
python scripts/list_users.py

# Search for specific user
python scripts/list_users.py --search "john@company.com"

# Get user by Slack ID
python scripts/get_user.py --slack-id U1234567890
```

#### Update User Permissions

```bash
# Add permissions
python scripts/update_user.py \
  --slack-id U1234567890 \
  --add-permissions query_share,admin

# Remove permissions
python scripts/update_user.py \
  --slack-id U1234567890 \
  --remove-permissions admin

# Set exact permissions
python scripts/update_user.py \
  --slack-id U1234567890 \
  --permissions query_execute,query_share
```

#### Deactivate/Reactivate Users

```bash
# Deactivate user
python scripts/update_user.py --slack-id U1234567890 --deactivate

# Reactivate user
python scripts/update_user.py --slack-id U1234567890 --activate
```

#### Delete Users

```bash
# Soft delete (keeps history)
python scripts/delete_user.py --slack-id U1234567890 --soft

# Hard delete (removes all data)
python scripts/delete_user.py --slack-id U1234567890 --hard
```

### LDAP Integration

#### Configure LDAP Authentication

```bash
# LDAP configuration in .env
LDAP_SERVER=ldap://your-ldap-server.com:389
LDAP_BASE_DN=dc=company,dc=com
LDAP_BIND_USER=cn=admin,dc=company,dc=com
LDAP_BIND_PASSWORD=admin-password
LDAP_USER_SEARCH_BASE=ou=users,dc=company,dc=com
LDAP_GROUP_SEARCH_BASE=ou=groups,dc=company,dc=com
```

#### Sync Users from LDAP

```bash
# Sync all LDAP users
python scripts/sync_ldap_users.py

# Sync specific group
python scripts/sync_ldap_users.py --group "data-team"

# Dry run (preview changes)
python scripts/sync_ldap_users.py --dry-run
```

#### Map LDAP Groups to Permissions

```python
# Configure group mappings in auth.py
LDAP_GROUP_PERMISSIONS = {
    "data-team": ["query_execute", "query_share", "admin"],
    "analysts": ["query_execute", "query_share"],
    "developers": ["query_execute"],
    "managers": ["query_execute", "query_share", "user_manage"]
}
```

## 🔐 Permission System

### Available Permissions

| Permission | Description | Allows User To |
|------------|-------------|----------------|
| `query_execute` | Execute data queries | Ask questions and run queries |
| `query_share` | Share query results | Share results with team members |
| `query_history` | Access query history | View past queries and results |
| `file_download` | Download result files | Download CSV files for large results |
| `user_manage` | Manage other users | Add/edit users (limited admin) |
| `admin` | Full admin access | All administrative functions |
| `audit_view` | View audit logs | Access system audit information |
| `config_manage` | Manage configuration | Update system settings |

### Permission Hierarchies

```
admin (includes all permissions)
├── config_manage
├── user_manage
├── audit_view
├── query_share
├── query_history
├── file_download
└── query_execute (base permission)
```

### Role-Based Permission Templates

Create standard roles for easy assignment:

```python
# Define in config.py
PERMISSION_ROLES = {
    "analyst": ["query_execute", "query_share", "query_history", "file_download"],
    "manager": ["query_execute", "query_share", "query_history", "file_download", "audit_view"],
    "admin": ["admin"],  # Includes all permissions
    "viewer": ["query_execute", "query_history"],
    "power_user": ["query_execute", "query_share", "query_history", "file_download", "user_manage"]
}
```

Apply roles:
```bash
# Assign role to user
python scripts/assign_role.py --slack-id U1234567890 --role analyst

# Create custom role
python scripts/create_role.py --name "data_scientist" --permissions query_execute,query_share,query_history,file_download,audit_view
```

### Permission Auditing

Track permission changes:

```bash
# View permission history for user
python scripts/audit_permissions.py --slack-id U1234567890

# View all permission changes
python scripts/audit_permissions.py --all --since "2023-01-01"

# Export permission audit
python scripts/audit_permissions.py --export permissions_audit.csv
```

## ⚙️ System Configuration

### Configuration Management

#### View Current Configuration

```bash
# View all settings
python scripts/show_config.py

# View specific category
python scripts/show_config.py --category slack
python scripts/show_config.py --category database
python scripts/show_config.py --category security
```

#### Update Configuration

**Via Environment Variables**:
```bash
# Update .env file
echo "MAX_RESULT_ROWS=15000" >> .env
echo "QUERY_TIMEOUT_SECONDS=600" >> .env

# Restart application to apply changes
systemctl restart goose-slackbot
```

**Via Admin API**:
```bash
curl -X PUT https://your-domain.com/api/admin/config \
  -H "Authorization: Bearer $ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_result_rows": 15000,
    "query_timeout_seconds": 600,
    "enable_file_uploads": true
  }'
```

**Via CLI Script**:
```bash
python scripts/update_config.py \
  --key max_result_rows \
  --value 15000

python scripts/update_config.py \
  --key enable_interactive_buttons \
  --value true
```

### Feature Flags

Manage feature availability:

```bash
# Enable/disable features
python scripts/manage_features.py --enable query_history
python scripts/manage_features.py --disable file_uploads
python scripts/manage_features.py --enable interactive_buttons

# View feature status
python scripts/manage_features.py --status
```

### Rate Limiting Configuration

```bash
# Configure rate limits
python scripts/configure_rate_limits.py \
  --per-user-per-minute 15 \
  --per-user-per-hour 200 \
  --global-per-minute 500

# View current rate limits
python scripts/show_rate_limits.py

# Reset rate limit counters
python scripts/reset_rate_limits.py --user U1234567890
```

### Slack Configuration

#### Update Slack Settings

```bash
# Update Slack bot settings
python scripts/update_slack_config.py \
  --admin-channel C1234567890 \
  --enable-dm true \
  --enable-mentions true

# Test Slack connectivity
python scripts/test_slack.py
```

#### Manage Slack Channels

```bash
# Add bot to channels
python scripts/manage_channels.py --add C1234567890 C2345678901

# Remove bot from channels
python scripts/manage_channels.py --remove C1234567890

# List bot channels
python scripts/manage_channels.py --list
```

## 📊 Monitoring and Analytics

### Usage Analytics

#### Query Statistics

```bash
# View query statistics
python scripts/query_stats.py --period "last_30_days"

# Top users by query count
python scripts/query_stats.py --top-users 10

# Most popular tables/queries
python scripts/query_stats.py --popular-tables
```

#### User Activity

```bash
# Active users report
python scripts/user_activity.py --period "last_week"

# User engagement metrics
python scripts/user_activity.py --engagement

# Export user activity
python scripts/user_activity.py --export user_activity.csv
```

#### System Performance

```bash
# Performance metrics
python scripts/system_metrics.py

# Query performance analysis
python scripts/query_performance.py --slow-queries

# Resource utilization
python scripts/resource_usage.py
```

### Dashboard and Reporting

#### Generate Reports

```bash
# Daily usage report
python scripts/generate_report.py --type daily --date 2023-12-01

# Weekly summary
python scripts/generate_report.py --type weekly --week 2023-W48

# Monthly report
python scripts/generate_report.py --type monthly --month 2023-12

# Custom report
python scripts/generate_report.py \
  --type custom \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --metrics queries,users,performance
```

#### Automated Reporting

Set up automated reports:

```bash
# Configure daily reports
python scripts/setup_automated_reports.py \
  --frequency daily \
  --recipients admin@company.com,data-team@company.com \
  --slack-channel C1234567890

# Configure weekly reports
python scripts/setup_automated_reports.py \
  --frequency weekly \
  --day monday \
  --recipients management@company.com
```

### Health Monitoring

#### System Health Checks

```bash
# Comprehensive health check
python scripts/health_check.py --full

# Database health
python scripts/health_check.py --database

# External services health
python scripts/health_check.py --external

# Performance health
python scripts/health_check.py --performance
```

#### Alerting Configuration

```bash
# Configure alerts
python scripts/setup_alerts.py \
  --error-rate-threshold 5 \
  --response-time-threshold 10 \
  --disk-usage-threshold 85 \
  --memory-usage-threshold 90

# Test alerting
python scripts/test_alerts.py
```

### Prometheus Metrics

Monitor key metrics:

```bash
# Query metrics
goose_slackbot_queries_total
goose_slackbot_query_duration_seconds
goose_slackbot_query_errors_total

# User metrics
goose_slackbot_active_users
goose_slackbot_user_sessions_total

# System metrics
goose_slackbot_database_connections
goose_slackbot_memory_usage_bytes
goose_slackbot_cpu_usage_percent
```

## 🔧 Maintenance Tasks

### Daily Maintenance

Create a daily maintenance script:

```bash
#!/bin/bash
# daily_maintenance.sh

echo "Starting daily maintenance..."

# Clean old sessions
python scripts/cleanup_sessions.py --older-than 7

# Clean old query history (keep 90 days)
python scripts/cleanup_query_history.py --older-than 90

# Update statistics
python scripts/update_statistics.py

# Generate daily report
python scripts/generate_report.py --type daily

# Health check
python scripts/health_check.py --full

echo "Daily maintenance completed"
```

### Weekly Maintenance

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "Starting weekly maintenance..."

# Database maintenance
python scripts/database_maintenance.py --vacuum --analyze

# Update user activity stats
python scripts/update_user_stats.py

# Clean old audit logs (keep 1 year)
python scripts/cleanup_audit_logs.py --older-than 365

# Generate weekly report
python scripts/generate_report.py --type weekly

# Backup configuration
python scripts/backup_config.py

echo "Weekly maintenance completed"
```

### Monthly Maintenance

```bash
#!/bin/bash
# monthly_maintenance.sh

echo "Starting monthly maintenance..."

# Full database backup
python scripts/backup_database.py --full

# Archive old data
python scripts/archive_old_data.py --older-than 180

# Update system statistics
python scripts/update_system_stats.py

# Security audit
python scripts/security_audit.py

# Generate monthly report
python scripts/generate_report.py --type monthly

echo "Monthly maintenance completed"
```

### Automated Maintenance

Set up cron jobs for automated maintenance:

```bash
# Edit crontab
crontab -e

# Add maintenance jobs
# Daily maintenance at 2 AM
0 2 * * * /path/to/goose-slackbot/scripts/daily_maintenance.sh

# Weekly maintenance on Sunday at 3 AM
0 3 * * 0 /path/to/goose-slackbot/scripts/weekly_maintenance.sh

# Monthly maintenance on 1st at 4 AM
0 4 1 * * /path/to/goose-slackbot/scripts/monthly_maintenance.sh
```

## 🔒 Security Management

### Access Control

#### Review User Access

```bash
# Audit user permissions
python scripts/audit_user_access.py

# Find users with admin permissions
python scripts/find_admins.py

# Review inactive users
python scripts/review_inactive_users.py --inactive-days 30
```

#### Access Reviews

Conduct regular access reviews:

```bash
# Generate access review report
python scripts/access_review.py \
  --output access_review_$(date +%Y%m%d).csv

# Review privileged users
python scripts/access_review.py --privileged-only

# Review by department
python scripts/access_review.py --department engineering
```

### Security Auditing

#### Audit Logs

```bash
# View recent security events
python scripts/view_audit_logs.py --security --recent

# Search for specific events
python scripts/view_audit_logs.py --search "failed_login"

# Export audit logs
python scripts/export_audit_logs.py \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --output audit_logs.csv
```

#### Security Scanning

```bash
# Run security scan
python scripts/security_scan.py

# Check for vulnerabilities
python scripts/vulnerability_check.py

# Validate configurations
python scripts/config_security_check.py
```

### Data Protection

#### Encryption Management

```bash
# Rotate encryption keys
python scripts/rotate_encryption_keys.py

# Verify data encryption
python scripts/verify_encryption.py

# Re-encrypt sensitive data
python scripts/re_encrypt_data.py --confirm
```

#### Data Retention

```bash
# Configure data retention policies
python scripts/configure_retention.py \
  --query-history 90 \
  --audit-logs 365 \
  --user-sessions 30

# Apply retention policies
python scripts/apply_retention.py --dry-run
python scripts/apply_retention.py --confirm
```

### Compliance

#### GDPR Compliance

```bash
# Handle data subject requests
python scripts/gdpr_request.py \
  --type export \
  --user-email user@company.com

python scripts/gdpr_request.py \
  --type delete \
  --user-email user@company.com \
  --confirm
```

#### SOX Compliance

```bash
# Generate SOX compliance report
python scripts/sox_compliance.py --quarter Q4_2023

# Audit trail verification
python scripts/verify_audit_trail.py
```

## 🚨 Troubleshooting

### Common Admin Issues

#### User Cannot Access Bot

**Diagnosis**:
```bash
# Check if user exists
python scripts/get_user.py --slack-id U1234567890

# Check user permissions
python scripts/check_permissions.py --slack-id U1234567890

# Check user status
python scripts/user_status.py --slack-id U1234567890
```

**Solutions**:
```bash
# Create user if missing
python scripts/add_user.py --slack-id U1234567890 --email user@company.com

# Grant permissions
python scripts/update_user.py --slack-id U1234567890 --add-permissions query_execute

# Activate user
python scripts/update_user.py --slack-id U1234567890 --activate
```

#### Performance Issues

**Diagnosis**:
```bash
# Check system performance
python scripts/performance_check.py

# Analyze slow queries
python scripts/slow_query_analysis.py

# Check resource usage
python scripts/resource_monitor.py
```

**Solutions**:
```bash
# Optimize database
python scripts/optimize_database.py

# Clear caches
python scripts/clear_caches.py

# Restart services
systemctl restart goose-slackbot
```

#### Configuration Issues

**Diagnosis**:
```bash
# Validate configuration
python scripts/validate_config.py

# Check environment variables
python scripts/check_env.py

# Test external connections
python scripts/test_connections.py
```

**Solutions**:
```bash
# Fix configuration
python scripts/fix_config.py --auto

# Reset to defaults
python scripts/reset_config.py --section database

# Reload configuration
python scripts/reload_config.py
```

### Emergency Procedures

#### System Outage

1. **Immediate Response**:
   ```bash
   # Check system status
   python scripts/emergency_status.py
   
   # Enable maintenance mode
   python scripts/maintenance_mode.py --enable
   
   # Notify users
   python scripts/notify_outage.py --message "System maintenance in progress"
   ```

2. **Recovery Steps**:
   ```bash
   # Restart services
   systemctl restart goose-slackbot postgresql redis
   
   # Verify functionality
   python scripts/verify_system.py
   
   # Disable maintenance mode
   python scripts/maintenance_mode.py --disable
   ```

#### Data Corruption

1. **Assessment**:
   ```bash
   # Check data integrity
   python scripts/check_data_integrity.py
   
   # Identify corruption scope
   python scripts/assess_corruption.py
   ```

2. **Recovery**:
   ```bash
   # Restore from backup
   python scripts/restore_backup.py --date 2023-12-01
   
   # Verify restoration
   python scripts/verify_restoration.py
   ```

#### Security Incident

1. **Immediate Actions**:
   ```bash
   # Disable affected accounts
   python scripts/emergency_disable.py --users user1,user2
   
   # Change security keys
   python scripts/emergency_key_rotation.py
   
   # Enable enhanced logging
   python scripts/enable_security_logging.py
   ```

2. **Investigation**:
   ```bash
   # Generate incident report
   python scripts/incident_report.py --incident-id SEC-001
   
   # Audit affected data
   python scripts/audit_incident.py --incident-id SEC-001
   ```

## 💾 Backup and Recovery

### Backup Strategy

#### Database Backups

```bash
# Daily incremental backup
python scripts/backup_database.py --incremental

# Weekly full backup
python scripts/backup_database.py --full

# Backup specific tables
python scripts/backup_database.py --tables users,query_history,audit_logs
```

#### Configuration Backups

```bash
# Backup configuration
python scripts/backup_config.py --output config_backup_$(date +%Y%m%d).tar.gz

# Backup environment files
python scripts/backup_env.py
```

#### Application Backups

```bash
# Full application backup
python scripts/backup_application.py --full

# Code and configuration only
python scripts/backup_application.py --code-only
```

### Recovery Procedures

#### Database Recovery

```bash
# List available backups
python scripts/list_backups.py --type database

# Restore from specific backup
python scripts/restore_database.py --backup 2023-12-01_full.sql

# Point-in-time recovery
python scripts/restore_database.py --point-in-time "2023-12-01 14:30:00"
```

#### Configuration Recovery

```bash
# Restore configuration
python scripts/restore_config.py --backup config_backup_20231201.tar.gz

# Restore specific settings
python scripts/restore_config.py --section slack --backup config_backup_20231201.tar.gz
```

### Disaster Recovery

#### Disaster Recovery Plan

1. **Preparation**:
   - Maintain offsite backups
   - Document recovery procedures
   - Test recovery regularly

2. **Recovery Steps**:
   ```bash
   # Initialize new environment
   python scripts/disaster_recovery.py --initialize
   
   # Restore data
   python scripts/disaster_recovery.py --restore-data
   
   # Restore configuration
   python scripts/disaster_recovery.py --restore-config
   
   # Verify system
   python scripts/disaster_recovery.py --verify
   ```

## ⚡ Performance Optimization

### Database Optimization

#### Query Performance

```bash
# Analyze slow queries
python scripts/analyze_slow_queries.py

# Optimize database indexes
python scripts/optimize_indexes.py

# Update table statistics
python scripts/update_table_stats.py
```

#### Connection Pooling

```bash
# Optimize connection pool
python scripts/optimize_db_pool.py \
  --min-connections 5 \
  --max-connections 20 \
  --max-overflow 30
```

### Application Optimization

#### Memory Management

```bash
# Monitor memory usage
python scripts/monitor_memory.py

# Optimize memory settings
python scripts/optimize_memory.py \
  --max-workers 8 \
  --memory-limit 2GB
```

#### Caching Optimization

```bash
# Optimize Redis cache
python scripts/optimize_cache.py \
  --cache-size 512MB \
  --ttl 3600

# Clear stale cache entries
python scripts/clear_stale_cache.py
```

### Scaling Considerations

#### Horizontal Scaling

```bash
# Configure load balancing
python scripts/setup_load_balancer.py \
  --instances 3 \
  --health-check /health

# Deploy additional instances
python scripts/scale_instances.py --count 3
```

#### Vertical Scaling

```bash
# Increase resource limits
python scripts/scale_resources.py \
  --cpu 4 \
  --memory 8GB \
  --storage 100GB
```

---

## 📞 Admin Support

### Getting Help

- **Documentation**: Check all documentation files
- **Community**: Join the admin Slack channel
- **Support**: Contact the development team
- **Emergency**: Use emergency contact procedures

### Training Resources

- **Admin Training**: Schedule regular admin training sessions
- **Best Practices**: Follow established admin best practices
- **Updates**: Stay informed about system updates and changes

### Feedback and Improvements

- **Feature Requests**: Submit requests for new admin features
- **Bug Reports**: Report issues with admin functionality
- **Process Improvements**: Suggest improvements to admin workflows

Remember: Good administration ensures a smooth experience for all users. Regular monitoring, maintenance, and proactive management are key to success!
