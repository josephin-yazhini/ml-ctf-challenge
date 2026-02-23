# ML CTF Platform - Quick Reference Guide

## 🚀 Getting Started (5 Minutes)

### Installation
```bash
# 1. Clone/navigate to project
cd ml-ctf-challenge

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize database
cd src
python main.py --init-db

# 6. Run application
python main.py

# 7. Open browser
# http://127.0.0.1:5000
```

---

## 📁 File Structure Quick Guide

```
ml-ctf-challenge/
├── src/
│   ├── main.py                 # Flask app factory, database init
│   ├── config.py              # Configuration for dev/prod
│   ├── models.py              # Database models (User, Challenge, Flag, etc.)
│   │
│   ├── routes/
│   │   ├── __init__.py       # Package init
│   │   ├── auth.py           # Login, register, password change
│   │   ├── api.py            # Flag submission, leaderboard, stats
│   │   └── challenges.py      # Challenge pages, dashboard
│   │
│   ├── templates/             # HTML pages (Jinja2)
│   │   ├── base.html         # Master template
│   │   ├── index.html        # Homepage
│   │   ├── challenge.html    # Single challenge page
│   │   ├── challenges.html   # All challenges list
│   │   ├── dashboard.html    # User progress
│   │   ├── leaderboard.html # Ranking table
│   │   ├── login.html        # Login form
│   │   └── register.html     # Registration form
│   │
│   └── static/
│       ├── styles.css        # Global styling
│       └── script.js         # JavaScript utilities
│
├── instance/
│   └── ctf.db               # SQLite database (auto-created)
│
├── README.md                 # Main documentation
├── QUICK_START.md           # 5-min setup guide
├── IMPLEMENTATION_GUIDE.md  # Technical architecture
├── IMPLEMENTATION_SUMMARY.md # Component overview
├── ARCHITECTURE.md          # System design diagrams
├── TROUBLESHOOTING.md       # FAQ & common issues
├── DEPLOYMENT.md            # Production deployment
├── requirements.txt         # Python dependencies
└── setup.sh                 # Automated setup script
```

---

## 🔑 Key Commands

### Running the App
```bash
# Development (hot reload, debug mode)
cd src
python main.py --debug

# Production
set FLASK_ENV=production
python main.py

# Different port
set FLASK_PORT=8000
python main.py

# Initialize database only
python main.py --init-db
```

### Working with Database

```bash
# Python shell (interactive)
cd src
python
>>> from main import create_app
>>> from models import db, User, Challenge, Flag
>>> app = create_app()
>>> app.app_context().push()

# List all users
>>> users = User.query.all()
>>> for u in users: print(f"{u.username}: {u.total_points} pts")

# List challenges
>>> challenges = Challenge.query.all()
>>> for c in challenges: print(f"{c.id}: {c.title} ({c.difficulty})")

# List flags in challenge
>>> chall = Challenge.query.get(1)
>>> for f in chall.flags: print(f"Flag {f.flag_order}: {f.flag_text}")

# Exit
>>> exit()
```

### Database Operations

```bash
# Backup SQLite
cp instance/ctf.db backups/ctf_backup.db

# Reset database (delete all data)
rm instance/ctf.db
# Then run: python main.py --init-db

# Export users to CSV
python -c "
from main import create_app
from models import db, User
import csv

app = create_app()
with app.app_context():
    users = User.query.all()
    with open('users.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'email', 'points'])
        for u in users:
            writer.writerow([u.username, u.email, u.total_points])
"
```

---

## 🔐 User Management

### Create User
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User(username='john', email='john@example.com')
    user.set_password('SecurePass123')
    db.session.add(user)
    db.session.commit()
    print(f"Created user: {user.username}")
```

### Reset User Password
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='john').first()
    user.set_password('NewPassword123')
    db.session.commit()
    print("Password reset!")
```

### Delete User
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='john').first()
    db.session.delete(user)
    db.session.commit()
    print("User deleted!")
```

### Reset User Progress
```python
from main import create_app
from models import db, User, Submission, Score

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='john').first()
    Submission.query.filter_by(user_id=user.id).delete()
    Score.query.filter_by(user_id=user.id).delete()
    user.total_points = 0
    db.session.commit()
    print("Progress reset!")
