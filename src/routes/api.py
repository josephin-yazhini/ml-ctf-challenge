from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Challenge, Flag, Submission, Score, User
import os
from challenge_catalog import get_resources_by_order

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Rate limiting tracker (in production, use Redis)
submission_tracker = {}

def check_rate_limit(user_id, max_attempts=5, time_window=60):
    """Check if user has exceeded submission rate limit"""
    current_time = datetime.utcnow()
    
    if user_id not in submission_tracker:
        submission_tracker[user_id] = []
    
    # Remove old attempts outside the time window
    submission_tracker[user_id] = [
        attempt_time for attempt_time in submission_tracker[user_id]
        if (current_time - attempt_time).total_seconds() < time_window
    ]
    
    if len(submission_tracker[user_id]) >= max_attempts:
        return False
    
    return True

def record_attempt(user_id):
    """Record a flag submission attempt"""
    if user_id not in submission_tracker:
        submission_tracker[user_id] = []
    submission_tracker[user_id].append(datetime.utcnow())


def _submit_flag_internal(challenge_id, submitted_flag, flag_order=None):
    """Shared submission flow for generic and per-flag endpoints."""
    # Validate input
    if not challenge_id or not submitted_flag:
        return jsonify({
            'success': False,
            'message': 'Challenge ID and flag are required'
        }), 400

    # Check rate limiting
    if not check_rate_limit(current_user.id, max_attempts=5, time_window=60):
        return jsonify({
            'success': False,
            'message': 'Too many attempts. Please wait before trying again.'
        }), 429

    record_attempt(current_user.id)

    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return jsonify({
            'success': False,
            'message': 'Challenge not found'
        }), 404

    if flag_order is not None:
        if flag_order != 1:
            return jsonify({
                'success': False,
                'message': 'Only final flag order 1 is valid for this challenge'
            }), 400
        if challenge.get_flags_count() != 1:
            return jsonify({
                'success': False,
                'message': 'This challenge does not have exactly 1 final flag configured'
            }), 400
        matching_flag = Flag.query.filter_by(
            challenge_id=challenge.id,
            flag_order=flag_order
        ).first()
        if not matching_flag:
            return jsonify({
                'success': False,
                'message': f'Flag {flag_order} not found for this challenge'
            }), 404
        is_correct = matching_flag.validate_flag(submitted_flag)
    else:
        matching_flag = None
        is_correct = False
        for flag in challenge.flags:
            if flag.validate_flag(submitted_flag):
                matching_flag = flag
                is_correct = True
                break

    if not is_correct:
        submission = Submission(
            user_id=current_user.id,
            challenge_id=challenge_id,
            flag_id=matching_flag.id if matching_flag else None,
            submitted_flag=submitted_flag,
            is_correct=False
        )
        db.session.add(submission)
        db.session.commit()
        progress = challenge.get_user_progress(current_user.id)
        return jsonify({
            'success': False,
            'message': 'Flag is incorrect. Try again!',
            'challenge_progress': progress
        }), 200

    existing_score = Score.query.filter_by(
        user_id=current_user.id,
        flag_id=matching_flag.id
    ).first()
    if existing_score:
        progress = challenge.get_user_progress(current_user.id)
        return jsonify({
            'success': False,
            'message': 'You have already submitted this flag.',
            'points': 0,
            'challenge_progress': progress
        }), 200

    points = matching_flag.points_value
    submission = Submission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        flag_id=matching_flag.id,
        submitted_flag=submitted_flag,
        is_correct=True,
        points_awarded=0
    )

    score = Score(
        user_id=current_user.id,
        challenge_id=challenge_id,
        flag_id=matching_flag.id,
        points=points,
        is_approved=False
    )

    db.session.add(submission)
    db.session.add(score)
    db.session.commit()

    progress = challenge.get_user_progress(current_user.id)
    return jsonify({
        'success': True,
        'message': f'Final flag submitted and pending admin approval.',
        'pending_points': points,
        'challenge_progress': progress
    }), 200


