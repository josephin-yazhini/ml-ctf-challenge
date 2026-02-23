from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Challenge, Flag, Score, Submission, User, db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect('/')


def _latest_correct_submission(score):
    return (
        Submission.query.filter_by(
            user_id=score.user_id,
            challenge_id=score.challenge_id,
            flag_id=score.flag_id,
            is_correct=True,
        )
        .order_by(Submission.submitted_at.desc())
        .first()
    )


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    pending_scores = (
        Score.query.filter_by(is_approved=False)
        .order_by(Score.awarded_at.desc())
        .all()
    )
    pending_rows = []
    for score in pending_scores:
        latest = _latest_correct_submission(score)
        pending_rows.append(
            {
                'score': score,
                'latest_flag_value': latest.submitted_flag if latest else '',
                'submitted_at': latest.submitted_at if latest else score.awarded_at,
            }
        )

    users = User.query.order_by(User.created_at.desc()).all()
    challenges = Challenge.query.order_by(Challenge.order_position).all()
    total_approved = Score.query.filter_by(is_approved=True).count()

    return render_template(
        'admin_dashboard.html',
        pending_rows=pending_rows,
        users=users,
        challenges=challenges,
        total_approved_scores=total_approved,
        is_leaderboard_public=current_user.is_leaderboard_public,
    )


@admin_bp.route('/approve-score/<int:score_id>', methods=['POST'])
@login_required
def approve_score(score_id):
    score = Score.query.get(score_id)
    if score:
        score.is_approved = True
        score.approved_by = current_user.id
        score.approved_at = datetime.utcnow()
        score.leaderboard_visible = True
        user = User.query.get(score.user_id)
        user.total_points = user.get_total_points()
        db.session.commit()
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reject-score/<int:score_id>', methods=['POST'])
@login_required
def reject_score(score_id):
    score = Score.query.get(score_id)
    if score:
        db.session.delete(score)
        db.session.commit()
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/toggle-leaderboard', methods=['POST'])
@login_required
def toggle_leaderboard():
    current_user.is_leaderboard_public = not current_user.is_leaderboard_public
    db.session.commit()
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def toggle_user_admin(user_id):
    user = User.query.get(user_id)
    if user and user.id != current_user.id:
        user.is_admin = not user.is_admin
        db.session.commit()
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user and user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/challenges/<int:challenge_id>/update', methods=['POST'])
@login_required
def update_challenge(challenge_id):
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return redirect(url_for('admin.dashboard'))

    title = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip()
    difficulty = request.form.get('difficulty', '').strip()
    description = request.form.get('description', '').strip()
    total_points = request.form.get('total_points', '').strip()
    flag_content = request.form.get('flag_content', '').strip()

    try:
        total_points_int = max(1, int(total_points))
    except Exception:
        total_points_int = challenge.total_points

    if title:
        challenge.title = title
    if category:
        challenge.category = category
    if difficulty:
        challenge.difficulty = difficulty
    if description:
        challenge.description = description
    challenge.total_points = total_points_int

    # Each challenge must have exactly one final flag.
    final_flag = Flag.query.filter_by(challenge_id=challenge.id, flag_order=1).first()
    if final_flag is None:
        final_flag = Flag(
            challenge_id=challenge.id,
            flag_order=1,
            flag_content=flag_content or f'flag{{challenge_{challenge.id}_final}}',
            points_value=total_points_int,
            description='Final verification flag',
        )
        db.session.add(final_flag)
    else:
        if flag_content:
            final_flag.flag_content = flag_content
        final_flag.points_value = total_points_int
        final_flag.description = 'Final verification flag'

    extra_flags = Flag.query.filter(
        Flag.challenge_id == challenge.id,
        Flag.flag_order != 1,
    ).all()
    for flag in extra_flags:
        db.session.delete(flag)

    db.session.commit()
    return redirect(url_for('admin.dashboard'))
