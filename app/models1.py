from datetime import datetime, timedelta
import boto3
import uuid
from boto3.dynamodb.conditions import Key, Attr
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

class DynamoDBManager:
    def __init__(self):
        self.user_table_name = 'Users'
        self.challenge_table_name = 'Challenges'
        self.score_table_name = 'Scores'

    def create_tables(self):
        # Get list of existing tables
        existing_tables = [table.name for table in dynamodb.tables.all()]

        # Create Users table if it doesn't exist
        if self.user_table_name not in existing_tables:
            try:
                dynamodb.create_table(
                    TableName=self.user_table_name,
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
        else:
            print("Users table already exists.")

        # Create Challenges table if it doesn't exist
        if self.challenge_table_name not in existing_tables:
            try:
                dynamodb.create_table(
                    TableName=self.challenge_table_name,
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
        else:
            print("Challenges table already exists.")

        # Create Scores table if it doesn't exist
        if self.score_table_name not in existing_tables:
            try:
                dynamodb.create_table(
                    TableName=self.score_table_name,
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
        else:
            print("Scores table already exists.")

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
# Challenge Model
class Challenge:
    def __init__(self, name, description, solution):
        self.challenge_id = str(uuid.uuid4())  # Use 'challenge_id' as the primary key
        self.name = name
        self.description = description
        self.solution = solution
        self.table = dynamodb.Table('Challenges')

    @staticmethod
    def get_all():
        table = dynamodb.Table('Challenges')
        try:
            response = table.scan()
            challenges = response.get('Items', [])
            logger.info(f"Retrieved {len(challenges)} challenges from DynamoDB")
            return challenges
        except Exception as e:
            logger.error(f"Error retrieving challenges: {str(e)}")
            return []

    @staticmethod
    def get_by_id(challenge_id):
        table = dynamodb.Table('Challenges')
        try:
            response = table.get_item(Key={'challenge_id': challenge_id})
            challenge = response.get('Item')
            logger.info(f"Retrieved challenge with ID {challenge_id}: {challenge is not None}")
            return challenge
        except Exception as e:
            logger.error(f"Error retrieving challenge {challenge_id}: {str(e)}")
            return None

    def save(self):
        try:
            item = {
                'challenge_id': self.challenge_id,  # Use 'challenge_id' as key
                'name': self.name,
                'description': self.description,
                'solution': self.solution,
                'created_at': datetime.utcnow().isoformat()
            }
            self.table.put_item(Item=item)
            logger.info(f"Successfully saved challenge '{self.name}' with ID {self.challenge_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving challenge '{self.name}': {str(e)}")
            return False

def debug_challenges():
    """Utility function to check the state of challenges in the database"""
    try:
        challenges = Challenge.get_all()
        logger.info("=== Current Challenges in Database ===")
        for challenge in challenges:
            logger.info(f"ID: {challenge.get('id')}")
            logger.info(f"Name: {challenge.get('name')}")
            logger.info(f"Description: {challenge.get('description')}")
            logger.info("---")
        return len(challenges)
    except Exception as e:
        logger.error(f"Error in debug_challenges: {str(e)}")
        return 0
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
