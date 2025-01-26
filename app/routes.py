from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
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
        data = request.get_json()
        command = data.get('command', '').strip()
        challenge_id = int(data.get('challenge_id', 0))

        print(f"Validating command for User ID: {user_id}, Challenge ID: {challenge_id}, Command: {command}")

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

                return jsonify({"message": f"✅ Correct! Challenge '{current_challenge.name}' completed!"})
            
            message = (
                "❌ Incorrect command for challenge: 'Launch an EC2 instance'\n"
                "Please refer to the AWS documentation here:\n"
                "📖 AWS CLI Guide: https://docs.aws.amazon.com/cli/v1/userguide/cli-services-ec2-instances.html\n"
                "Additionally, you can watch this video for a demo:\n"
                "🎥 YouTube - Stephen Maarek: https://www.youtube.com/watch?v=crNyDkR3ulU"
            )
            return jsonify({"message": message})

        print(f"Challenge with ID {challenge_id} not found.")
        return jsonify({"message": "❌ Challenge not found."})
    except Exception as e:
        print(f"Error processing validation: {e}")
        return jsonify({"message": f"❌ An error occurred: {str(e)}"}), 500

# Route to display the leaderboard
@main.route('/leaderboard')
def leaderboard():
    scores = User.query.join(Score)\
        .with_entities(User.username, db.func.sum(Score.score).label('total_score'))\
        .group_by(User.id).order_by(db.func.sum(Score.score).desc()).all()

    result = [{"username": username, "total_score": total_score} for username, total_score in scores]
    return jsonify(result)
