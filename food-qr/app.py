import uuid
import boto3
import qrcode
import io
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from scan_logic import validate_scan, calculate_daily_units, get_todays_claims
from register import register_user
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

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
HOST = 'http://localhost:5000'


# --- / ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# --- /register ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    phone = data.get('phone_number')
    dependents = data.get('dependents_under_18', 0)

    if not name or not phone:
        return jsonify({'error': 'name and phone_number are required'}), 400

    user_id = register_user(name, phone, dependents)
    if not user_id:
        return jsonify({'error': 'Phone number already registered'}), 409

    return jsonify({'user_id': user_id, 'qr_url': f'{HOST}/scan?user_id={user_id}'}), 201


# --- /scan ---
@app.route('/scan', methods=['GET'])
def scan():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    result = validate_scan(user_id)

    if result['approved']:
        return render_template('scan_result.html',
            approved=True,
            bg_color='linear-gradient(135deg, #1a7a4a, #25a560)',
            title='Collection Approved',
            subtitle=f"Welcome, {result['name']}",
            info=f"You may collect <span>{result['units_given']}</span> packet(s) today.<br>Thank you for using this service."
        )
    else:
        return render_template('scan_result.html',
            approved=False,
            bg_color='linear-gradient(135deg, #a52020, #d93030)',
            title='Collection Denied',
            subtitle='Sorry, we could not approve this request.',
            info=f"{result['reason']}"
        )


# --- /deactivate ---
@app.route('/deactivate', methods=['POST'])
def deactivate():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    response = citizens_table.get_item(Key={'user_id': user_id})
    if not response.get('Item'):
        return jsonify({'error': 'User not found'}), 404

    citizens_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET card_status = :s',
        ExpressionAttributeValues={':s': 'inactive'}
    )
    return jsonify({'message': 'Card deactivated'}), 200


# --- /reactivate ---
@app.route('/reactivate', methods=['POST'])
def reactivate():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    response = citizens_table.get_item(Key={'user_id': user_id})
    citizen = response.get('Item')
    if not citizen:
        return jsonify({'error': 'User not found'}), 404

    # Generate new user_id — old QR is permanently invalidated
    new_user_id = str(uuid.uuid4())

    # Copy citizen record with new user_id
    citizens_table.put_item(Item={
        'user_id': new_user_id,
        'name': citizen['name'],
        'phone_number': citizen['phone_number'],
        'dependents_under_18': citizen['dependents_under_18'],
        'card_status': 'active',
        'registered_at': citizen['registered_at']
    })

    # Deactivate old record
    citizens_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression='SET card_status = :s',
        ExpressionAttributeValues={':s': 'inactive'}
    )

    # Generate new QR
    qr_url = f"{HOST}/scan?user_id={new_user_id}"
    qr = qrcode.make(qr_url)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    s3.put_object(Bucket=BUCKET, Key=f"{new_user_id}.png", Body=buffer, ContentType='image/png')

    return jsonify({
        'message': 'Card reactivated with new QR',
        'new_user_id': new_user_id,
        'qr_url': qr_url
    }), 200


# --- /status ---
@app.route('/status', methods=['GET'])
def status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    response = citizens_table.get_item(Key={'user_id': user_id})
    citizen = response.get('Item')
    if not citizen:
        return jsonify({'error': 'User not found'}), 404

    dependents = int(citizen['dependents_under_18'])
    daily_units = calculate_daily_units(dependents)
    todays_claims = get_todays_claims(user_id)
    units_used = sum(int(c['units_given']) for c in todays_claims)

    return jsonify({
        'name': citizen['name'],
        'card_status': citizen['card_status'],
        'daily_units': daily_units,
        'units_used': units_used,
        'units_remaining': max(0, daily_units - units_used),
        'last_claim': max([c['timestamp'] for c in todays_claims], default=None)
    }), 200


if __name__ == '__main__':
    app.run(debug=True)