# Goose Slackbot - AI-Powered Data Assistant

<div align="center">

![Goose Slackbot Logo](docs/images/logo.png)

**Transform your team's data analysis with AI-powered natural language queries in Slack**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Slack API](https://img.shields.io/badge/Slack-API-4A154B)](https://api.slack.com/)
[![Goose](https://img.shields.io/badge/Powered%20by-Goose-00C7B7)](https://github.com/block/goose)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture) • [Support](#-support)

</div>

---

## 📖 Overview

Goose Slackbot is an enterprise-grade AI assistant that brings the power of natural language data querying directly into your Slack workspace. Built on top of [Goose Query Expert](https://github.com/block/goose), it enables anyone on your team to ask data questions in plain English and receive instant, accurate results from your data warehouse.

**Perfect for:**
- 📊 Data analysts who want faster insights
- 👥 Business teams who need self-service analytics
- 🔍 Executives who need quick answers to business questions
- 🚀 Product teams who want data-driven decisions

## ✨ Key Features

### 🤖 Natural Language Processing
- **Ask Questions Naturally**: "What was our revenue last month?" - No SQL required
- **Context-Aware**: Understands business terminology and your data schema
- **Smart Suggestions**: Get query refinement suggestions and alternatives
- **Multi-Turn Conversations**: Ask follow-up questions in threaded conversations

### ⚡ Intelligent Query Execution
- **AI-Powered SQL Generation**: Goose Query Expert generates optimized SQL automatically
- **Real-Time Progress Updates**: See query progress with live status updates
- **Fast Results**: Typical queries complete in 1-10 seconds
- **Error Recovery**: Helpful error messages with suggestions for resolution

### 📊 Smart Result Formatting
- **Inline Tables**: Small results displayed as formatted tables in Slack
- **CSV Downloads**: Large datasets automatically exported as CSV files
- **Data Previews**: See first rows before downloading full results
- **Visual Indicators**: Clear metrics on execution time and row counts

### 👥 Collaboration Features
- **Expert Recommendations**: Get connected with data experts for complex queries
- **Query Sharing**: Share interesting findings with your team
- **Thread Management**: Keep conversations organized with threaded replies
- **Team Learning**: Learn from colleagues' successful queries

### 🔐 Enterprise Security
- **LDAP Integration**: Seamless authentication with your existing directory
- **Role-Based Access Control**: Granular permissions for query execution
- **Audit Logging**: Complete audit trail of all queries and actions
- **Data Encryption**: Sensitive data encrypted at rest and in transit
- **Rate Limiting**: Protection against abuse and excessive usage

### 📈 Query Management
- **Query History**: Access your previous queries and results
- **Session Tracking**: Maintain context across conversations
- **Query Refinement**: Easily modify and re-run queries
- **Bookmarking**: Save frequently used queries for quick access

### 🛠️ Developer Friendly
- **RESTful APIs**: Comprehensive API for integrations
- **Webhook Support**: Real-time event notifications
- **Extensible Architecture**: Easy to customize and extend
- **Docker Support**: Containerized deployment ready
- **Kubernetes Ready**: Production-grade orchestration support

## 📋 Prerequisites

### Required Software
- **Python 3.9+** - Application runtime
- **PostgreSQL 12+** - Primary database for user data and query history
- **Redis 6+** - Caching and session management
- **Goose Query Expert** - AI-powered query generation engine
- **Snowflake** - Data warehouse (or compatible alternative)

### Required Access
- **Slack Workspace** - Admin privileges to create and configure apps
- **Snowflake Account** - Appropriate query permissions
- **LDAP Server** - (Optional) For enterprise authentication

## 🛠️ Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd goose-slackbot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create database
createdb goose_slackbot

# Run migrations
python migrations.py
```

### 3. Environment Configuration

```bash
cp env.example .env
# Edit .env with your configuration (see SETUP.md for details)
```

### 4. Slack App Setup

Follow the detailed instructions in [SETUP.md](SETUP.md) to create and configure your Slack app.

### 5. Run the Bot

```bash
# Development mode
python slack_bot.py

# Production mode
gunicorn -w 4 -k uvicorn.workers.UvicornWorker slack_bot:app
```

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Complete setup and configuration guide
- **[API.md](API.md)** - API documentation and integration details
- **[USER_MANUAL.md](USER_MANUAL.md)** - User guide for team members
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Administrator guide for managing users and permissions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack Users   │◄──►│  Goose Slackbot │◄──►│ Goose Query     │
│                 │    │                 │    │ Expert          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │   Snowflake     │
                       │   Database      │    │ Data Warehouse  │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │     Cache       │
                       └─────────────────┘
```

### Core Components

- **Slack Bot**: Handles Slack events and user interactions
- **Goose Client**: Interfaces with Goose Query Expert for SQL generation
- **Database Layer**: Manages user sessions, query history, and audit logs
- **Authentication**: LDAP integration and permission management
- **Result Formatter**: Smart formatting of query results for Slack display

## 🔧 Configuration

The bot uses environment variables for configuration. Key settings include:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# Database
DATABASE_URL=postgresql://user:pass@localhost/goose_slackbot
REDIS_URL=redis://localhost:6379/0

# Goose Integration
GOOSE_MCP_SERVER_URL=http://localhost:8000
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_WAREHOUSE=COMPUTE_WH

# Security
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

See [SETUP.md](SETUP.md) for complete configuration details.

## 💬 Usage Examples

### Basic Queries
```
@goose-bot What was our revenue last month?
@goose-bot Show me top 10 customers by sales
@goose-bot How many new users signed up this week?
```

### Advanced Queries
```
@goose-bot Compare revenue between Q3 and Q4 2023 by product category
@goose-bot What's the average order value for customers in California?
@goose-bot Show me the conversion funnel for our mobile app
```

### Interactive Features
- **Refine Query**: Click "Refine Query" button to modify your question
- **Share Results**: Share interesting findings with your team
- **Download Data**: Large result sets are automatically provided as CSV files

## 🔐 Security Features

- **Authentication**: LDAP integration for user verification
- **Authorization**: Role-based permissions for query execution
- **Audit Logging**: Complete audit trail of all queries and actions
- **Data Encryption**: Sensitive data encrypted at rest and in transit
- **Rate Limiting**: Protection against abuse and excessive usage

## 📊 Monitoring and Observability

- **Metrics**: Prometheus metrics for monitoring bot performance
- **Logging**: Structured logging with configurable levels
- **Health Checks**: Built-in health endpoints for monitoring
- **Error Tracking**: Optional Sentry integration for error monitoring

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black .
flake8 .
mypy .
```

### Docker Development
```bash
docker-compose up -d
```

## 🚀 Deployment

### Docker Deployment
```bash
docker build -t goose-slackbot .
docker run -d --env-file .env goose-slackbot
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/
```

### Environment-Specific Configurations
- **Development**: Socket Mode with local database
- **Staging**: Events API with staging database
- **Production**: Events API with production database and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the docs folder for detailed guides
- **Issues**: Report bugs and feature requests on GitHub Issues
- **Slack**: Contact the data team in #data-support channel
- **Email**: data-team@company.com

## 🔄 Changelog

### v1.0.0 (Latest)
- Initial release with core functionality
- Natural language query processing
- Slack integration with interactive features
- User authentication and permissions
- Query history and audit logging

### Roadmap
- [ ] Advanced visualization support
- [ ] Scheduled queries and alerts
- [ ] Integration with additional data sources
- [ ] Enhanced collaboration features
- [ ] Mobile app support

## 🙏 Acknowledgments

- [Goose Query Expert](https://github.com/block/goose) for the AI-powered query generation
- [Slack Bolt](https://slack.dev/bolt-python/) for the Slack integration framework
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- All contributors and the data team for their valuable feedback

---

**Made with ❤️ by the Data Team**

For detailed setup instructions, see [SETUP.md](SETUP.md)
