# ML CTF Platform - Production Deployment Guide

## Pre-Deployment Checklist

```
Security:
☐ Set FLASK_ENV=production
☐ Generate strong SECRET_KEY
☐ Enable HTTPS/SSL
☐ Configure CORS properly
☐ Set secure database password
☐ Remove debug statements from code
☐ Enable CSRF protection

Infrastructure:
☐ Choose hosting platform (Heroku, AWS, DigitalOcean, etc.)
☐ Set up PostgreSQL database
☐ Configure Redis for caching (optional)
☐ Set up monitoring/alerting
☐ Configure backups
☐ Set up domain name with SSL

Scaling:
☐ Use Gunicorn (4+ workers) instead of Flask dev server
☐ Use Nginx as reverse proxy
☐ Enable database connection pooling
☐ Set up load balancer (if multi-server)
☐ Enable CDN for static files

Testing:
☐ Test all user registration flows
☐ Test flag submission in production config
☐ Test leaderboard queries
☐ Test database backups
☐ Load test with concurrent users
☐ Test logging and monitoring
```

---

## Option 1: Heroku Deployment (Easiest)

### Step 1: Prepare Application

```bash
# Create Procfile
echo "web: gunicorn 'src.main:create_app()'" > Procfile

# Create runtime.txt (specify Python version)
echo "python-3.11.0" > runtime.txt

# Update requirements.txt (add production dependencies)
pip install gunicorn psycopg2-binary python-dotenv
pip freeze > requirements.txt
```

### Step 2: Create Heroku App

```bash
# Install Heroku CLI (if not done)
# Windows: choco install heroku-cli
# Mac: brew tap heroku/brew && brew install heroku
# Linux: curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create app
heroku create your-ml-ctf-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Get database URL
heroku config:get DATABASE_URL
```

### Step 3: Set Environment Variables

```bash
# Set production config
heroku config:set FLASK_ENV=production
heroku config:set FLASK_DEBUG=0
heroku config:set SECRET_KEY="$(python -c 'import os; print(os.urandom(24).hex())')"

# Verify
heroku config
```

### Step 4: Deploy

```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Initial commit: ML CTF Platform"

# Deploy to Heroku
git push heroku main  # or master

# View logs
heroku logs --tail

# Run migrations/init
heroku run python -c "from src.main import create_app; app = create_app(); app.app_context().push(); from src.models import db; db.create_all()"

# Open app
heroku open
```

### Step 5: Monitor

```bash
# View live logs
heroku logs --tail

# Check app status
heroku status

# Scale dyno (if needed)
heroku dyno:type web=standard-2x

# Check for errors
heroku logs --tail -n 100 | grep ERROR
```

---

## Option 2: DigitalOcean Deployment (Recommended for Learning)

### Step 1: Create Droplet

```bash
# Create Ubuntu 22.04 Basic droplet (5$/month)
# SSH into droplet
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.11 python3-pip python3-venv postgresql postgresql-contrib nginx
```

### Step 2: Clone & Setup

```bash
# Create app directory
mkdir /var/www/ml-ctf
cd /var/www/ml-ctf

# Clone repository (if using GitHub)
git clone https://github.com/your-username/ml-ctf-challenge .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

### Step 3: Setup PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE ml_ctf;
CREATE USER ml_ctf_user WITH PASSWORD 'your_secure_password';
ALTER ROLE ml_ctf_user SET client_encoding TO 'utf8';
ALTER ROLE ml_ctf_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ml_ctf_user SET default_transaction_deferrable TO on;
ALTER ROLE ml_ctf_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ml_ctf TO ml_ctf_user;
\q

# Test connection
psql -U ml_ctf_user -d ml_ctf -h localhost -W
```

### Step 4: Configure Environment

```bash
# Create .env file
cat > /var/www/ml-ctf/.env << EOF
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=postgresql://ml_ctf_user:your_secure_password@localhost:5432/ml_ctf
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')
EOF

# Set permissions
chmod 600 .env
```