@api_bp.route('/submit-flag', methods=['POST'])
@login_required
def submit_flag():
    """
    Submit a flag for validation
    
    Request JSON:
    {
        "challenge_id": 1,
        "flag": "flag{...}"
    }
    
    Response:
    {
        "success": true/false,
        "message": "Flag is correct!|Flag is incorrect|Already completed",
        "points": 25,
        "challenge_progress": {
            "completed_flags": 2,
            "total_flags": 4,
            "points_earned": 50,
            "total_possible": 100
        }
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        challenge_id = data.get('challenge_id')
        submitted_flag = (data.get('flag') or '').strip()
        return _submit_flag_internal(challenge_id, submitted_flag)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@api_bp.route('/challenges/<int:challenge_id>/flags/<int:flag_order>/submit', methods=['POST'])
@login_required
def submit_flag_by_order(challenge_id, flag_order):
    """Submit a specific flag number (1-4) for a challenge."""
    try:
        data = request.get_json(silent=True) or {}
        submitted_flag = (data.get('flag') or '').strip()
        return _submit_flag_internal(challenge_id, submitted_flag, flag_order=flag_order)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@api_bp.route('/challenges', methods=['GET'])
def get_challenges():
    """Get all challenges"""
    try:
        challenges = Challenge.query.order_by(Challenge.order_position).all()
        resources_by_order = get_resources_by_order()
        
        challenges_data = []
        for challenge in challenges:
            challenge_dict = {
                'id': challenge.id,
                'title': challenge.title,
                'description': challenge.description,
                'category': challenge.category,
                'difficulty': challenge.difficulty,
                'total_points': challenge.total_points,
                'source_file_path': challenge.source_file_path,
                'flags_count': challenge.get_flags_count(),
                'resources': resources_by_order.get(challenge.order_position, [])
            }
            
            if current_user.is_authenticated:
                progress = challenge.get_user_progress(current_user.id)
                challenge_dict['user_progress'] = progress
            
            challenges_data.append(challenge_dict)
        
        return jsonify({
            'success': True,
            'challenges': challenges_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/challenges/<int:challenge_id>', methods=['GET'])
def get_challenge(challenge_id):
    """Get single challenge details"""
    try:
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'success': False, 'message': 'Challenge not found'}), 404
        
        challenge_data = {
            'id': challenge.id,
            'title': challenge.title,
            'description': challenge.description,
            'category': challenge.category,
            'difficulty': challenge.difficulty,
            'total_points': challenge.total_points,
            'source_file_path': challenge.source_file_path,
            'flags_count': challenge.get_flags_count(),
            'created_at': challenge.created_at.isoformat(),
            'resources': get_resources_by_order().get(challenge.order_position, [])
        }
        
        if current_user.is_authenticated:
            progress = challenge.get_user_progress(current_user.id)
            challenge_data['user_progress'] = progress
        
        return jsonify({
            'success': True,
            'challenge': challenge_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/challenges/<int:challenge_id>/status', methods=['GET'])
@login_required
def get_challenge_status(challenge_id):
    """Get user's progress on a specific challenge"""
    try:
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'success': False, 'message': 'Challenge not found'}), 404
        
        progress = challenge.get_user_progress(current_user.id)
        
        return jsonify({
            'success': True,
            'progress': progress
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get global leaderboard"""
    try:
        admin_user = User.query.filter_by(is_admin=True).first()
        is_leaderboard_public = bool(admin_user and admin_user.is_leaderboard_public)
        is_admin_viewer = bool(current_user.is_authenticated and current_user.is_admin)

        # Private mode: only admin can view
        if not is_leaderboard_public and not is_admin_viewer:
            return jsonify({
                'success': False,
                'message': 'Leaderboard is private'
            }), 403
        
        users = User.query.order_by(User.total_points.desc()).limit(100).all()
        
        leaderboard = []
        for rank, user in enumerate(users, 1):
            leaderboard.append({
                'rank': rank,
                'username': user.username,
                'total_points': user.total_points,
                'challenges_completed': len(user.get_completed_challenges()),
                'joined_at': user.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/user/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get user statistics (public profile)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        completed_challenges = user.get_completed_challenges()
        
        # Get challenge details for completed challenges
        completed_details = []
        for challenge_tuple in completed_challenges:
            challenge = Challenge.query.get(challenge_tuple[0])
            if challenge:
                progress = challenge.get_user_progress(user.id)
                completed_details.append({
                    'challenge_id': challenge.id,
                    'title': challenge.title,
                    'progress': progress
                })
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'total_points': user.total_points,
                'challenges_completed': len(completed_challenges),
                'joined_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'completed_challenges': completed_details
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/challenges/<int:challenge_id>/download', methods=['GET'])
def download_challenge_file(challenge_id):
    """Download challenge source file"""
    try:
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'success': False, 'message': 'Challenge not found'}), 404
        
        resources = get_resources_by_order().get(challenge.order_position, [])
        if not resources:
            return jsonify({'success': False, 'message': 'No file available for download'}), 404
        return download_challenge_resource(challenge_id, resources[0]['local_name'])
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/challenges/<int:challenge_id>/download/<path:filename>', methods=['GET'])
def download_challenge_resource(challenge_id, filename):
    """Download a specific allowed resource for a challenge."""
    try:
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({'success': False, 'message': 'Challenge not found'}), 404

        allowed_resources = {
            item['local_name']: item['display_name']
            for item in get_resources_by_order().get(challenge.order_position, [])
        }
        safe_name = os.path.basename(filename)
        if safe_name not in allowed_resources:
            return jsonify({'success': False, 'message': 'Resource not allowed for this challenge'}), 404

        file_path = os.path.join(current_app.static_folder, 'challenge_files', safe_name)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=allowed_resources[safe_name]
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
