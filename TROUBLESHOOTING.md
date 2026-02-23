# ML CTF Platform - Troubleshooting & FAQ

## Common Issues & Solutions

### 1. Database Issues

#### Issue: "sqlite3.OperationalError: no such table"
**Cause**: Database hasn't been initialized yet

**Solutions**:
```bash
# Option 1: Delete old database and reinitialize
rm instance/ctf.db

# Option 2: Initialize database on app startup
cd src
python main.py --init-db

# Option 3: Programmatically (Python shell)
from main import create_app
app = create_app()
with app.app_context():
    from models import db
    db.create_all()
```

---

#### Issue: "database is locked"
**Cause**: Multiple Flask instances or long-running queries

**Solutions**:
```bash
# Kill all Python processes
pkill -f flask
pkill -f python

# Wait 30 seconds, then restart
# Or use WAL mode in SQLite (production-grade)
export SQLALCHEMY_ENGINE_OPTIONS='{"connect_args": {"timeout": 10}}'
```

---

#### Issue: "IntegrityError on duplicate key"
**Cause**: Unique constraint violation (username, email, or score)

**Solutions**:
```python
# In Python shell:
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    # Find duplicate
    users = User.query.filter_by(username='duplicate').all()
    for user in users[1:]:  # Keep first, delete others
        db.session.delete(user)
    db.session.commit()
```

---

### 2. Authentication Issues

#### Issue: "Login fails but password is correct"
**Cause**: User password not properly hashed or session expired

**Solutions**:
```bash
# Clear browser cookies
# Ctrl+Shift+Delete → Clear all cookies

# Reset user password (Python shell):
from main import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='your_username').first()
    if user:
        user.password_hash = generate_password_hash('newpassword', method='pbkdf2:sha256')
        db.session.commit()
        print("Password reset successfully")
```

---

#### Issue: "Register button doesn't work"
**Cause**: JavaScript error or invalid form data

**Solutions**:
```bash
# 1. Check browser console (F12 → Console tab)
# 2. Look for error messages (red text)
# 3. Verify Flask server is running (should see requests)
# 4. Clear browser cache: Ctrl+Shift+Delete

# 4. Check server logs for validation errors
# Should show password validation details
```

**If registration always fails**:
```python
# Manually create user (Python shell)
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('SecurePassword123')
    db.session.add(user)
    db.session.commit()
    print("User created!")
```

---

### 3. Flag Submission Issues

#### Issue: "Flag submission returns 429 (Too Many Attempts)"
**Cause**: Rate limiting (5 attempts per 60 seconds)

**Solutions**:
```bash
# Wait 60 seconds before submitting again
# Check server logs to see when rate limit resets

# To increase limit (development only):
# Edit: src/routes/api.py, line 45
MAX_SUBMISSIONS_PER_MINUTE = 10  # Change from 5 to 10
```

---

#### Issue: "Correct flag shows as incorrect"
**Cause**: Whitespace, case sensitivity, or regex mismatch

**Solutions**:
```python
# Check flag in database (Python shell):
from main import create_app
from models import db, Flag, Challenge

app = create_app()
with app.app_context():
    chall = Challenge.query.first()
    for flag in chall.flags:
        print(f"Flag {flag.flag_order}: '{flag.flag_text}'")
        print(f"Pattern: {flag.flag_context}")

# When submitting, copy exactly as shown above
# No extra spaces or different casing
```

---

#### Issue: "Points not awarded after correct flag"
**Cause**: Score already exists OR database transaction failed

**Solutions**:
```python
# Check if score was awarded (Python shell):
from main import create_app
from models import db, Score, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='your_username').first()
    scores = Score.query.filter_by(user_id=user.id).all()
    for score in scores:
        print(f"Flag {score.flag_id}: {score.points} points")
    
    print(f"Total points: {user.total_points}")

# If missing, add score manually:
from models import Flag
flag = Flag.query.get(flag_id)
score = Score(user_id=user.id, flag_id=flag.id, points=flag.points_value)
db.session.add(score)
user.total_points = user.get_total_points()
db.session.commit()
```

---

### 4. Server Issues

#### Issue: "Address already in use: port 5000"
**Cause**: Flask server already running or port occupied

