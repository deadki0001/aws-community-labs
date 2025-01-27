from datetime import datetime, timedelta
import boto3
import uuid
from boto3.dynamodb.conditions import Key, Attr

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# DynamoDB Manager Class
class DynamoDBManager:
    def __init__(self):
        self.user_table = dynamodb.Table('Users')
        self.challenge_table = dynamodb.Table('Challenges')
        self.score_table = dynamodb.Table('Scores')

    def create_tables(self):
        # Create Users table
        try:
            dynamodb.create_table(
                TableName='Users',
                KeySchema=[
                    {'AttributeName': 'username', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'username', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Users table created.")
        except Exception as e:
            print(f"Error creating Users table: {e}")

        # Create Challenges table
        try:
            dynamodb.create_table(
                TableName='Challenges',
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Challenges table created.")
        except Exception as e:
            print(f"Error creating Challenges table: {e}")

        # Create Scores table
        try:
            dynamodb.create_table(
                TableName='Scores',
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'UserScores',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("Scores table created.")
        except Exception as e:
            print(f"Error creating Scores table: {e}")

# User Model
class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.created_at = datetime.utcnow().isoformat()
        self.reset_token = None
        self.reset_token_expiration = None

    @staticmethod
    def get_by_username(username):
        try:
            response = dynamodb.Table('Users').get_item(Key={'username': username})
            return response.get('Item')
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None

    def save(self):
        try:
            dynamodb.Table('Users').put_item(
                Item={
                    'username': self.username,
                    'email': self.email,
                    'password': self.password,
                    'created_at': self.created_at,
                    'reset_token': self.reset_token,
                    'reset_token_expiration': self.reset_token_expiration
                }
            )
            print(f"User {self.username} saved successfully.")
        except Exception as e:
            print(f"Error saving user: {e}")

# Challenge Model
class Challenge:
    def __init__(self, name, description, solution):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.solution = solution

    @staticmethod
    def get_all():
        try:
            response = dynamodb.Table('Challenges').scan()
            return response.get('Items', [])
        except Exception as e:
            print(f"Error retrieving challenges: {e}")
            return []

    def save(self):
        try:
            dynamodb.Table('Challenges').put_item(
                Item={
                    'id': self.id,
                    'name': self.name,
                    'description': self.description,
                    'solution': self.solution
                }
            )
            print(f"Challenge {self.name} saved successfully.")
        except Exception as e:
            print(f"Error saving challenge: {e}")

# Score Model
class Score:
    def __init__(self, user_id, challenge_id, score):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.score = score
        self.completed_at = datetime.utcnow().isoformat()

    def save(self):
        try:
            dynamodb.Table('Scores').put_item(
                Item={
                    'id': self.id,
                    'user_id': self.user_id,
                    'challenge_id': self.challenge_id,
                    'score': self.score,
                    'completed_at': self.completed_at
                }
            )
            print(f"Score for user {self.user_id} saved successfully.")
        except Exception as e:
            print(f"Error saving score: {e}")

# Initialize Challenges
def initialize_challenges():
    existing_challenges = {challenge['name'] for challenge in Challenge.get_all()}
    initial_challenges = [
        Challenge(name='Create a VPC', description='Use the AWS CLI to create a new VPC.', solution='aws ec2 create-vpc'),
        Challenge(name='Create an RDS Instance', description='Use the AWS CLI to create an RDS instance.', solution='aws rds create-db-instance'),
        Challenge(name='Create a Security Group', description='Use the AWS CLI to create a security group.', solution='aws ec2 create-security-group'),
        Challenge(name='Create an IAM User', description='Use the AWS CLI to create a new IAM user.', solution='aws iam create-user --user-name'),
        Challenge(name='Launch an EC2 instance', description='Use the AWS CLI to launch an EC2 instance.', solution='aws ec2 run-instances'),
        Challenge(name='Create an S3 Bucket', description='Use the AWS CLI to create an S3 bucket.', solution='aws s3 mb')
    ]

    for challenge in initial_challenges:
        if challenge.name not in existing_challenges:
            challenge.save()

# Main Script Execution
if __name__ == "__main__":
    manager = DynamoDBManager()
    manager.create_tables()
    initialize_challenges()