```

---

## 🎯 Challenge Management

### Create New Challenge
```python
from main import create_app
from models import db, Challenge, Flag

app = create_app()
with app.app_context():
    chall = Challenge(
        title='Reverse Engineering',
        description='Reverse engineer the binary to find flags...',
        difficulty='hard',
        max_points=100,
        source_file_url='https://example.com/binary.zip'
    )
    db.session.add(chall)
    db.session.flush()
    
    # Add 4 flags
    for i, text in enumerate(['flag1', 'flag2', 'flag3', 'flag4']):
        flag = Flag(
            challenge_id=chall.id,
            flag_text=text,
            flag_order=i+1,
            flag_context=f'Hint for flag {i+1}',
            points_value=25
        )
        db.session.add(flag)
    
    db.session.commit()
    print(f"Challenge created!")
```

### Edit Challenge
```python
from main import create_app
from models import db, Challenge

app = create_app()
with app.app_context():
    chall = Challenge.query.get(1)
    chall.title = 'New Title'
    chall.description = 'New description...'
    db.session.commit()
    print("Challenge updated!")
```

### Edit Flag
```python
from main import create_app
from models import db, Flag

app = create_app()
with app.app_context():
    flag = Flag.query.get(1)
    flag.flag_text = 'new_flag_value'
    flag.flag_context = 'Updated hint'
    db.session.commit()
    print("Flag updated!")
```

### Delete Challenge
```python
from main import create_app
from models import db, Challenge

app = create_app()
with app.app_context():
    chall = Challenge.query.get(1)
    db.session.delete(chall)
    db.session.commit()
    print("Challenge deleted!")
```

---

## 🏆 Leaderboard & Scoring

### View Top 10 Users
```python
from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    users = User.query.order_by(User.total_points.desc()).limit(10).all()
    for rank, user in enumerate(users, 1):
        print(f"{rank}. {user.username}: {user.total_points} pts")
```

### View Challenge Statistics
```python
from main import create_app
from models import db, Challenge, Score

app = create_app()
with app.app_context():
    chall = Challenge.query.get(1)
    num_solvers = db.session.query(Score).join(
        Score.flag
    ).filter(Flag.challenge_id == chall.id).group_by(Score.user_id).count()
    print(f"{chall.title}: {num_solvers} solvers")
```

### Recalculate All Points
```python
from main import create_app
from models import db, User, Score

app = create_app()
with app.app_context():
    for user in User.query.all():
        user.total_points = sum(s.points for s in user.scores)
    db.session.commit()
    print("Points recalculated!")
```

---

## 🌐 API Quick Reference

### Flag Submission
```bash
curl -X POST http://localhost:5000/api/submit-flag \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": 1,
    "submitted_flag": "flag_value"
  }'

# Response:
{
  "success": true,
  "message": "Correct! +25 points",
  "points_earned": 25,
  "total_points": 75,
  "progress": 75
}
```

### Get Leaderboard
```bash
curl http://localhost:5000/api/leaderboard?limit=10

# Response:
{
  "leaderboard": [
    {"rank": 1, "username": "alice", "email": "alice@example.com", "total_points": 400},
    ...
  ]
}
```

### Get User Stats
```bash
curl http://localhost:5000/api/user/1/stats

# Response:
{
  "username": "alice",
  "total_points": 400,
  "completed_challenges": 4,
  "total_flags": 16,
  "progress": 80
}
```

### Get Challenge List
```bash
curl http://localhost:5000/api/challenges

# Response:
{
  "challenges": [
    {
      "id": 1,
      "title": "PII Detection",
      "difficulty": "easy",
      "max_points": 100
    },
    ...
  ]
}
```

---

## 🛠️ Troubleshooting One-Liners

```bash
# Reset everything (delete database)
rm instance/ctf.db && python main.py --init-db

# Check if port is in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Mac/Linux

# Kill process on port
taskkill /PID <PID> /F         # Windows
kill -9 <PID>                  # Mac/Linux

# Check database tables
sqlite3 instance/ctf.db ".tables"

