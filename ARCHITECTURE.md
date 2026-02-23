# ML CTF Platform - Complete Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│  (HTML, CSS, JavaScript)                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/AJAX
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Web Server (Port 5000)                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Request Routing Layer                      │   │
│  │  - URL mapping to route handlers                   │   │
│  │  - Session/Authentication middleware               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│          ┌───────────────┼───────────────┬─────────────┐   │
│          ▼               ▼               ▼             ▼   │
│      ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐ │
│      │ Auth   │    │ API    │    │ Chall. │    │ Pages  │ │
│      │ Routes │    │ Routes │    │ Routes │    │ Render │ │
│      └───┬────┘    └───┬────┘    └───┬────┘    └───┬────┘ │
│          │             │             │             │       │
│      [Login]      [Submit Flag] [View Chall]  [Templates] │
│      [Register]   [Leaderboard] [Progress]        │       │
│      [Profile]    [Stats]       [Download]        │       │
│      [Password]   [Challenges]  [Dashboard]       │       │
│                                                         │       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        Business Logic Layer (Models)               │   │
│  │  - User authentication & authorization             │   │
│  │  - Flag validation & scoring                       │   │
│  │  - Leaderboard calculations                        │   │
│  │  - Rate limiting & security checks                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     SQLAlchemy ORM Layer                           │   │
│  │  - Database abstraction                            │   │
│  │  - Model relationships                             │   │
│  │  - Query optimization                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQL Queries
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database (SQLite3)                       │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Users     │  │ Challenges  │  │   Flags     │         │
│  │─────────────│  │─────────────│  │─────────────│         │
│  │ id          │  │ id          │  │ id          │         │
│  │ username ───┼──┼─ N:M        │  │ challenge_id├─────┐   │
│  │ email      │  │ title       │  │ flag_order  │     │   │
│  │ password   │  │ description │  │ flag_context│     │   │
│  │ total_pts  │  │ difficulty  │  │ points_val  │     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│       △                                                  │   │
│       │                                                  │   │
│  ┌────┴──────────────┐                ┌────────────────┘   │
│  │  Submissions      │                │                   │
│  │───────────────────│                │                   │
│  │ id                │                │                   │
│  │ user_id ──────────┼────────────┐   │                   │
│  │ challenge_id      │            │   │                   │
│  │ flag_id ──────────┼────────────┼───┼┐                  │
│  │ submitted_flag    │            │   ││                  │
│  │ is_correct        │            │   ││                  │
│  │ submitted_at      │            │   ││                  │
│  └───────────────────┘            │   ││                  │
│                                    │   ││                  │
│  ┌──────────────────────┐          │   ││                  │
│  │  Scores             │          │   ││                  │
│  │──────────────────────│          │   ││                  │
│  │ id                  │          │   ││                  │
│  │ user_id ────────────┼──────────┤   ││                  │
│  │ flag_id ────────────┼──────────┼───┤│                  │
│  │ points              │              ││                  │
│  │ awarded_at          │              ││                  │
│  └──────────────────────┘              ││                  │
│   (Unique: user_id, flag_id) ─────────┘│                  │
│                                         │                  │
│  ┌───────────────────────────────────────┘                 │
│  │ Relationships:                                          │
│  │ • Users have many Submissions                          │
│  │ • Users have many Scores                               │
│  │ • Challenges have many Flags                           │
│  │ • Challenges have many Submissions                     │
│  │ • Flags have many Submissions & Scores                │
│  └────────────────────────────────────────────────────────│
└─────────────────────────────────────────────────────────────┘
```

## Data Flow - Flag Submission

```
User Submits Flag
        │
        ▼
┌─────────────────────┐
│ Frontend JavaScript │ ← Validates input
└──────────┬──────────┘
           │ AJAX POST /api/submit-flag
           ▼
