import uuid
import boto3
from datetime import datetime, timezone, timedelta

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

citizens_table = dynamodb.Table('citizens')
claims_table = dynamodb.Table('claims')

STORES = ['store_001', 'store_002']


def clear_tables():
    # Clear citizens
    response = citizens_table.scan()
    for item in response['Items']:
        citizens_table.delete_item(Key={'user_id': item['user_id']})

    # Clear claims
    response = claims_table.scan()
    for item in response['Items']:
        claims_table.delete_item(Key={'claim_id': item['claim_id']})

    print("Tables cleared.")


def seed():
    clear_tables()

    users = [
        # name, phone, dependents, card_status, give_past_claim
        ("Ali Raza",       "03001111111", 0, "active",   False),  # single adult, no claim yet
        ("Sara Malik",     "03002222222", 2, "active",   False),  # small family, no claim yet
        ("Usman Tariq",    "03003333333", 4, "active",   False),  # large family, no claim yet
        ("Nadia Hussain",  "03004444444", 1, "active",   True),   # claimed 2hrs ago, cooldown active
        ("Bilal Ahmed",    "03005555555", 3, "active",   True),   # claimed 25hrs ago, eligible again
        ("Zara Khan",      "03006666666", 0, "inactive", False),  # deactivated card
        ("Hamid Sheikh",   "03007777777", 2, "active",   False),  # will demo reactivation flow
    ]

    seeded = []

    for name, phone, dependents, status, past_claim in users:
        user_id = str(uuid.uuid4())

        citizens_table.put_item(Item={
            'user_id': user_id,
            'name': name,
            'phone_number': phone,
            'dependents_under_18': dependents,
            'card_status': status,
            'registered_at': datetime.now(timezone.utc).isoformat()
        })

        if past_claim:
            # Nadia — claimed 2 hours ago (cooldown still active)
            # Bilal — claimed 25 hours ago (eligible again)
            hours_ago = 2 if name == "Nadia Hussain" else 25
            claim_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            claims_table.put_item(Item={
                'claim_id': str(uuid.uuid4()),
                'user_id': user_id,
                'store_id': STORES[0],
                'timestamp': claim_time.isoformat(),
                'units_given': 3
            })

        seeded.append((name, user_id, phone, dependents, status))
        print(f"Seeded: {name} | dependents: {dependents} | status: {status}")

    print("\n--- User IDs for demo ---")
    for name, user_id, phone, dependents, status in seeded:
        print(f"{name}: {user_id}")

    return seeded


if __name__ == '__main__':
    seed()