**Solutions**:
```bash
# Find process using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Mac/Linux

# Kill the process
taskkill /PID <PID> /F         # Windows
kill -9 <PID>                  # Mac/Linux

# Or use different port
set FLASK_PORT=5001           # Windows
export FLASK_PORT=5001        # Mac/Linux
python src/main.py
```

---

#### Issue: "Module not found: Flask, SQLAlchemy, etc."
**Cause**: Dependencies not installed or wrong virtual environment

**Solutions**:
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# If still failing, upgrade pip first
python -m pip install --upgrade pip

# Verify installation
pip list | grep Flask
pip list | grep SQLAlchemy

# Use Python directly if pip fails
python -m pip install Flask Flask-SQLAlchemy Flask-Login
```

---

#### Issue: "Template not found" error
**Cause**: Flask can't locate HTML files

**Solutions**:
```bash
# Verify file structure:
src/
├── main.py
└── templates/
    ├── base.html
    ├── challenge.html
    └── ...

# File must be in src/templates/ directory, not root

# Check Flask template loader:
# In Python shell, verify app.template_folder
```

---

### 5. Performance Issues

#### Issue: "Website is slow to load"
**Causes**: Large database, inefficient queries, missing indexes

**Solutions**:
```python
# Profile database queries (Python shell):
from main import create_app
from flask_sqlalchemy import get_debug_queries

app = create_app()
app.config['SQLALCHEMY_ECHO'] = True  # Print SQL queries

with app.app_context():
    # Run your queries
    # All SQL will be printed

# Check query count - too many means N+1 problem
```

**For leaderboard slowness**:
```python
# Add caching (Redis):
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/leaderboard')
@cache.cached(timeout=30)  # Cache 30 seconds
def leaderboard():
    ...
```

---

#### Issue: "Leaderboard doesn't update in real-time"
**Cause**: It's cached OR client-side auto-refresh isn't working

**Solutions**:
```javascript
// In browser console, check refresh interval:
// Should see network requests to /api/leaderboard every 30 seconds

// Force refresh:
location.reload()

// Or check JavaScript console (F12) for errors
// Look for failed fetch requests
```

---

### 6. CORS & Security Issues

#### Issue: "CORS error: Cross-Origin Request Blocked"
**Cause**: Frontend and backend on different domains

**Solutions**:
```python
# Already handled in main.py:
from flask_cors import CORS
CORS(app)

# If issue persists, check:
# 1. Frontend and backend both running
# 2. Correct URLs in JavaScript
# 3. Browser console for exact error message
```

---

#### Issue: "Session expires too quickly"
**Cause**: Default Flask session timeout

**Solutions**:
```python
# In config.py:
PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Change from 1 day

# Also in your route:
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)
```

---

### 7. Data Issues

#### Issue: "Leaderboard shows wrong points"
**Cause**: User.total_points out of sync with Score records

**Solutions**:
```python
# Recalculate all points (Python shell):
from main import create_app
from models import db, User, Score

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        user.total_points = sum(s.points for s in user.scores)
    db.session.commit()
    print("Points recalculated!")
```

---

#### Issue: "Challenge progress doesn't update"
**Cause**: JavaScript not refreshing or backend calculation wrong

**Solutions**:
```javascript
// Force refresh progress (browser console):
fetch('/api/challenges')
  .then(r => r.json())
  .then(d => console.log(d))

// Clear browser cache: Ctrl+Shift+Delete
// Hard refresh: Ctrl+F5
```

---

### 8. Deployment Issues

#### Issue: "Website works locally but not on deployed server"
**Causes**: Environment variables, database path, static files

**Solutions**:
```bash
# On production server:

# 1. Set environment
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_URL=postgresql://...

# 2. Run with Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'src.main:create_app()'

# 3. Verify static files served
# CSS/JS should load (use Nginx to serve them)

# 4. Check logs
# Look for error messages in server logs
```

---

---

## FAQ

### Q: Can I customize the challenges?
**A**: Yes! Edit in Python shell:
```python
from main import create_app
from models import db, Challenge, Flag

