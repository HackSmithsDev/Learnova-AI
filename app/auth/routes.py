import logging
from flask import session, jsonify, request, current_app, redirect, url_for, render_template, flash
from flask_login import login_user, current_user
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from app.auth import auth
from app.extensions import db, limiter
from app.models import User, UserDetails
from app.services.email import (
    send_welcome_email, send_login_alert, 
    send_password_reset_code, send_password_reset_success_email
)
from app.utils import generate_auth_code #, run_async_email
from datetime import datetime, timezone
import os
import secrets
# import threading

logger = logging.getLogger(__name__)
@auth.route('/page/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    return render_template('auth.html')

# --- LOGIN ROUTE ---
@auth.route('/login', methods=['POST'])
@limiter.limit("5 per 5 minutes")
def submit_login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))

    identifier = request.form.get('identifier') # Can be email or username
    password = request.form.get('password')

    # Check by email or username
    user = User.query.filter((User.email == identifier) | (User.user_id == identifier)).first()
    
    if user and user.check_password(password):
        login_user(user)

        # app = current_app._get_current_object()
        # # Fire and forget in a separate thread
        # threading.Thread(target=run_async_email, args=(app, send_login_alert, user.email, user.user_id)).start()

        send_login_alert.submit(user.email, user.user_id)

        # Look for the 'next' page in the URL (from the email redirect)
        next_page = request.args.get('next') or request.form.get('next') # if send using formData
        
        # Security check: Ensure 'next' is a relative path, not a malicious external site
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('home.index')

        return jsonify({"status": "success", "redirect": next_page}), 200
    
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401



