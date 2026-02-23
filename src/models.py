from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and tracking"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    total_points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)  # Admin can approve scores and manage leaderboard
    is_leaderboard_public = db.Column(db.Boolean, default=False)  # Admin toggle to show leaderboard to all
    
    # Relationships
    submissions = db.relationship('Submission', backref='user', lazy=True, cascade='all, delete-orphan')
    scores = db.relationship('Score', foreign_keys='Score.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    approved_scores = db.relationship('Score', foreign_keys='Score.approved_by', backref='approved_by_user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def get_total_points(self):
        """Calculate total points from approved scores only"""
        return db.session.query(db.func.sum(Score.points)).filter(
            Score.user_id == self.id,
            Score.is_approved == True
        ).scalar() or 0
    
    def get_completed_challenges(self):
        """Get list of completed challenge IDs"""
        return db.session.query(db.distinct(Submission.challenge_id)).filter(
            Submission.user_id == self.id,
            Submission.is_correct == True
        ).all()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Challenge(db.Model):
    """Challenge model"""
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))  # Easy, Medium, Hard, Expert
    total_points = db.Column(db.Integer, default=100)
    source_file_path = db.Column(db.String(255))
    order_position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    flags = db.relationship('Flag', backref='challenge', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='challenge', lazy=True, cascade='all, delete-orphan')
    scores = db.relationship('Score', backref='challenge', lazy=True, cascade='all, delete-orphan')
    
    def get_flags_count(self):
        """Get number of flags in this challenge"""
        return len(self.flags)
    
    def get_user_progress(self, user_id):
        """Get user's progress on this challenge"""
        approved_flags = db.session.query(db.func.count(db.distinct(Score.flag_id))).filter(
            Score.user_id == user_id,
            Score.challenge_id == self.id,
            Score.is_approved == True
        ).scalar() or 0

        pending_flags = db.session.query(db.func.count(db.distinct(Score.flag_id))).filter(
            Score.user_id == user_id,
            Score.challenge_id == self.id,
            Score.is_approved == False
        ).scalar() or 0

        total_points = db.session.query(db.func.sum(Score.points)).filter(
            Score.user_id == user_id,
            Score.challenge_id == self.id,
            Score.is_approved == True
        ).scalar() or 0
        
        return {
            'completed_flags': approved_flags,
            'pending_flags': pending_flags,
            'total_flags': len(self.flags),
            'points_earned': total_points,
            'total_possible': self.total_points
        }
    
    def __repr__(self):
        return f'<Challenge {self.title}>'


class Flag(db.Model):
    """Flag model - each challenge can have multiple flags"""
    __tablename__ = 'flags'
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    flag_content = db.Column(db.String(255), nullable=False)
    flag_order = db.Column(db.Integer)  # Order of flags within challenge
    points_value = db.Column(db.Integer, default=25)
    description = db.Column(db.Text)  # Optional: hint for users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='flag', lazy=True)
    
    def validate_flag(self, submitted_flag):
        """
        Validate submitted flag using exact match or regex
        Returns: (is_valid, None)
        """
        # Exact match (case-insensitive)
        if self.flag_content.lower() == submitted_flag.lower():
            return True
        
        # Regex match (if flag starts with regex pattern marker)
        if self.flag_content.startswith('REGEX:'):
            pattern = self.flag_content.replace('REGEX:', '')
            try:
                if re.match(pattern, submitted_flag):
                    return True
            except re.error:
                pass
        
        return False
    
    def __repr__(self):
        return f'<Flag challenge_id={self.challenge_id} order={self.flag_order}>'


class Submission(db.Model):
    """Flag submission tracking"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    flag_id = db.Column(db.Integer, db.ForeignKey('flags.id'))
    submitted_flag = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_awarded = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Submission user_id={self.user_id} challenge_id={self.challenge_id} correct={self.is_correct}>'


class Score(db.Model):
    """Points tracking per user per challenge - requires admin approval"""
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    flag_id = db.Column(db.Integer, db.ForeignKey('flags.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval required
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who approved
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    leaderboard_visible = db.Column(db.Boolean, default=False)  # Only show on leaderboard if approved
    
    # Prevent duplicate scores
    __table_args__ = (db.UniqueConstraint('user_id', 'flag_id', name='user_flag_unique'),)
    
    def __repr__(self):
        return f'<Score user_id={self.user_id} flag_id={self.flag_id} points={self.points} approved={self.is_approved}>'
