# Deployment Guide

Deploy your AI Book Assistant to production with this comprehensive guide.

## 🚀 Production Deployment Options

### Option 1: PythonAnywhere (Recommended for Beginners)

**Pros:** Free, easy setup, Python pre-installed  
**Cons:** Limited resources, shared environment

#### Steps:
1. **Create account** at [pythonanywhere.com](https://www.pythonanywhere.com)
2. **Clone repository** to PythonAnywhere
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set environment variables** in PythonAnywhere dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FLASK_ENV`: `production`
5. **Configure web app:**
   ```bash
   python app.py
   ```
6. **Reload web app** in PythonAnywhere dashboard

**Access URL:** `https://yourusername.pythonanywhere.com`

---

### Option 2: Heroku

**Pros:** Git integration, scalable, add-ons  
**Cons:** Requires credit card, dyno hours

#### Steps:
1. **Install Heroku CLI:**
   ```bash
   npm install -g heroku
   ```
2. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```
3. **Set environment variables:**
   ```bash
   heroku config:set OPENAI_API_KEY=your-key-here
   heroku config:set FLASK_ENV=production
   ```
4. **Create Procfile:**
   ```procfile
   web: gunicorn app:app
   ```
5. **Deploy:**
   ```bash
   git init
   git add .
   git commit -m "Initial deploy"
   heroku git:remote -a heroku https://git.heroku.com/your-app.git
   git push heroku main
   ```

**Access URL:** `https://your-app-name.herokuapp.com`

---

### Option 3: DigitalOcean App Platform

**Pros:** Full control, good performance  
**Cons:** Requires setup, paid

#### Steps:
1. **Create account** at [digitalocean.com](https://www.digitalocean.com)
2. **Create App** with Python runtime
3. **Set environment variables** in App Settings:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FLASK_ENV`: `production`
   - `FLASK_APP`: `app.py`
4. **Deploy** using Git or GitHub integration

---

### Option 4: AWS Elastic Beanstalk

**Pros:** AWS integration, scalable  
**Cons:** Complex setup, AWS learning curve

#### Steps:
1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```
2. **Initialize application:**
   ```bash
   eb init -p python
   ```
3. **Create application:**
   ```bash
   eb create your-app-name
   ```
4. **Set environment variables:**
   ```bash
   eb setenv OPENAI_API_KEY your-key-here
   eb setenv FLASK_ENV production
   ```
5. **Deploy:**
   ```bash
   eb deploy
   ```

---

### Option 5: VPS/Dedicated Server

**Pros:** Full control, best performance  
**Cons:** Requires server management

#### Steps:
1. **Choose provider** (Linode, Vultr, DigitalOcean, etc.)
2. **Create server** with Ubuntu 20.04+
3. **Setup domain** and DNS
4. **Install requirements:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv
   git clone your-repo
   cd your-repo
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Configure web server** (nginx + gunicorn):
   ```bash
   sudo apt install nginx
   pip install gunicorn
   ```
6. **Setup systemd service:**
   ```bash
   sudo nano /etc/systemd/ai-book-assistant.service
   ```
7. **Configure nginx** to proxy to gunicorn
8. **Start service:**
   ```bash
   sudo systemctl start ai-book-assistant
   sudo systemctl enable ai-book-assistant
   ```

## 🔧 Production Configuration

### Environment Variables
Set these in your production environment:

```bash
# Required
OPENAI_API_KEY=sk-your-production-key-here
FLASK_ENV=production

# Optional (Firebase)
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/production-service-account.json
FIREBASE_WEB_API_KEY=your-production-web-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-production-project-id
FIREBASE_STORAGE_BUCKET=your-production-storage.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-production-sender-id
FIREBASE_APP_ID=your-production-app-id
```

### Security Settings
```python
# Disable debug mode
app.run(debug=False, host='0.0.0.0', port=5000)

# Use production server
gunicorn app:app --workers 4 --bind 0.0.0.0:5000
```

### File Permissions
```bash
# Secure uploads folder
chmod 755 uploads/
chmod 644 uploads/*

# Secure logs
chmod 755 logs/
chmod 644 logs/*
```

## 🌐 Domain and SSL

### SSL Certificate
```bash
# Let's Encrypt (Free)
sudo apt install certbot
sudo certbot --nginx -d yourdomain.com

# Or use Cloudflare SSL (Free)
# Add domain to Cloudflare dashboard
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring

### Application Monitoring
```bash
# Use process manager
pm2 start app.py

# Or systemd
sudo systemctl status ai-book-assistant
sudo journalctl -u ai-book-assistant -f
```

### Log Management
```bash
# Log rotation
sudo nano /etc/logrotate.d/ai-book-assistant

# Monitor logs
tail -f logs/ai-book-assistant.log
```

## 🔍 Performance Optimization

### Database Optimization
- Use Firebase Firestore indexes
- Implement caching for frequent requests
- Optimize PDF processing

### CDN for Static Files
```javascript
// Use CDN for assets
<link href="https://cdn.yourdomain.com/style.css" rel="stylesheet">
<script src="https://cdn.yourdomain.com/app.js"></script>
```

### Compression
```python
# Enable gzip compression
from flask_compress import Compress
Compress(app)

# Nginx compression
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## 🚨 Troubleshooting Production

### Common Issues

#### 502 Bad Gateway
- Check if gunicorn is running
- Verify port binding
- Check firewall settings

#### 504 Gateway Timeout
- Increase timeout in nginx
- Check server resources
- Optimize PDF processing

#### Memory Issues
- Monitor memory usage
- Implement streaming for large files
- Add swap space if needed

#### Database Connection
- Verify Firebase credentials
- Check network connectivity
- Review Firebase console

## 📞 Support

For deployment issues:
1. Check application logs: `logs/ai-book-assistant.log`
2. Verify environment variables
3. Test API endpoints: `python utils/test_api.py`
4. Review this guide and [API documentation](API.md)

---

*Deploy with confidence using this guide!*
