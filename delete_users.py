import boto3

dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4566', region_name='us-east-1', aws_access_key_id='test', aws_secret_access_key='test')
table = dynamodb.Table('citizens')
response = table.scan()

for item in response['Items']:
    print(item['name'], '|', item['phone_number'], '|', item['user_id'])
    if item['phone_number'] == '+923338170618':
        table.delete_item(Key={'user_id': item['user_id']})
        print(f"Deleted: {item['name']}")

print("Done")