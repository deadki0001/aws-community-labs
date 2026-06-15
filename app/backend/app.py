from flask import Blueprint

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/')
def home():
    return "Welcome to the AWS CLI Learning Platform!"

