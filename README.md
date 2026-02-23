# ML CTF Challenge Platform

A comprehensive **Machine Learning & Security Capture The Flag (CTF)** challenge platform built with Flask. Test your skills in security, cryptography, data analysis, and machine learning through 5 real-world challenges.

## Features

✅ **5 Progressive Challenges** - Each with 4 flags at increasing difficulty  
✅ **User Authentication** - Secure registration and login system  
✅ **Points & Scoring System** - Earn points only after valid flag submission  
✅ **Global Leaderboard** - Real-time competition tracking  
✅ **User Dashboard** - Track personal progress and statistics  
✅ **File Downloads** - Download challenge source files and datasets  
✅ **Responsive Design** - Works on all devices  

## Challenges

1. **Find Hidden PII** (Easy) - Data privacy, pattern analysis
2. **SQL Injection** (Medium) - Web security, database exploitation
3. **ML Model Evasion** (Hard) - Adversarial examples, ML security
4. **Cryptography** (Expert) - Cryptanalysis, encryption breaking
5. **Fraud Detection** (Medium) - Anomaly detection, pattern recognition

Each challenge has **4 flags** worth 25 points each (100 points total).

## Quick Start

### Installation

```bash
# Clone repository
cd ml-ctf-challenge

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/main.py --init-db

# Run application
python src/main.py --debug
```

Visit `http://127.0.0.1:5000`

### Configuration

Create `.env` file if needed:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///ctf_challenge.db
```

## Project Structure

```
ml-ctf-challenge/
├── src/
│   ├── main.py                 # Flask app
│   ├── config.py               # Configuration
│   ├── models.py               # Database models
│   ├── routes/
│   │   ├── auth.py            # Authentication
│   │   ├── api.py             # API endpoints
│   │   └── challenges.py       # Challenge routes
│   ├── templates/              # HTML templates
│   └── static/                 # CSS, JS, files
├── requirements.txt
├── IMPLEMENTATION_GUIDE.md     # Detailed guide
└── README.md
```

## User Guide

### Registration & Login
1. Click "Register" on homepage
2. Create account with strong password
3. Login with credentials
4. Start solving challenges

### Solving Challenges
1. Navigate to "Challenges"
2. Select a challenge
3. Read description and download files
4. Submit flags as you find them
5. Earn points for correct flags

### Tracking Progress
- **Dashboard**: View personal stats
- **Leaderboard**: See global rankings
- **Challenge Page**: Track individual progress

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/submit-flag` | POST | Submit flag for validation |
| `/api/challenges` | GET | List all challenges |
| `/api/challenges/<id>` | GET | Get challenge details |
| `/api/leaderboard` | GET | Get global rankings |
| `/api/user/<id>/stats` | GET | Get user statistics |
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | User login |
| `/auth/logout` | POST | User logout |

## Flag Submission Example

```bash
curl -X POST http://localhost:5000/api/submit-flag \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": 1,
    "flag": "flag{found_ssn}"
  }'
```

## Database Models

- **User** - Stores user accounts and statistics
- **Challenge** - Challenge metadata and descriptions
- **Flag** - Individual flags per challenge
- **Submission** - Track all flag attempts
- **Score** - Points awarded for correct flags

## Customization

### Add New Challenge

Edit `src/main.py`:
```python
def init_sample_data():
    # Add new challenge
    challenge = Challenge(
        title='New Challenge',
        description='...',
        category='Category',
        difficulty='Medium',
        total_points=100,
        source_file_path='file.csv'
    )
    # Add flags...
```

### Change Scoring

Edit `src/routes/api.py` in `submit_flag()`:
```python
points = flag.points_value  # Customize here
```

## Security Features

✅ Password hashing with bcrypt  
✅ SQL injection prevention (ORM)  
✅ Rate limiting (5 attempts/min)  
✅ Secure session management  
✅ Input validation  
✅ CSRF protection ready  

## Deployment

### Production with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:create_app()
```

### Docker

```bash
docker build -t ml-ctf .
docker run -p 5000:5000 ml-ctf
```

### Environment Variables

```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
DEBUG=False
```

## Troubleshooting

**Database Issue:**
```bash
rm src/ctf_challenge.db
python src/main.py --init-db
```

**Module Not Found:**
```bash
pip install -r requirements.txt
```

**Port Already in Use:**
```bash
python src/main.py --port 5001
```

## Performance Tips

- Use PostgreSQL for production
- Enable database connection pooling
- Use CDN for static files
- Implement caching for leaderboard
- Enable gzip compression on server

## References

- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- CTFd: https://github.com/CTFd/CTFd
- ML Challenge: https://github.com/RaghunandhanG/Yugam_ML_Challenge-3

## License

MIT License

## Support

Issues or questions? Check IMPLEMENTATION_GUIDE.md for detailed documentation.

---

**Version**: 1.0.0 | **Status**: Production Ready | **Last Updated**: Feb 2026