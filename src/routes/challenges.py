from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Challenge
from challenge_catalog import get_resources_by_order

challenges_bp = Blueprint('challenges', __name__)

@challenges_bp.route('/challenges')
def list_challenges():
    """Display all challenges"""
    challenges = Challenge.query.order_by(Challenge.order_position).all()
    if current_user.is_authenticated:
        for challenge in challenges:
            challenge.user_progress = challenge.get_user_progress(current_user.id)
    return render_template('challenges.html', challenges=challenges)

@challenges_bp.route('/challenge/<int:challenge_id>')
@challenges_bp.route('/challenges/<int:challenge_id>')
def view_challenge(challenge_id):
    """Display single challenge"""
    challenge = Challenge.query.get_or_404(challenge_id)
    progress = {}
    
    if current_user.is_authenticated:
        progress = challenge.get_user_progress(current_user.id)
    
    resources = get_resources_by_order().get(challenge.order_position, [])
    return render_template('challenge.html', challenge=challenge, progress=progress, resources=resources)

@challenges_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with progress"""
    challenges = Challenge.query.order_by(Challenge.order_position).all()
    progress_data = {
        challenge.id: challenge.get_user_progress(current_user.id)
        for challenge in challenges
    }
    return render_template('dashboard.html', challenges=challenges, progress=progress_data)

@challenges_bp.route('/leaderboard')
def leaderboard():
    """Global leaderboard"""
    return render_template('leaderboard.html')