┌──────────────────────────┐
│ Flask API Handler        │
│ (submit_flag route)      │
└──────────┬───────────────┘
           │
           ├─→ Rate Limit Check
           │    ├─→ Too fast? Return 429
           │    └─→ OK? Continue
           │
           ├─→ Get Challenge from DB
           │    └─→ Not found? Return 404
           │
           ├─→ Find Matching Flag
           │    ├─→ Not found? Log submission
           │    │            Return "Incorrect"
           │    └─→ Found? Continue
           │
           ├─→ Check for Duplicate Score
           │    ├─→ Already earned? Return "Complete"
           │    └─→ New? Continue
           │
           ├─→ Award Points
           │    ├─→ Create Submission record
           │    ├─→ Create Score record
           │    ├─→ Update User.total_points
           │    └─→ Commit to database
           │
           ▼
    Return Success Response
    ├─→ Points earned
    ├─→ Challenge progress
    └─→ Success message
           │
           ▼
    Update Frontend
    ├─→ Show success message
    ├─→ Update progress bar
    ├─→ Increment points display
    └─→ Refresh leaderboard
```

## User Authentication Flow

```
User Registration/Login
        │
        ▼
┌───────────────────────────┐
│ Fill Form (HTML)          │
│ - Username                │
│ - Email (if registering)  │
│ - Password                │
└──────────┬────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Client-Side Validation (JS)     │
│ - Check fields not empty        │
│ - Email format validation       │
│ - Password strength (register)  │
└──────────┬──────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ AJAX POST (JSON)                     │
│ /auth/register or /auth/login        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Server-Side Validation               │
│ - Input format check                 │
│ - SQL injection prevention (ORM)     │
│ - Email validation                   │
│ - Password strength check (register) │
└──────────┬───────────────────────────┘
           │
    ┌──────┴──────┬─────────┐
    │             │         │
    ▼             ▼         ▼
 Register      Login    Error
    │             │        │
    ├─→ Hash      ├─→ Query └──→ Return 400/409
    │   password  │   user  
    ├─→ Check     ├─→ Check
    │   duplicates│   password
    ├─→ Create    ├─→ Update
    │   user      │   last_login
    └─→ Commit    └─→ Create
                       session
                 │
                 ▼
          Return success
          + user data
          + Set cookie
                 │
                 ▼
          Frontend redirect
          to /challenges
```

## Challenge Difficulty Progression

```
Easy (Challenge 1)           Medium (Challenges 2,5)
├─ PII Detection             ├─ SQL Injection
├─ Basic patterns            ├─ Query analysis
├─ Straightforward hints      ├─ Multiple vectors
└─ 100 points                └─ 100 points

Hard (Challenge 3)           Expert (Challenge 4)
├─ ML Evasion                ├─ Cryptography
├─ Adversarial examples      ├─ Advanced attacks
├─ Model behavior            ├─ Complex systems
└─ 100 points                └─ 100 points
```

## Points System Flowchart

```
Start Challenge (0 points for this challenge)
        │
        ├─→ Submit Flag 1 ─→ Correct? ─→ +25 pts (Total: 25/100)
        │                        │
        │                    Incorrect → No points
        │
        ├─→ Submit Flag 2 ─→ Correct? ─→ +25 pts (Total: 50/100)
        │                        │
        │                    Incorrect → No points
        │
        ├─→ Submit Flag 3 ─→ Correct? ─→ +25 pts (Total: 75/100)
        │                        │
        │                    Incorrect → No points
        │
        └─→ Submit Flag 4 ─→ Correct? ─→ +25 pts (Total: 100/100)
                                │      ┌─→ Challenge Complete!
                            Incorrect → No points
```

## Leaderboard Update Process

```
User Submits Flag
        │
        ▼
Score Awarded
        │
        ▼
User.total_points Updated
        │
        ▼
Updated to Database
        │
        ├─→ Next refresh: 30 seconds
        │   (client JS polls periodically)
        │
        ▼
Leaderboard API called
/api/leaderboard
        │
        ▼
