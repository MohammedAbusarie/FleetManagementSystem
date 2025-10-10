# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Fleet Management System to a production environment.

## Prerequisites

- Ubuntu 22.04 LTS or similar Linux server
- Root or sudo access
- Domain name (optional but recommended)
- SSL certificate (for HTTPS)

## Step 1: Server Setup

### Update System Packages
```bash
sudo apt update
sudo apt upgrade -y
```

### Install Required Software
```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Nginx
sudo apt install -y nginx

# Install system dependencies
sudo apt install -y libpq-dev python3.11-dev build-essential
```

## Step 2: Create Application User

```bash
# Create a dedicated user for the application
sudo useradd -m -s /bin/bash fleetapp
sudo passwd fleetapp

# Switch to the application user
sudo su - fleetapp
```

## Step 3: Set Up Application Directory

```bash
# Create application directory
mkdir -p /home/fleetapp/fleet_management
cd /home/fleetapp/fleet_management

# Upload your application files here
# (Use scp, rsync, or git clone)
```

## Step 4: Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## Step 5: Configure PostgreSQL

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql << EOF
CREATE DATABASE fleet_management_prod;
CREATE USER fleetapp WITH PASSWORD 'your_secure_password_here';
ALTER ROLE fleetapp SET client_encoding TO 'utf8';
ALTER ROLE fleetapp SET default_transaction_isolation TO 'read committed';
ALTER ROLE fleetapp SET timezone TO 'Asia/Riyadh';
GRANT ALL PRIVILEGES ON DATABASE fleet_management_prod TO fleetapp;
ALTER DATABASE fleet_management_prod OWNER TO fleetapp;
\q
EOF

# Exit postgres user
exit
```

## Step 6: Configure Environment Variables

Create `/home/fleetapp/fleet_management/.env`:

```env
SECRET_KEY=your-very-long-random-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip
DB_NAME=fleet_management_prod
DB_USER=fleetapp
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
TIME_ZONE=Asia/Riyadh
```

**Generate a secure SECRET_KEY**:
```bash
python3.11 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 7: Run Django Setup

```bash
# Activate virtual environment
source /home/fleetapp/fleet_management/venv/bin/activate

# Navigate to project directory
cd /home/fleetapp/fleet_management

# Run migrations
python3.11 manage.py makemigrations
python3.11 manage.py migrate

# Create superuser and seed data
python3.11 manage.py setup_initial_data

# Collect static files
python3.11 manage.py collectstatic --noinput

# Create media directories
mkdir -p media/cars media/equipment media/calibration_certificates
chmod -R 755 media/
```

## Step 8: Configure Gunicorn

Create `/home/fleetapp/fleet_management/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
errorlog = "/home/fleetapp/fleet_management/logs/gunicorn_error.log"
accesslog = "/home/fleetapp/fleet_management/logs/gunicorn_access.log"
loglevel = "info"
```

Create logs directory:
```bash
mkdir -p /home/fleetapp/fleet_management/logs
```

## Step 9: Create Systemd Service

Create `/etc/systemd/system/fleet-management.service`:

```ini
[Unit]
Description=Fleet Management System Gunicorn Daemon
After=network.target

[Service]
User=fleetapp
Group=fleetapp
WorkingDirectory=/home/fleetapp/fleet_management
Environment="PATH=/home/fleetapp/fleet_management/venv/bin"
ExecStart=/home/fleetapp/fleet_management/venv/bin/gunicorn \
    --config /home/fleetapp/fleet_management/gunicorn_config.py \
    fleet_management.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fleet-management
sudo systemctl start fleet-management
sudo systemctl status fleet-management
```

## Step 10: Configure Nginx

**Security Note**: Media files (uploaded images) are now served securely through Django views that require authentication. This prevents unauthorized access to uploaded files.

Create `/etc/nginx/sites-available/fleet-management`:

```nginx
upstream fleet_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 50M;

    access_log /var/log/nginx/fleet_access.log;
    error_log /var/log/nginx/fleet_error.log;

    location /static/ {
        alias /home/fleetapp/fleet_management/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files are now served securely through Django views
    # No direct access to /media/ directory for security

    location / {
        proxy_pass http://fleet_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/fleet-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 11: Configure SSL with Let's Encrypt (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot will automatically configure Nginx for HTTPS
```

