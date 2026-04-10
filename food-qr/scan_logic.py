import boto3
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

citizens_table = dynamodb.Table('citizens')
claims_table = dynamodb.Table('claims')


def calculate_daily_units(dependents_under_18):
    return max(3, int(3 + (dependents_under_18 * 1.5)))


def get_todays_claims(user_id):
    today = datetime.now(timezone.utc).date().isoformat()
    response = claims_table.scan(
        FilterExpression='user_id = :u AND begins_with(#ts, :d)',
        ExpressionAttributeValues={
            ':u': user_id,
            ':d': today
        },
        ExpressionAttributeNames={'#ts': 'timestamp'}
    )
    return response['Items']


def get_last_claim(user_id):
    response = claims_table.scan(
        FilterExpression='user_id = :u',
        ExpressionAttributeValues={':u': user_id}
    )
    items = response['Items']
    if not items:
        return None
    return max(items, key=lambda x: x['timestamp'])


def validate_scan(user_id, store_id='store_001'):
    # Fetch citizen
    response = citizens_table.get_item(Key={'user_id': user_id})
    citizen = response.get('Item')

    if not citizen:
        return {'approved': False, 'reason': 'User not found'}

    if citizen['card_status'] != 'active':
        return {'approved': False, 'reason': 'This card has been deactivated. Please contact the NGO to reactivate.'}

    # Check 24hr cooldown
    last_claim = get_last_claim(user_id)
    if last_claim:
        last_time = datetime.fromisoformat(last_claim['timestamp'].replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff_hours = (now - last_time).total_seconds() / 3600
        if diff_hours < 24:
            hours_left = round(24 - diff_hours, 1)
            return {'approved': False, 'reason': f'You already collected today. Please come back in {hours_left} hours.'}

    # Calculate quota
    dependents = int(citizen['dependents_under_18'])
    daily_units = calculate_daily_units(dependents)

    # Check how many units used today
    todays_claims = get_todays_claims(user_id)
    units_used = sum(int(c['units_given']) for c in todays_claims)
    units_remaining = daily_units - units_used

    if units_remaining <= 0:
        return {'approved': False, 'reason': 'You have collected your full allocation for today.'}

    # Approve — log the claim
    import uuid
    claim_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    claims_table.put_item(Item={
        'claim_id': claim_id,
        'user_id': user_id,
        'store_id': store_id,
        'timestamp': now.isoformat(),
        'units_given': units_remaining
    })

    return {
        'approved': True,
        'reason': 'Approved',
        'units_given': units_remaining,
        'units_remaining': 0,
        'name': citizen['name']
    }


# --- Tests ---
if __name__ == '__main__':
    import sys

    # Get user IDs from DynamoDB to test with
    response = citizens_table.scan()
    users = {item['name']: item['user_id'] for item in response['Items']}

    print("=== TEST 1: Valid first scan (Ahmed Khan) ===")
    result = validate_scan(users['Ahmed Khan'])
    print(result)

    print("\n=== TEST 2: Cooldown active (scan again immediately) ===")
    result = validate_scan(users['Ahmed Khan'])
    print(result)

    print("\n=== TEST 3: User not found ===")
    result = validate_scan('fake-user-id-000')
    print(result)

    print("\n=== TEST 4: Deactivated card ===")
    # Temporarily deactivate Fatima
    citizens_table.update_item(
        Key={'user_id': users['Fatima Bibi']},
        UpdateExpression='SET card_status = :s',
        ExpressionAttributeValues={':s': 'inactive'}
    )
    result = validate_scan(users['Fatima Bibi'])
    print(result)
    # Reactivate her
    citizens_table.update_item(
        Key={'user_id': users['Fatima Bibi']},
        UpdateExpression='SET card_status = :s',
        ExpressionAttributeValues={':s': 'active'}
    )

    print("\n=== TEST 5: Daily units formula ===")
    print(f"0 dependents = {calculate_daily_units(0)} units")
    print(f"2 dependents = {calculate_daily_units(2)} units")
    print(f"4 dependents = {calculate_daily_units(4)} units")