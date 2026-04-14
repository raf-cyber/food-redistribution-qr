import uuid
import boto3
import qrcode
import io
from datetime import datetime, timezone

# AWS clients pointed at LocalStack
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    config=boto3.session.Config(s3={'addressing_style': 'path'})
)

citizens_table = dynamodb.Table('citizens')
BUCKET = 'qr-images'
HOST = 'https://motherly-existential-loreta.ngrok-free.dev'


def register_user(name, phone_number, dependents_under_18):
    # Check if phone number already registered
    response = citizens_table.scan(
        FilterExpression='phone_number = :p',
        ExpressionAttributeValues={':p': phone_number}
    )
    if response['Items']:
        print(f"Phone number {phone_number} already registered.")
        return None

    # Generate unique user ID
    user_id = str(uuid.uuid4())

    # Write to DynamoDB
    citizens_table.put_item(Item={
        'user_id': user_id,
        'name': name,
        'phone_number': phone_number,
        'dependents_under_18': int(dependents_under_18),
        'card_status': 'active',
        'registered_at': datetime.now(timezone.utc).isoformat()
    })

    # Generate QR code
    qr_url = f"{HOST}/scan?user_id={user_id}"
    qr = qrcode.make(qr_url)

    # Upload QR to S3
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    s3_key = f"{user_id}.png"
    s3.put_object(Bucket=BUCKET, Key=s3_key, Body=buffer, ContentType='image/png')

    print(f"Registered: {name}")
    print(f"User ID: {user_id}")
    print(f"QR URL: {qr_url}")
    print(f"QR saved to S3: s3://{BUCKET}/{s3_key}")
    return user_id


if __name__ == '__main__':
    register_user("Ahmed Khan", "03001234567", 2)
    register_user("Fatima Bibi", "03019876543", 0)
    register_user("Usman Ali", "03331122334", 4)