# View database schema
sqlite3 instance/ctf.db ".schema users"

# Run interactive Python with app context
cd src && python
from main import create_app
app = create_app()
app.app_context().push()
# Now you can use db and models directly
```

---

## 📊 Default Test Flags

All test challenges come with these flags:

```
Challenge 1 - PII Detection (Easy):
  Flag 1: ssn_123456789
  Flag 2: email_leak_confirmed
  Flag 3: address_exposed
  Flag 4: final_flag_pii

Challenge 2 - SQL Injection (Medium):
  Flag 1: sql_union_attack
  Flag 2: admin_bypass_success
  Flag 3: database_extracted
  Flag 4: sql_mastery_complete

Challenge 3 - ML Evasion (Hard):
  Flag 1: adversarial_example_found
  Flag 2: model_fooled_successfully
  Flag 3: evasion_technique_worked
  Flag 4: ml_security_conquered

Challenge 4 - Cryptography (Expert):
  Flag 1: crypto_broken_rsa
  Flag 2: decryption_successful
  Flag 3: key_recovered
  Flag 4: crypto_expert_level

Challenge 5 - Fraud Detection (Medium):
  Flag 1: fraud_pattern_found
  Flag 2: anomaly_detected
  Flag 3: scheme_exposed
  Flag 4: fraud_prevention_complete
```

---

## 🔧 Configuration Quick Changes

### Change Secret Key
```python
# In config.py
class Config:
    SECRET_KEY = 'your-new-secret-key-here'
    # Or generate random:
    # from secrets import token_hex
    # SECRET_KEY = token_hex(32)
```

### Change Database
```python
# In config.py for development:
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/ml_ctf'
    # Or keep SQLite:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ctf.db'
```

### Change Rate Limit
```python
# In src/routes/api.py, around line 45
MAX_SUBMISSIONS_PER_MINUTE = 10  # Change from 5
```

### Change Session Timeout
```python
# In config.py
from datetime import timedelta
PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Change from 1 day
```

### Change Debug Mode
```python
# In main.py when running
app.run(debug=False)  # Change from True for production

# Or environment variable:
export FLASK_DEBUG=0
python main.py
```

---

## 📝 Common Development Tasks

### Add New Page/Route
```python
# 1. Create route in routes/challenges.py
@app.route('/new-page')
def new_page():
    return render_template('new_page.html')

# 2. Create template in templates/new_page.html
# 3. Add navigation link in templates/base.html
# 4. Restart Flask
```

### Add New Database Field
```python
# 1. Edit models.py - add column to class
class User(db.Model):
    # ... existing fields ...
    new_field = db.Column(db.String(100))

# 2. Restart Flask (it recreates schema)
# OR run migration:
# python main.py --init-db

# 3. Update forms/templates if needed
```

### Add New API Endpoint
```python
# In src/routes/api.py
@app.route('/api/new-endpoint', methods=['GET'])
def new_endpoint():
    data = {"message": "Hello"}
    return jsonify(data)

# Test with:
# curl http://localhost:5000/api/new-endpoint
```

---

## 🚀 Performance Tips

- Use database indexes on frequently queried fields
- Cache leaderboard with Redis
- Use CDN for static files (CSS, JS, images)
- Enable gzip compression in Nginx
- Use connection pooling for PostgreSQL
- Monitor slow queries with SQLALCHEMY_ECHO

---

## 🔒 Security Reminders

- Never commit `.env` files with secrets
- Use strong passwords (20+ characters with mixed case, numbers)
- Enable HTTPS in production
- Restrict CORS to your domain
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Use environment variables for sensitive data
- Enable rate limiting on all user input endpoints

---

## 📚 Further Reading

- **QUICK_START.md** - 5-minute setup
- **IMPLEMENTATION_GUIDE.md** - Technical details
- **ARCHITECTURE.md** - System design
- **TROUBLESHOOTING.md** - FAQ & common issues
- **DEPLOYMENT.md** - Production setup

---

**Everything working?** You're ready to:
1. Customize challenges
2. Add users
3. Deploy to production
4. Share with others!

Good luck with your CTF platform! 🎯
