## Part 2: Create a size-tracking lamda rule
import boto3
import time

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    bucket_name = 'test-bucket-jinhu'
    table_name = 'S3-object-size-history'
    table = dynamodb.Table(table_name)

    # List objects in the S3 bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    total_size = 0
    object_count = 0

    if 'Contents' in response:
        object_count = len(response['Contents'])
        total_size = sum(obj['Size'] for obj in response['Contents'])

    # Store the result in DynamoDB
    timestamp = str(time.time())
    table.put_item(
        Item={
            'bucket_name': bucket_name,
            'timestamp': timestamp,
            'size': total_size,
            'object_count': object_count
        }
    )

    return {
        'statusCode': 200,
        'body': f"Updated size info for bucket {bucket_name}."
    }

## Part 3: Plotting Lambda
import boto3
import matplotlib.pyplot as plt
import io
import time
import datetime
import matplotlib.dates as mdates

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Constants
BUCKET_NAME = 'test-bucket-jinhu'
TABLE_NAME = 'S3-object-size-history'

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Get the current time and calculate the time 10 seconds ago as strings
    now = str(time.time())  # Current timestamp as string with decimal
    ten_seconds_ago = str(float(now) - 10)  # Subtract 10 seconds, convert to string

    # Query DynamoDB for items in the last 10 seconds (stored as strings)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bucket_name').eq(BUCKET_NAME) &
                               boto3.dynamodb.conditions.Key('timestamp').between(ten_seconds_ago, now)
    )

    # Extract the relevant data for plotting
    items = response['Items']
    
    # Convert string timestamps back to float and convert them to datetime objects for better plotting
    timestamps = [datetime.datetime.fromtimestamp(float(item['timestamp'])) for item in items]
    sizes = [int(item['size']) for item in items]

    # Query the maximum bucket size from the whole table
    response_max = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bucket_name').eq(BUCKET_NAME),
        ProjectionExpression='size',
        Limit=1,  # Get only one item (maximum size)
        ScanIndexForward=False  # Sort descending to get the largest size
    )
    
    # Check if max size exists
    if response_max['Items']:
        max_size = int(response_max['Items'][0]['size'])
    else:
        max_size = 0  # Default to 0 if no data

    # Plotting using matplotlib
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, sizes, label='Bucket Size (last 10s)', marker='o')

    # Formatting the x-axis for better readability
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))  # Formatting as HH:MM:SS
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator())  # Tick every second

    plt.axhline(y=max_size, color='r', linestyle='--', label=f'Max Size: {max_size} bytes')

    plt.title('Bucket Size Changes (Last 10 Seconds)')
    plt.xlabel('Time')
    plt.ylabel('Size (Bytes)')
    plt.legend()

    # Auto-rotate the x-axis labels for better readability
    plt.gcf().autofmt_xdate()

    # Save the plot to a buffer and upload to S3
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Upload the plot to S3
    plot_key = 'bucket_size_plot.png'
    s3_client.put_object(Bucket=BUCKET_NAME, Key=plot_key, Body=buf, ContentType='image/png')

    return {
        'statusCode': 200,
        'body': f"Plot successfully generated and uploaded to S3 as {plot_key}."
    }

## Part 4: Driver Lambda
import boto3
import time
import urllib3

# Initialize S3 and Lambda clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')
bucket_name = 'test-bucket-jinhu'

def empty_bucket(bucket_name):
    """
    Function to empty the given S3 bucket by deleting all objects.
    """
    try:
        # List all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            # Collect the object keys to delete
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            # Perform the bulk delete
            delete_response = s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            print(f"Deleted objects: {delete_response}")

        else:
            print(f"No objects to delete in {bucket_name}")

    except Exception as e:
        print(f"Error occurred while emptying bucket {bucket_name}: {str(e)}")
        raise e

def lambda_handler(event, context):
    empty_bucket(bucket_name)
    # 1. Create object 'assignment1.txt' with content "Empty Assignment 1"
    time.sleep(1)
    s3_client.put_object(Bucket=bucket_name, Key='assignment1.txt', Body='Empty Assignment 1')
    print("Created assignment1.txt with content 'Empty Assignment 1' (size: 19 bytes)")

    # Wait for 1 second so that data points won't be too close
    time.sleep(1)

    # 2. Update object 'assignment1.txt' with content "Empty Assignment 2222222222"
    s3_client.put_object(Bucket=bucket_name, Key='assignment1.txt', Body='Empty Assignment 2222222222')
    print("Updated assignment1.txt with content 'Empty Assignment 2222222222' (size: 28 bytes)")

    # Wait for 1 second
    time.sleep(1)

    # 3. Delete object 'assignment1.txt'
    s3_client.delete_object(Bucket=bucket_name, Key='assignment1.txt')
    print("Deleted assignment1.txt (size: 0 bytes)")

    # Wait for 1 second
    time.sleep(1)

    # 4. Create object 'assignment2.txt' with content "33"
    s3_client.put_object(Bucket=bucket_name, Key='assignment2.txt', Body='33')
    print("Created assignment2.txt with content '33' (size: 2 bytes)")

    # 5. Invoke the plotting lambda function to generate the plot
    api_url = "https://oocne6a5o8.execute-api.us-west-1.amazonaws.com/stage1/driver"
    http = urllib3.PoolManager()
    response = http.request('GET', api_url)
    
    # # Return the result of invoking the plotting lambda
    # return {
    #     'statusCode': 200,
    #     'body': f'Driver Lambda executed successfully. Plotting Lambda invoked via API: {response.status}'
    # }

    try:
        response = http.request('GET', api_url)
        print(f"API call response status: {response.status}")
        print(f"API call response data: {response.data.decode('utf-8')}")
    
        # Return the result of invoking the plotting lambda
        return {
            'statusCode': 200,
            'body': f'Driver Lambda executed successfully. Plotting Lambda invoked via API: {response.status}'
        }
    except Exception as e:
        print(f"Error occurred while calling plotting lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error invoking plotting lambda: {str(e)}'
        }