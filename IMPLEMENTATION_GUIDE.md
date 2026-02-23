# ML CTF Challenge Website - Implementation Guide

## Overview
This guide provides a complete step-by-step implementation of an ML CTF (Capture The Flag) challenge website with 5 security/data challenges, flag validation, and point-based scoring system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         Frontend (HTML/CSS/JavaScript)              │
│  - Challenge Pages with Descriptions                │
│  - Download Source File Buttons                     │
│  - Flag Input Forms                                 │
│  - Scoreboard                                       │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│         Flask Backend (Python)                       │
│  - Challenge Management Routes                      │
│  - Flag Validation Endpoints                        │
│  - User Management & Sessions                       │
│  - Points Calculation & Leaderboard                 │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│         Database (SQLite/PostgreSQL)                │
│  - Users Table                                      │
│  - Challenges Table                                 │
│  - Flags Table (with answers)                       │
│  - User Submissions Table                           │
│  - Scores Table                                     │
└─────────────────────────────────────────────────────┘
```

## Database Schema

### 1. Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_points INTEGER DEFAULT 0
);
```

### 2. Challenges Table
```sql
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    difficulty VARCHAR(50),
    points INTEGER NOT NULL,
    source_file_path VARCHAR(255),
    order_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Flags Table
```sql
CREATE TABLE flags (
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER NOT NULL,
    flag_content VARCHAR(255) NOT NULL UNIQUE,
    flag_order INTEGER,
    points_value INTEGER DEFAULT 25,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id)
);
```

### 4. Submissions Table
```sql
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    flag_id INTEGER,
    submitted_flag VARCHAR(255) NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    points_awarded INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (challenge_id) REFERENCES challenges(id),
    FOREIGN KEY (flag_id) REFERENCES flags(id)
);
```

### 5. Scores Table
```sql
CREATE TABLE scores (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    points INTEGER NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (challenge_id) REFERENCES challenges(id),
    UNIQUE(user_id, challenge_id)
);
```

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Challenges
- `GET /api/challenges` - List all challenges
- `GET /api/challenges/<id>` - Get challenge details
- `GET /api/challenges/<id>/download` - Download source file

### Flag Validation
- `POST /api/submit-flag` - Submit flag for validation
  - Request: `{ "challenge_id": 1, "flag": "flag{...}" }`
  - Response: `{ "success": true/false, "message": "...", "points": 25 }`

- `GET /api/challenges/<id>/status` - Check user's progress on challenge
  - Response: `{ "completed_flags": 2, "total_flags": 4, "points_earned": 50, "total_possible": 100 }`

### Leaderboard
- `GET /api/leaderboard` - Get global leaderboard
- `GET /api/user/<id>/stats` - Get user statistics

## Implementation Steps

### Step 1: Set Up Flask Application Structure
```
ml-ctf-challenge/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── challenges.py
│   │   ├── auth.py
│   │   ├── api.py
│   │   └── admin.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── challenge.html
│   │   ├── leaderboard.html
│   │   ├── login.html
│   │   └── register.html
│   └── static/
│       ├── styles.css
│       ├── script.js
│       └── challenges/
│           ├── challenge1.csv
│           ├── challenge1_solution.py
│           └── ... (other challenge files)
├── requirements.txt
└── README.md
```

### Step 2: Core Models & Database
- Create SQLAlchemy models for Users, Challenges, Flags, Submissions
- Implement database initialization and migration

### Step 3: Authentication System
- User registration with email validation
- Secure password hashing (bcrypt)
- Session management with Flask-Login

### Step 4: Challenge Management
- Display challenges with description, difficulty, points
- File download functionality for challenge sources
- Track user progress per challenge

### Step 5: Flag Validation Logic
```python
def validate_flag(user_id, challenge_id, submitted_flag):
    """
    Validates submitted flag and awards points
    - Exact match validation or regex matching
    - Check if user already completed this flag
    - Award points only once per flag
    - Return validation status and points
    """