### Step 5: Create Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/ml-ctf.service > /dev/null << EOF
[Unit]
Description=ML CTF Challenge Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ml-ctf
Environment="PATH=/var/www/ml-ctf/venv/bin"
EnvironmentFile=/var/www/ml-ctf/.env
ExecStart=/var/www/ml-ctf/venv/bin/gunicorn --workers 4 --bind unix:/run/ml-ctf.sock 'src.main:create_app()'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ml-ctf
sudo systemctl start ml-ctf
sudo systemctl status ml-ctf
```

### Step 6: Configure Nginx

```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/ml-ctf > /dev/null << EOF
server {
    listen 80;
    server_name your_domain.com;

    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your_domain.com;

    # SSL certificates (get from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location / {
        proxy_pass http://unix:/run/ml-ctf.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/ml-ctf/src/static;
        expires 30d;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/ml-ctf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 7: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your_domain.com

# Auto-renewal (already enabled by default)
sudo systemctl status certbot.timer
```

### Step 8: Monitor & Maintain

```bash
# View logs
sudo systemctl logs ml-ctf -f

# Check Nginx logs
sudo tail -f /var/access.log
sudo tail -f /var/error.log

# Restart services (if needed)
sudo systemctl restart ml-ctf
sudo systemctl restart nginx

# Backup database
sudo -u postgres pg_dump ml_ctf > /backup/ml_ctf_$(date +%Y%m%d).sql
```

---

## Option 3: AWS Deployment (Full Control)

### Architecture

```
Route 53 (DNS)
    ↓
CloudFront (CDN) ← S3 (static files)
    ↓
Application Load Balancer
    ↓
EC2 Auto Scaling Group (2+ instances)
    ↓
RDS PostgreSQL (Multi-AZ)
    ↓
ElastiCache Redis (optional)
```

### Step 1: Create EC2 Instance

```bash
# Launch Ubuntu 22.04 t3.small instance
# Security group: Allow 22 (SSH), 80 (HTTP), 443 (HTTPS)
# Create/use EC2 key pair

# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-IP

# Update system
sudo apt update && apt upgrade -y
```

### Step 2: Create RDS Database

```bash
# AWS Console:
# 1. RDS → Databases → Create database
# 2. PostgreSQL 14
# 3. db.t3.micro (free tier eligible)
# 4. Storage: 20GB
# 5. Multi-AZ: No (unless production-critical)
# 6. Database name: ml_ctf
# 7. Master username: ml_ctf_admin
# 8. Create password
# 9. Security group: Allow port 5432 from EC2

# After creation, get RDS endpoint:
# Example: ml-ctf.xxxxx.us-east-1.rds.amazonaws.com
```

### Step 3: Setup Application on EC2

```bash
# Same as DigitalOcean steps 2-6 above
# But use RDS endpoint in DATABASE_URL:
DATABASE_URL=postgresql://ml_ctf_admin:password@ml-ctf.xxxxx.us-east-1.rds.amazonaws.com:5432/ml_ctf
```

### Step 4: Create Load Balancer

```bash
# AWS Console:
# 1. EC2 → Load Balancers → Create Load Balancer
# 2. Application Load Balancer
# 3. Create listening on port 80 and 443
# 4. Target group: EC2 instances running ml-ctf service
# 5. Health check: /challenges (or any public endpoint)
```

### Step 5: Setup Auto Scaling

```bash
# AWS Console:
# 1. Create Launch Template from current instance
# 2. EC2 → Auto Scaling Groups → Create
# 3. Min: 2, Desired: 2, Max: 4
# 4. Associate with Load Balancer
# 5. Set scaling policies based on CPU usage
```

### Step 6: Setup CloudFront (CDN)

```bash
# AWS Console:
# 1. CloudFront → Create Distribution
# 2. Origin: Point to Load Balancer
# 3. Cache behavior: /static/* → cache everything
# 4. /api/* → no cache
# 5. Deploy

# Update DNS (Route 53):
# Create CNAME record pointing to CloudFront domain
```

---

## Performance Optimization

### Database Optimization

```python
# Add indexes for frequently queried fields
class User(db.Model):
    __table_args__ = (
        db.Index('ix_username', 'username'),
        db.Index('ix_email', 'email'),
    )

class Score(db.Model):
    __table_args__ = (
        db.Index('ix_user_id', 'user_id'),
        db.Index('ix_flag_id', 'flag_id'),
    )

# In production:
# Run: sqlite3 ctf.db "CREATE INDEX ix_username ON users(username);"
```

### Caching Strategy

```python
from flask_caching import Cache
from datetime import timedelta

cache = Cache(app, config={
    'CACHE_TYPE': 'RedisCache',  # or 'SimpleCache' for development
    'CACHE_REDIS_URL': 'redis://localhost:6379'
})

# Cache expensive queries
@app.route('/api/leaderboard')
@cache.cached(timeout=60)  # Cache 60 seconds
def leaderboard():
    return get_leaderboard_data()

# Cache static HTML
@app.route('/challenges')
@cache.cached(timeout=300)  # Cache 5 minutes
def challenges():
    return render_template('challenges.html')
```

### Database Connection Pooling

```python
# In config.py
class ProductionConfig(Config):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
```

### Gunicorn Optimization

```bash
# Production startup:
gunicorn \
    --workers 8 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile - \
    'src.main:create_app()'
```

---

## Monitoring & Logging

### Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('ctf.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ML CTF Platform startup')
```

### External Monitoring (Sentry)

```bash
# Install Sentry integration
pip install sentry-sdk

# Initialize in main.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

### Health Check Endpoint

```python
@app.route('/health')
def health():
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return {'status': 'healthy'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
```

---

## Security Hardening

### Environment Variables

```bash
# Never commit secrets
echo ".env" >> .gitignore

# Use secret management:
# AWS Secrets Manager
# HashiCorp Vault
# GitHub Secrets (if using CI/CD)
```

### Rate Limiting (Production)

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

# More strict on flag submission
@app.route('/api/submit-flag', methods=['POST'])
@limiter.limit("5 per minute")
def submit_flag():
    ...
```

### Database Security

```bash
# Use strong passwords
# postgresql_password_should_be_>=20_chars_with_upper_lower_number_special

# Use SSL for postgres connection
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Run regular backups:
0 2 * * * pg_dump ml_ctf | gzip > /backup/ml_ctf_$(date +\%Y\%m\%d).sql.gz
```

### Web Security Headers

```python
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

---

## Disaster Recovery

### Backup Strategy

```bash
# Daily database backups
0 3 * * * PGPASSWORD="$DB_PASS" pg_dump -U $DB_USER -h $DB_HOST $DB_NAME | gzip > /backup/ml_ctf_$(date +\%Y\%m\%d).sql.gz

# Weekly full disk backup
0 4 * * 0 tar -czf /backup/full_backup_$(date +\%Y\%m\%d).tar.gz /var/www/ml-ctf

# Upload to S3
aws s3 sync /backup/ s3://my-backup-bucket/ml-ctf/
```

### Recovery Procedures

```bash
# Restore from backup
gunzip < /backup/ml_ctf_20240101.sql.gz | psql -U ml_ctf_user -d ml_ctf

# Verify restore
psql -U ml_ctf_user -d ml_ctf -c "SELECT COUNT(*) FROM users;"
```

---

## Cost Estimation (Monthly)

### Heroku
- Dyno: $7
- PostgreSQL: $9
- **Total: ~$16/month**

### DigitalOcean
- Droplet (2GB RAM): $12
- PostgreSQL Managed: $15
- **Total: ~$27/month**

### AWS (Small Scale)
- EC2 t3.small: $20
- RDS db.t3.micro: $15
- Load Balancer: $16
- Data transfer: $10
- **Total: ~$60+/month**

---

## Checklist Before Going Live

```
☐ Database backups configured and tested
☐ SSL certificate valid and auto-renewing
☐ Monitoring/alerting set up
☐ Logging configured and available
☐ Performance tested with concurrent users
☐ Security headers configured
☐ CORS properly restricted
☐ Rate limiting enabled
☐ Database connection pooling configured
☐ Static files served through CDN/Nginx
☐ Admin tools for user management
☐ Database recovery procedure tested
☐ Incident response plan documented
☐ Domain DNS configured
☐ Email notifications working
☐ Analytics tracking enabled
```

---

For more help, see:
- ARCHITECTURE.md - System design overview
- TROUBLESHOOTING.md - Common issues
- requirements.txt - All dependencies
