# Troubleshooting Guide

Common issues and solutions for AI Book Assistant.

## 🔧 Quick Fixes

### 🚨 API Key Issues

#### Problem: "OpenAI API key not set"
**Symptoms:**
- 503 Service Unavailable errors
- API key warnings in logs

**Solutions:**
1. **Check .env file:**
   ```bash
   cat .env
   ```
2. **Verify format:**
   ```
   OPENAI_API_KEY=sk-your-key-here
   # No quotes, no extra spaces
   ```
3. **Restart application:**
   ```bash
   python app.py
   ```

#### Problem: "OpenAI quota exceeded"
**Symptoms:**
- 429 Too Many Requests errors
- Features work intermittently

**Solutions:**
1. **Add billing to OpenAI:**
   - Go to: https://platform.openai.com/account/billing
   - Add payment method (minimum $5)
   - Wait 5-10 minutes for activation
2. **Use different API key:**
   - Generate new key from: https://platform.openai.com/api-keys
3. **Implement rate limiting:**
   - Add delays between requests
   - Show user-friendly error messages

---

### 📄 PDF Processing Issues

#### Problem: "Could not extract text from PDF"
**Symptoms:**
- Upload fails with text extraction error
- Works with some PDFs but not others

**Solutions:**
1. **Check PDF type:**
   - Ensure PDF has selectable text (not scanned images)
   - Try copying text from PDF manually
2. **Install OCR (for scanned PDFs):**
   ```bash
   # Windows
   # Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   ```
3. **Try different extraction method:**
   - The app tries multiple methods automatically
   - Check logs for which method failed

#### Problem: "File too large"
**Symptoms:**
- 413 Payload Too Large error
- Upload fails immediately

**Solutions:**
1. **Compress PDF:**
   - Use Adobe Acrobat or online tools
   - Aim for under 10MB if possible
2. **Split large documents:**
   - Upload in sections if applicable
3. **Check file size:**
   - Maximum is 16MB

---

### 🌐 Network & Connection Issues

#### Problem: "CORS error"
**Symptoms:**
- Browser console shows CORS errors
- Requests blocked by browser

**Solutions:**
1. **Check Flask-CORS configuration:**
   ```python
   # In app.py
   CORS(app, resources={
       r'/*': {
           'origins': ['http://localhost:5000', 'https://yourdomain.com'],
           'allow_headers': ['Authorization', 'Content-Type']
       }
   })
   ```
2. **Verify frontend URL:**
   - Ensure using correct domain in production
   - Check for typos in API calls

#### Problem: "Firebase authentication failed"
**Symptoms:**
- 401 Unauthorized errors
- Login redirects not working

**Solutions:**
1. **Check Firebase configuration:**
   ```bash
   # Verify .env variables
   echo $FIREBASE_WEB_API_KEY
   echo $FIREBASE_PROJECT_ID
   ```
2. **Check Firebase console:**
   - Ensure service account is active
   - Verify web app configuration
3. **Clear browser cache:**
   - Firebase auth tokens can cache
   - Try incognito/private browsing

---

### 🔧 Server Issues

#### Problem: "Port already in use"
**Symptoms:**
- Application fails to start
- "Address already in use" error

**Solutions:**
1. **Find and kill process:**
   ```bash
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <process_id>
   
   # Linux/Mac
   lsof -i :5000
   kill -9 <process_id>
   ```
2. **Use different port:**
   ```bash
   python app.py --port 5001
   ```
3. **Check for other services:**
   - Skype, Zoom, other development tools

#### Problem: "Module not found"
**Symptoms:**
- ImportError for flask, openai, etc.
- Application crashes on startup

**Solutions:**
1. **Check Python environment:**
   ```bash
   python -m pip list
   ```
2. **Install missing packages:**
   ```bash
   pip install flask openai python-dotenv flask-cors PyPDF2 pdfplumber gtts firebase-admin
   ```
3. **Use virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

### 🎨 Frontend Issues