```

### Step 6: Scoring System
- Points awarded only after flag validation
- Prevent duplicate submissions for same flag
- Cumulative points per user
- Dynamic scoring (optional)

### Step 7: Leaderboard & Analytics
- Real-time leaderboard updates
- User progress tracking
- Challenge completion statistics

## Key Features

### 1. Multi-Flag Support Per Challenge
- Each challenge can have 4 flags (progressive difficulty)
- Each flag worth different points (25, 25, 25, 25 = 100 total)
- Users see progress: "2/4 flags completed"

### 2. Source File Download
- Each challenge includes downloadable dataset/source code
- Links properly managed in database
- Version control for challenge updates

### 3. Flag Submission System
- Input field with regex/exact match validation
- Real-time feedback (correct/incorrect)
- Prevent brute force attacks
- Rate limiting on submissions

### 4. Points & Ranking
- Instant point calculation upon flag validation
- Points only awarded once per user per flag
- Automatic leaderboard updates
- User profile with achievement stats

### 5. Admin Dashboard (Optional)
- Add/Edit/Delete challenges
- Manage challenge flags
- View submissions & analytics
- User management

## Security Considerations

1. **Password Security**: Use bcrypt/argon2 for hashing
2. **Flag Validation**: Sanitize input, use constant-time comparison
3. **Rate Limiting**: Prevent brute force attacks (e.g., 5 attempts/minute)
4. **Session Management**: Secure cookies, CSRF protection
5. **File Uploads/Downloads**: Validate file types, prevent directory traversal
6. **SQL Injection**: Use parameterized queries (SQLAlchemy ORM)
7. **HTTPS**: Run on HTTPS in production

## Challenge Data Example

### Challenge 1: Data Privacy Violation
- **Title**: "Find the Hidden PII in Dataset"
- **Description**: Analyze a dataset to find hidden personally identifiable information
- **Flags**: 
  1. `flag{found_ssn}` - 25 points
  2. `flag{found_credit_card}` - 25 points
  3. `flag{found_dob_pattern}` - 25 points
  4. `flag{prevention_recommendation}` - 25 points
- **Source File**: `challenge1_dataset.csv`

### Challenge 2: SQL Injection Attack
- **Title**: "Exploit the Vulnerable Database"
- **Description**: Use SQL injection to extract secret data
- **Flags**: 4 progressive difficulty levels
- **Source File**: `challenge2_vulnerable_code.py`

### Challenge 3: Machine Learning Model Evasion
- **Title**: "Bypass the ML Security System"
- **Description**: Craft adversarial examples to fool the model
- **Flags**: 4 different attack vectors
- **Source File**: `challenge3_model_and_data.pkl`

### Challenge 4: Cryptography Challenge
- **Title**: "Decrypt the Message"
- **Description**: Break the encryption using known plaintext attack
- **Flags**: 4 keys at different difficulty levels
- **Source File**: `challenge4_encrypted_data.txt`

### Challenge 5: Anomaly Detection
- **Title**: "Detect the Fraudulent Transaction"
- **Description**: Find anomalies in transaction data
- **Flags**: 4 different fraud patterns
- **Source File**: `challenge5_transactions.csv`

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/main.py --init-db

# Run development server
python src/main.py

# Or with Flask
flask --app src.main run --debug
```

## Testing Flag Validation

```bash
# Test API
curl -X POST http://localhost:5000/api/submit-flag \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": 1, "flag": "flag{found_ssn}"}'
```

## Advanced Features (Optional)

1. **Dynamic Scoring**: Reduce points based on number of incorrect attempts
2. **Team Mode**: Allow team-based competition
3. **Hints System**: Reveal hints after N attempts (costs points)
4. **Time-based Challenges**: Bonus points for completing within time limit
5. **Achievements/Badges**: Special badges for specific accomplishments
6. **Challenge Dependencies**: Unlock challenges after completing prerequisites
7. **Export Feature**: Allow users to export their progress

## Deployment

1. **Local Development**: Flask development server
2. **Production**: Use Gunicorn + Nginx + PostgreSQL
3. **Docker**: Containerize application for easy deployment
4. **Cloud**: Deploy to AWS, Azure, or Heroku

## References

- CTFd Framework: https://github.com/CTFd/CTFd
- ML Challenge Repo: https://github.com/RaghunandhanG/Yugam_ML_Challenge-3
- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy ORM: https://www.sqlalchemy.org/
