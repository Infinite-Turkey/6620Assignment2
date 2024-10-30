import boto3
import time
from botocore.exceptions import ClientError

# Initialize S3 and DynamoDB client server
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')

# S3 bucket name
bucket_name = 'test-bucket-jinhu'

# DynamoDB table name
table_name = 'S3-object-size-history'


## Part 1: Create a S3 bucket and a DynamoDB table
# Create S3 bucket
def create_s3_bucket():
    try:
        s3_client.create_bucket(Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'us-west-1'})
        print(f"S3 bucket '{bucket_name}' created.")
    except Exception as e:
        print(f"Error creating bucket: {e}")


create_s3_bucket()

# Create DynamoDB table
def create_dynamodb_table():
    try:
        response = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'bucket_name',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'bucket_name',
                    'AttributeType': 'S'  # String
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'  # Number (for epoch timestamp)
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"DynamoDB table '{table_name}' created successfully.")
    except ClientError as e:
        print(f"Error creating DynamoDB table: {e}")
        return None
    return response

create_dynamodb_table()