# --- SIGNUP ROUTE ---
@auth.route('/signup', methods=['POST'])
def signup():
    data = request.form
    user_id = data.get('userid')
    email = data.get('email')
    password = data.get('password')

    # Basic Validation
    # if User.query.filter((User.email == email) | (User.user_id == user_id)).first():
    #     return jsonify({"status": "error", "message": "Email or Username already taken"}), 409

    try:
        # 1. Create User (T1)
        new_user = User(
            user_id=user_id,
            email=email,
            is_profile_complete=True 
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush() # Sync with DB to allow Foreign Key linkage

        # 2. Handle Profile Photo Upload
        photo_filename = 'default-avatar.png'
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                # Ensure unique filename to prevent overwriting
                ext = file.filename.rsplit('.', 1)[1].lower()
                photo_filename = f"user_{user_id}_profile.{secure_filename(ext)}"
                upload_path = current_app.config['PROFILE_IMAGE_FOLDER']
                file.save(os.path.join(upload_path, photo_filename))

        # 3. Create Profile (T2) 
        # Added course_id and branch to match your new table structure
        new_profile = UserDetails(
            user_id=new_user.user_id,
            name=data.get('name'),           # From Step 2
            age=data.get('age'),             # From Step 2
            gender=data.get('gender'),       # From Step 2
            photo=photo_filename,            # Saved filename
            # academic_level=data.get('level'),
            academic_context=data.get('context'),
            branch=data.get('branch'),      # UNCOMMENT if you added branch to UserDetails
            grade_level=data.get('grade'),
            course_id=data.get('course_id'), # CRITICAL: The ID we fetched in Step 3
            selected_subjects=request.form.getlist('subjects[]')
        )
        
        db.session.add(new_profile)
        db.session.commit()

        login_user(new_user)

        # app = current_app._get_current_object()
        # threading.Thread(target=run_async_email, args=(app, send_welcome_email, new_user.email, new_user.user_id)).start()

        send_welcome_email.submit(new_user.email, new_user.user_id)

        # Look for the 'next' page in the URL (from the email redirect)
        next_page = request.args.get('next') or request.form.get('next')
        
        # Security check: Ensure 'next' is a relative path, not a malicious external site
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('home.index')

        return jsonify({"status": "success", "redirect": next_page}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    identifier = request.form.get('identifier')

    # 1. Single efficient fetch
    user = User.query.filter((User.email == identifier) | (User.user_id == identifier)).first()

    # Security check: If no user, return 404 immediately
    if not user:
        return jsonify({"message": "User not found"}), 404

    if current_app.redis is None:
        return jsonify({"message": "Server configuration error"}), 503
    
    code = generate_auth_code()
    redis_key = f'reset:{user.email}'

    try:
        current_app.redis.setex(redis_key, 600, code)
        # app = current_app._get_current_object()    
        # # Start email thread
        # threading.Thread(
        #     target=run_async_email, 
        #     args=(app, send_password_reset_code, user.email, user.user_id, code)
        # ).start()

        send_password_reset_code.submit(user.email, user.user_id, code)

        return jsonify({"status": "success", "message": "Code sent to email"}), 200
    except Exception as e:
        current_app.logger.error(f"Redis/Email error: {e}")
        return jsonify({"message": "Service unavailable"}), 500


@auth.route('/verify_code', methods=['POST'])
@limiter.limit("10 per hour")
def verify_code():
    identifier = request.form.get('identifier')
    user = User.query.filter((User.email == identifier) | (User.user_id == identifier)).first()

    # Safety: Don't reveal if user exists or not to prevent user enumeration
    if not user:
        return jsonify({"status": "error", "message": "Invalid request."}), 400

    attempts_key = f"attempts:{user.email}"
    
    # 1. Use Redis INCR directly (it returns the new value)
    # We do this before checking so the current attempt is counted
    current_attempts = current_app.redis.get(attempts_key) or 0
    
    if int(current_attempts) >= 5:
        return jsonify({"status": "error", "message": "Account locked for 15 minutes."}), 429

    code_submitted = request.form.get('code')
    stored_code = current_app.redis.get(f'reset:{user.email}')

    # 2. Check the code
    if stored_code and secrets.compare_digest(stored_code, code_submitted):
        session['reset_verified_email'] = user.email
        session['reset_timestamp'] = datetime.now(timezone.utc).timestamp()
        current_app.redis.delete(attempts_key) 
        return jsonify({"status": "success", "redirect": url_for('auth.reset_password')}), 200
    
    # 3. Increment and set expiry on failure
    new_count = current_app.redis.incr(attempts_key)
    if new_count == 1:
        current_app.redis.expire(attempts_key, 900) # Start 15 min timer on first fail
    
    remaining = 5 - new_count
    return jsonify({
        "status": "error", 
        "message": f"Invalid code. {max(0, remaining)} attempts left."
    }), 400


# --- RESET PASSWORD ---
@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_verified_email')
    start_time = session.get('reset_timestamp')

    # 1. Unified Session Check
    if not email or not start_time:
        # Better check: Does the client expect JSON?
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "error", "message": "Session expired. Please restart the process."}), 403
        return redirect(url_for('auth.login'))
    
    # 2. Precise Time Check
    current_time = datetime.now(timezone.utc).timestamp()
    if current_time - start_time > 600:
        session.pop('reset_verified_email', None)
        session.pop('reset_timestamp', None)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "error", "message": "The 10-minute window has expired."}), 403
        flash("Your reset window (10 mins) has expired.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            return jsonify({"status": "error", "message": "Passwords do not match!"}), 400

        # 3. The "User Existence" Guard
        user = User.query.filter_by(email=email).first()
        if not user:
            session.clear() # Clear everything if the user doesn't exist anymore
            return jsonify({"status": "error", "message": "Account error. Please contact support."}), 404

        user.set_password(new_password)
        db.session.commit()

        # 4. Immediate Cleanup
        session.pop('reset_verified_email', None)
        session.pop('reset_timestamp', None)

        send_password_reset_success_email.submit(user.email, user.user_id)

        return jsonify({"status": "success", "message": "Password updated"}), 200

    return render_template('auth.html', mode='reset')