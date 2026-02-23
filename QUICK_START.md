# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Python Packages

```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python src/main.py --init-db
```

Creates SQLite database with 5 sample challenges and 20 flags.

### Step 3: Run Application

```bash
python src/main.py --debug
```

Opens at: **http://127.0.0.1:5000**

## First Time Users

### 1. Create Account
- Click **"Register"** on homepage
- Choose username, email, strong password
- Password requirements:
  - ✓ 8+ characters
  - ✓ At least 1 uppercase letter
  - ✓ At least 1 number

### 2. Login
- Use your credentials
- See dashboard with 0 points

### 3. Start Challenge
- Click **"Challenges"** in navigation
- Select **Challenge 1: Find Hidden PII** (Easy)
- Download the CSV dataset
- Analyze and submit flags:
  - `flag{found_ssn}` (25 pts)
  - `flag{found_credit_card}` (25 pts)
  - `flag{found_dob_pattern}` (25 pts)
  - `flag{prevention_recommendation}` (25 pts)

### 4. Track Progress
- **Dashboard**: See personal stats
- **Leaderboard**: View global rankings
- **Challenge Page**: Monitor per-challenge progress

## Test Submissions

Try these flags to test the system:

**Challenge 1** (Easy - PII Detection):
```
flag{found_ssn}
flag{found_credit_card}
flag{found_dob_pattern}
flag{prevention_recommendation}
```

**Challenge 2** (Medium - SQL Injection):
```
flag{sqli_basic}
flag{sqli_union}
flag{sqli_admin}
flag{sqli_bypass}
```

And so on for Challenges 3, 4, and 5.

## Common Commands

### Run with Custom Port
```bash
python src/main.py --debug --port 8000
```

### Initialize Fresh Database
```bash
rm src/ctf_challenge.db
python src/main.py --init-db
```

### Production Mode
```bash
python src/main.py  # --debug not included
```

## Project Files

| File | Purpose |
|------|---------|
| `src/main.py` | Flask app initialization & database setup |
| `src/models.py` | Database models (User, Challenge, Flag, etc) |
| `src/config.py` | Configuration settings |
| `src/routes/auth.py` | Login, register, authentication |
| `src/routes/api.py` | Flag submission, leaderboard, statistics |
| `src/routes/challenges.py` | Challenge views |
| `src/templates/` | HTML pages |
| `src/static/` | CSS, JavaScript, challenge files |

## API Quick Reference

### Submit Flag
```bash
curl -X POST http://localhost:5000/api/submit-flag \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": 1, "flag": "flag{found_ssn}"}'
```

### Get All Challenges
```bash
curl http://localhost:5000/api/challenges
```

### Get Leaderboard
```bash
curl http://localhost:5000/api/leaderboard
```

### Get User Stats
```bash
curl http://localhost:5000/api/user/1/stats
```

## Database Reset

If something goes wrong:

```bash
# Remove old database
rm src/ctf_challenge.db

# Reinitialize
python src/main.py --init-db
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "Port 5000 already in use"
```bash
python src/main.py --debug --port 5001
```

### "Database locked" error
- Close other instances
- Delete `ctf_challenge.db` and reinitialize
- Use PostgreSQL for production

### Flags not submitting
- Ensure you're logged in
- Check flag text exactly (case-insensitive in code)
- Wait 1 minute if rate limited (max 5 attempts/minute)

## Features Overview

### ✓ Authentication
- Secure password hashing
- Email validation
- Session management

### ✓ Challenges
- 5 progressively difficult challenges
- 4 flags per challenge (100 pts each)
- Downloadable source files
- Real-time validation

### ✓ Points System
- 25 points per flag
- Points awarded only for correct submissions
- Can't earn points twice for same flag

### ✓ Leaderboard
- Global ranking system
- Top 3 with special badges
- Updates every 30 seconds
- Shows total points and challenges completed

### ✓ User Dashboard
- Personal statistics
- Progress per challenge
- Visual progress bars
- Total points counter

## Advanced Configuration

### Use PostgreSQL

1. Install: `pip install psycopg2`
2. Create database: `createdb ctf_db`
3. Set `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost/ctf_db
   ```

### Enable More Logging

Edit `src/config.py`:
```python
DEBUG = True
TESTING = False
```

### Change Rate Limiting

Edit `src/config.py`:
```python
MAX_ATTEMPTS_PER_MINUTE = 10  # Default is 5
```

### Add New Challenge

Edit `src/main.py` - `init_sample_data()` function:
```python
new_challenge = Challenge(
    title='Challenge 6',
    description='...',
    # ... add details
)
```

## Next Steps

1. ✅ Run application
2. ✅ Create account
3. ✅ Solve Challenge 1 (Easy)
4. ✅ Attempt Challenge 2 (Medium)
5. ✅ Compete on Leaderboard
6. ✅ Check IMPLEMENTATION_GUIDE.md for advanced customization

## Support Files

- **IMPLEMENTATION_GUIDE.md** - Detailed technical documentation
- **README.md** - Full project information
- **requirements.txt** - All Python dependencies

---

**Ready?** Run `python src/main.py --debug` and visit http://127.0.0.1:5000!
