from flask import Flask, render_template, jsonify
from flask_login import LoginManager, current_user
from flask_cors import CORS
import os
import sys
from datetime import datetime
import requests
from sqlalchemy import text

# Import configuration
from config import config
from models import db, User, Challenge, Flag
from challenge_catalog import CATALOG, get_catalog_by_order

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Enable CORS
    CORS(app, supports_credentials=True)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.api import api_bp
    from routes.challenges import challenges_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(admin_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'message': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    
    # Home route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # Database initialization
    with app.app_context():
        db.create_all()
        migrate_sqlite_schema()
        sync_challenge_catalog()
        ensure_default_admin()
        ensure_challenge_files(app)
    
    return app


def init_sample_data():
    """Backward-compatible hook for initialization."""
    sync_challenge_catalog()
    print("Challenge catalog synchronized successfully!")


def init_db(app):
    """Initialize database"""
    with app.app_context():
        db.create_all()
        migrate_sqlite_schema()
        sync_challenge_catalog()
        print("Database initialized!")


def ensure_challenge_files(app):
    """Download challenge files into static/challenge_files if missing."""
    challenge_files_dir = os.path.join(app.static_folder, 'challenge_files')
    os.makedirs(challenge_files_dir, exist_ok=True)

    for challenge_cfg in CATALOG:
        for item in challenge_cfg['resources']:
            file_path = os.path.join(challenge_files_dir, item['local_name'])
            if os.path.exists(file_path):
                continue
            try:
                response = requests.get(item['url'], timeout=20)
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    f.write(response.content)
            except Exception:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('Challenge asset could not be downloaded automatically.\n')
                    f.write(f"Source: {item['url']}\n")


def sync_challenge_catalog():
    """Seed challenges/flags from catalog without overwriting admin edits."""
    by_order = get_catalog_by_order()
    existing = {c.order_position: c for c in Challenge.query.all()}

    for order, cfg in by_order.items():
        challenge = existing.get(order)
        primary_file = cfg['resources'][0]['local_name'] if cfg['resources'] else None
        if challenge is None:
            challenge = Challenge(order_position=order)
            db.session.add(challenge)
            challenge.title = cfg['title']
            challenge.description = cfg['description']
            challenge.category = cfg['category']
            challenge.difficulty = cfg['difficulty']
            challenge.total_points = cfg['total_points']
            challenge.source_file_path = primary_file
        elif not challenge.source_file_path:
            challenge.source_file_path = primary_file

        db.session.flush()
        existing_flags = {f.flag_order: f for f in challenge.flags}
        for flag_cfg in cfg['flags']:
            flag = existing_flags.get(flag_cfg['flag_order'])
            if flag is None:
                flag = Flag(challenge_id=challenge.id, flag_order=flag_cfg['flag_order'])
                db.session.add(flag)
                flag.flag_content = flag_cfg['flag_content']
                flag.points_value = flag_cfg['points_value']
                flag.description = flag_cfg['description']

        for flag_order, flag in list(existing_flags.items()):
            if flag_order not in {f['flag_order'] for f in cfg['flags']}:
                db.session.delete(flag)

        main_flag = Flag.query.filter_by(challenge_id=challenge.id, flag_order=1).first()
        if main_flag:
            main_flag.points_value = challenge.total_points
            if not main_flag.description:
                main_flag.description = 'Final verification flag'
    db.session.commit()


def ensure_default_admin():
    """Create a default admin account if no admin exists."""
    if User.query.filter_by(is_admin=True).first():
        return

    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@mlctf.local')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@12345')

    existing = User.query.filter(
        (User.username == admin_username) | (User.email == admin_email)
    ).first()
    if existing:
        existing.is_admin = True
        if not existing.password_hash:
            existing.set_password(admin_password)
        db.session.commit()
        return

    admin_user = User(
        username=admin_username,
        email=admin_email,
        is_admin=True
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.commit()


def migrate_sqlite_schema():
    """Best-effort SQLite migration for legacy local databases."""
    if not str(db.engine.url).startswith('sqlite'):
        return

    def _columns(table_name):
        rows = db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return {row[1] for row in rows}

    def _safe_add_column(table_name, column_name, ddl):
        cols = _columns(table_name)
        if column_name in cols:
            return
        try:
            db.session.execute(text(ddl))
        except Exception:
            db.session.rollback()

    _safe_add_column('scores', 'is_approved', "ALTER TABLE scores ADD COLUMN is_approved BOOLEAN DEFAULT 0")
    _safe_add_column('scores', 'approved_by', "ALTER TABLE scores ADD COLUMN approved_by INTEGER")
    _safe_add_column('scores', 'approved_at', "ALTER TABLE scores ADD COLUMN approved_at DATETIME")
    _safe_add_column('scores', 'leaderboard_visible', "ALTER TABLE scores ADD COLUMN leaderboard_visible BOOLEAN DEFAULT 0")
    _safe_add_column('users', 'is_admin', "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    _safe_add_column('users', 'is_leaderboard_public', "ALTER TABLE users ADD COLUMN is_leaderboard_public BOOLEAN DEFAULT 0")

    db.session.commit()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ML CTF Challenge')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    app = create_app(config_name='development' if args.debug else 'production')
    
    if args.init_db:
        init_db(app)
        sys.exit(0)
    
    app.run(host=args.host, port=args.port, debug=args.debug)