The Nginx configuration will be automatically updated to:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of configuration
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Step 12: Configure Firewall

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## Step 13: Set Up Automated Backups

Create `/home/fleetapp/backup_database.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/fleetapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="fleet_management_prod"
DB_USER="fleetapp"

mkdir -p $BACKUP_DIR

# Backup database
PGPASSWORD="your_secure_password_here" pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /home/fleetapp/fleet_management/media/

# Delete backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

Make it executable:
```bash
chmod +x /home/fleetapp/backup_database.sh
```

Add to crontab (daily at 2 AM):
```bash
crontab -e
```

Add this line:
```
0 2 * * * /home/fleetapp/backup_database.sh >> /home/fleetapp/backup.log 2>&1
```

## Step 14: Monitoring and Maintenance

### Check Application Status
```bash
sudo systemctl status fleet-management
```

### View Application Logs
```bash
# Gunicorn logs
tail -f /home/fleetapp/fleet_management/logs/gunicorn_error.log
tail -f /home/fleetapp/fleet_management/logs/gunicorn_access.log

# Nginx logs
sudo tail -f /var/log/nginx/fleet_error.log
sudo tail -f /var/log/nginx/fleet_access.log

# Systemd logs
sudo journalctl -u fleet-management -f
```

### Restart Application
```bash
sudo systemctl restart fleet-management
```

### Update Application
```bash
# Switch to application user
sudo su - fleetapp

# Navigate to project directory
cd /home/fleetapp/fleet_management

# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using git)
git pull

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python3.11 manage.py migrate

# Collect static files
python3.11 manage.py collectstatic --noinput

# Restart the service
sudo systemctl restart fleet-management
```

## Security Checklist

- [ ] DEBUG is set to False in production
- [ ] SECRET_KEY is unique and secure
- [ ] Database password is strong and secure
- [ ] ALLOWED_HOSTS is properly configured
- [ ] SSL/HTTPS is enabled
- [ ] Firewall is configured
- [ ] Regular backups are scheduled
- [ ] File permissions are properly set
- [ ] PostgreSQL is not accessible from outside
- [ ] Admin password is changed from default
- [ ] Server is regularly updated

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_car_fleet_no ON inventory_car(fleet_no);
CREATE INDEX idx_car_plate_no_en ON inventory_car(plate_no_en);
CREATE INDEX idx_equipment_door_no ON inventory_equipment(door_no);
```

### Enable Nginx Gzip Compression
Add to Nginx configuration:
```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

### Configure PostgreSQL for Production
Edit `/etc/postgresql/*/main/postgresql.conf`:
```conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Troubleshooting

### Application Won't Start
1. Check systemd logs: `sudo journalctl -u fleet-management -n 50`
2. Check Gunicorn logs: `tail -f /home/fleetapp/fleet_management/logs/gunicorn_error.log`
3. Verify database connection
4. Check file permissions

### 502 Bad Gateway
1. Ensure Gunicorn is running: `sudo systemctl status fleet-management`
2. Check Nginx error logs: `sudo tail -f /var/log/nginx/fleet_error.log`
3. Verify proxy_pass configuration in Nginx

### Static Files Not Loading
1. Run `python3.11 manage.py collectstatic --noinput`
2. Check Nginx static file configuration
3. Verify file permissions: `chmod -R 755 /home/fleetapp/fleet_management/staticfiles/`

### Database Connection Errors
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify database credentials in `.env`
3. Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*-main.log`

## Maintenance Tasks

### Weekly
- Review application logs for errors
- Check disk space usage
- Verify backups are working

### Monthly
- Update system packages: `sudo apt update && sudo apt upgrade`
- Review and optimize database
- Check SSL certificate expiration

### Quarterly
- Review and update dependencies
- Security audit
- Performance review

## Support

For production issues:
1. Check logs first (application, Nginx, PostgreSQL)
2. Review this deployment guide
3. Consult Django deployment documentation
4. Check server resource usage (CPU, memory, disk)

## Additional Resources

- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- Gunicorn Documentation: https://docs.gunicorn.org/
- Nginx Documentation: https://nginx.org/en/docs/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Let's Encrypt: https://letsencrypt.org/