#### Problem: "Static files not loading"
**Symptoms:**
- CSS/JS not applied
- 404 errors for assets

**Solutions:**
1. **Check Flask static configuration:**
   ```python
   # In app.py
   app = Flask(__name__, static_folder='frontend/static')
   ```
2. **Verify file paths:**
   - Check browser developer tools
   - Look for 404 errors on CSS/JS files
3. **Clear browser cache:**
   - Hard refresh: Ctrl+F5
   - Clear cache: Ctrl+Shift+Delete

#### Problem: "Firebase not initialized"
**Symptoms:**
- Login buttons not working
- Console errors about Firebase

**Solutions:**
1. **Check Firebase config:**
   ```javascript
   // In browser console
   console.log(window.__FIREBASE_CONFIG__);
   ```
2. **Verify Firebase SDK URLs:**
   - Check internet connection
   - Try different browser
3. **Check Firebase project settings:**
   - Ensure web app is properly configured

---

### 📊 Performance Issues

#### Problem: "Slow PDF processing"
**Symptoms:**
- Upload takes >30 seconds
- Timeout errors

**Solutions:**
1. **Optimize PDF:**
   - Remove unnecessary images
   - Compress if possible
2. **Increase timeout:**
   ```python
   # In upload route
   file.seek(0, os.SEEK_END)
   file_size = file.tell()
   if file_size > 10 * 1024 * 1024:  # 10MB
       return jsonify({'error': 'File too large for processing'}), 413
   ```
3. **Use streaming:**
   - Process PDF in chunks
   - Show progress to user

#### Problem: "Memory usage high"
**Symptoms:**
- Server becomes unresponsive
- Out of memory errors

**Solutions:**
1. **Monitor memory:**
   ```bash
   # Linux/Mac
   top -p python
   
   # Windows
   tasklist | findstr python
   ```
2. **Limit concurrent processing:**
   ```python
   # Add rate limiting
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=lambda: request.args.get("user"))
   ```
3. **Use production server:**
   ```bash
   gunicorn app:app --workers 2 --max-requests 1000
   ```

---

### 🔍 Debugging Tools

#### Application Logs
```bash
# Real-time log monitoring
tail -f logs/ai-book-assistant.log

# Search for errors
grep -i error logs/ai-book-assistant.log

# Filter by date
grep "2026-04-04" logs/ai-book-assistant.log
```

#### API Testing
```bash
# Test all endpoints
python utils/test_api.py

# Test specific endpoint
curl -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     http://localhost:5000/health
```

#### Browser Debugging
```javascript
// Enable detailed logging
localStorage.setItem('debug', 'true');

// Network monitoring
fetch('/api/session').then(r => r.json()).then(console.log);
```

---

### 📞 Getting Help

#### Self-Service Resources:
1. **Check logs first:** `logs/ai-book-assistant.log`
2. **Review this guide:** Follow relevant section
3. **Test API:** `python utils/test_api.py`
4. **Check documentation:** [API.md](API.md)

#### Community Support:
- **GitHub Issues:** Create detailed issue with logs
- **Stack Overflow:** Tag with `ai-book-assistant`
- **Discord/Slack:** Ask for help

#### Professional Support:
- **OpenAI Support:** https://help.openai.com
- **Firebase Support:** https://firebase.google.com/support
- **Flask Documentation:** https://flask.palletsprojects.com

---

## 🧪 Maintenance

### Regular Tasks
- [ ] Monitor log files for errors
- [ ] Update dependencies monthly
- [ ] Backup user data regularly
- [ ] Review API usage and quotas
- [ ] Security audit quarterly

### Backup Strategy
```bash
# Backup user uploads
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/

# Backup configuration
cp .env .env.backup-$(date +%Y%m%d)

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

---

*If you encounter an issue not covered here, please create a GitHub issue with:*
- *Error description*
- *Steps to reproduce*
- *Expected vs actual behavior*
- *System information*
- *Relevant logs*