Query: Users sorted by total_points DESC, limit 100
        │
        ▼
Return JSON with rankings
        │
        ▼
Frontend updates table
with smooth animation
```

## File Structure & Relationships

```
Frontend Layer
├─ base.html (master template)
│  ├─ Navigation (Flask url_for routing)
│  ├─ Flash messages
│  └─ Footer
├─ index.html (homepage)
├─ challenge.html (single challenge)
│  └─ JavaScript for flag submission
├─ challenges.html (list)
├─ leaderboard.html
│  └─ Auto-refresh JS
├─ dashboard.html
├─ login.html & register.html
└─ Styling
   ├─ styles.css (global)
   └─ script.js (utilities)
          │
          ▼
Backend Routes
├─ auth.py (authentication)
│  ├─ /auth/register
│  ├─ /auth/login
│  └─ /auth/logout
├─ api.py (state changes & data)
│  ├─ /api/submit-flag (POST)
│  ├─ /api/challenges (GET)
│  ├─ /api/leaderboard (GET)
│  └─ /api/user/<id>/stats (GET)
└─ challenges.py (page rendering)
   ├─ /challenges
   ├─ /challenge/<id>
   ├─ /dashboard
   └─ /leaderboard
          │
          ▼
Data Layer (SQLAlchemy ORM)
├─ models.py
│  ├─ User class
│  ├─ Challenge class  
│  ├─ Flag class
│  ├─ Submission class
│  └─ Score class
└─ Relationships defined
          │
          ▼
Database (SQLite)
├─ users table
├─ challenges table
├─ flags table
├─ submissions table
└─ scores table
```

## Security Architecture

```
Request Comes In
       │
       ▼
┌─────────────────────────────┐
│ Web Server (Flask)          │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ CORS Check                  │
│ (Flask-CORS middleware)     │
└──────────┬──────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Session/Authentication Check        │
│ (Flask-Login, cookies)              │
│ ├─→ Public endpoints OK              │
│ └─→ Protected endpoints require auth │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Input Validation                     │
│ ├─→ Data type checking               │
│ ├─→ Length validation                │
│ └─→ Format validation                │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Rate Limiting Check                 │
│ ├─→ 5 flag attempts/minute/user      │
│ └─→ Prevents brute force             │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Database Query (Parameterized)      │
│ ├─→ SQLAlchemy ORM prevents SQLi     │
│ └─→ No string concatenation          │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Response Generation                  │
│ ├─→ Data validation before sending   │
│ └─→ Secure headers set               │
└──────────┬──────────────────────────┘
           │
           ▼
Response Sent to Client
(With proper status codes & error messages)
```

## Scalability Considerations

### Current (SQLite)
- Good for: Development, learning, single-server deployment
- Limit: ~1000 concurrent users

### Scale to PostgreSQL
```python
# Change in config.py:
DATABASE_URL = 'postgresql://user:pass@host/db'
# Then: pip install psycopg2
```

### Production Improvements
1. **Database**: Use PostgreSQL with connection pooling
2. **Caching**: Add Redis for leaderboard
3. **Load Balancer**: Run multiple app instances behind Nginx
4. **Monitoring**: Add logging and error tracking
5. **CDN**: Serve static files from CDN

## Environment Flow

```
   Development         →        Production
   (debug=True)                (debug=False)
         │                           │
         ├─→ SQLite                  ├─→ PostgreSQL
         ├─→ Hot reload              ├─→ Gunicorn
         ├─→ Verbose logging         ├─→ Nginx proxy
         ├─→ Local testing           ├─→ HTTPS/SSL
         └─→ 127.0.0.1:5000         └─→ domain.com
```

---

This architecture ensures:
✅ Security at every layer
✅ Clean separation of concerns
✅ Scalability for growth
✅ Maintainability and clarity
✅ Performance optimization
✅ User experience quality

For more details, see IMPLEMENTATION_GUIDE.md