app = create_app()
with app.app_context():
    # Edit challenge
    chall = Challenge.query.get(1)
    chall.title = "New Title"
    chall.description = "New description..."
    db.session.commit()
    
    # Edit flags
    flag = chall.flags[0]
    flag.flag_text = "newinput"
    db.session.commit()
```

---

### Q: How do I add a new challenge?
**A**: Use this script:
```python
from main import create_app
from models import db, Challenge, Flag

app = create_app()
with app.app_context():
    challenge = Challenge(
        title='New Challenge',
        description='Description here...',
        difficulty='medium',  # easy, medium, hard, expert
        max_points=100,
        source_file_url='url_to_download'
    )
    db.session.add(challenge)
    db.session.flush()  # Get challenge ID
    
    # Add 4 flags
    for i, flag_text in enumerate(['flag1', 'flag2', 'flag3', 'flag4']):
        flag = Flag(
            challenge_id=challenge.id,
            flag_text=flag_text,
            flag_order=i+1,
            flag_context='Context/hint',
            points_value=25
        )
        db.session.add(flag)
    
    db.session.commit()
    print(f"Challenge created with ID: {challenge.id}")
```

---

### Q: How do I reset a user's progress?
**A**: 
```python
from main import create_app
from models import db, User, Submission, Score

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='username').first()
    
    # Delete all submissions and scores
    Submission.query.filter_by(user_id=user.id).delete()
    Score.query.filter_by(user_id=user.id).delete()
    
    # Reset points
    user.total_points = 0
    db.session.commit()
    print("User progress reset!")
```

---

### Q: How do I view all user accounts?
**A**:
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"{user.username}: {user.email} - {user.total_points} pts")
```

---

### Q: Can I use regex for flag validation?
**A**: Yes! Use `REGEX:` prefix:
```python
from models import Flag

# Exact match
flag.flag_text = "exact_flag_value"
flag.flag_context = "Context"

# Regex pattern
flag.flag_text = "REGEX:flag_[0-9]{4}"  # Matches: flag_0000 to flag_9999
flag.flag_context = "Must match pattern"
```

---

### Q: How do I backup the database?
**A**:
```bash
# Backup SQLite
cp instance/ctf.db backups/ctf_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump -U username database_name > backup.sql

# Restore
psql -U username database_name < backup.sql
```

---

### Q: Can I change the port?
**A**:
```bash
# Environment variable
set FLASK_PORT=8000          # Windows
export FLASK_PORT=8000       # Mac/Linux

python src/main.py

# Or in Python
app.run(port=8000)
```

---

### Q: How do I reset the admin password?
**A**: There's no separate admin account. Create one with Python shell:
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com'
    )
    admin.set_password('AdminPassword123')
    db.session.add(admin)
    db.session.commit()
```

---

### Q: How do I delete a user?
**A**:
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='username').first()
    db.session.delete(user)
    db.session.commit()
    print("User deleted!")
```

---

### Q: Can I export leaderboard as CSV?
**A**: Yes, add this route:
```python
import csv
from flask import send_file
from io import StringIO

@app.route('/api/leaderboard/export')
def export_leaderboard():
    users = User.query.order_by(User.total_points.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Rank', 'Username', 'Total Points'])
    
    for i, user in enumerate(users, 1):
        writer.writerow([i, user.username, user.total_points])
    
    output.seek(0)
    return send_file(
        StringIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='leaderboard.csv'
    )
```

---

### Q: How do I enable HTTPS?
**A**: In production with Let's Encrypt:
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d yourdomain.com

# Configure Nginx to use HTTPS
# Then restart Flask/Gunicorn
```

---

### Q: Can users change their username?
**A**: Currently no, but you can add:
```python
@app.route('/auth/change-username', methods=['POST'])
@login_required
def change_username():
    new_username = request.json.get('username')
    
    if User.query.filter_by(username=new_username).first():
        return {'error': 'Username taken'}, 409
    
    current_user.username = new_username
    db.session.commit()
    return {'success': True}
```

---

For more help, check the logs:
```bash
# Flask development logs (if running with --debug)
# Check terminal output

# Browser console logs
# F12 → Console tab

# Python error stack trace
# Shows in terminal and sometimes ctf.log
```

**Need more help?** Check IMPLEMENTATION_GUIDE.md or ARCHITECTURE.md
