from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from app.models import User, Challenge, Score
from app import db
from datetime import datetime

main = Blueprint('main', __name__)

# Route for the homepage
@main.route('/')
def index():
    if 'user_id' in session:
        challenges = Challenge.query.all()
        return render_template('index.html', challenges=challenges, message="Welcome to AWS CLI Learning Platform!")
    return redirect(url_for('main.signup'))

# Route for the sign-up page
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            return render_template('signup.html', message="❌ Username already exists.")

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        return redirect(url_for('main.index'))

    return render_template('signup.html')

# Route for the login page
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('main.index'))
        return render_template('login.html', message="❌ Invalid username or password.")

    return render_template('login.html')

# Route for logging out
@main.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))

# Route for validating a challenge command
@main.route('/validate', methods=['POST'])
def validate_command():
    if 'user_id' not in session:
        return jsonify({"message": "❌ You must be logged in to validate commands."}), 401

    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        data = request.get_json()
        command = data.get('command', '').strip()
        challenge_id = int(data.get('challenge_id', 0))

        current_challenge = Challenge.query.get(challenge_id)

        if current_challenge:
            if command.lower() == current_challenge.solution.strip().lower():
                score = Score(
                    user_id=user_id,
                    challenge_id=current_challenge.id,
                    score=10,
                    completed_at=datetime.now()
                )
                db.session.add(score)
                db.session.commit()

                total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0

                return jsonify({
                    "message": f"✅ Correct! Challenge '{current_challenge.name}' completed!",
                    "username": user.username,
                    "total_score": total_score
                })

            return jsonify({"message": "❌ Incorrect command. Please try again."})

        return jsonify({"message": "❌ Challenge not found."})
    except Exception as e:
        return jsonify({"message": f"❌ An error occurred: {str(e)}"}), 500

# Route for fetching user info
@main.route('/user_info')
def user_info():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=user_id).scalar() or 0

        return jsonify({
            "username": user.username,
            "total_score": total_score
        })
    return jsonify({"message": "User not logged in"}), 401

# Route for the leaderboard
@main.route('/leaderboard')
def leaderboard():
    scores = User.query.join(Score)\
        .with_entities(User.username, db.func.sum(Score.score).label('total_score'))\
        .group_by(User.id).order_by(db.func.sum(Score.score).desc()).all()

    return render_template('leaderboard.html', scores=scores, enumerate=enumerate)
