# Food Redistribution QR System — MVP

Built to distribute surplus bakery food to low-income families in Lahore —
fairly, autonomously, and without abuse.

---

## Setup

### 1. Start Docker Desktop

Open Docker Desktop and wait for it to fully load, then run:

```bash
docker compose up -d
```

### 2. Provision Infrastructure

```bash
terraform init
terraform apply -auto-approve
```

### 3. Activate virtual environment

```bash
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 4. Seed demo data

```bash
py seed_data.py              # Windows
python seed_data.py          # Mac/Linux
```

### 5. Start the Flask server

```bash
py app.py                    # Windows
python app.py                # Mac/Linux
```

### 6. Start ngrok (new terminal, venv active)

```bash
ngrok http 5000
```

Copy the ngrok URL (e.g. `https://xxxx.ngrok-free.app`) and set it in `.env`:

```
HOST=https://xxxx.ngrok-free.app
```

### 7. Connect Twilio WhatsApp Sandbox

- Go to twilio.com → Messaging → Try it out → Send a WhatsApp message
- Send `join <your-keyword>` from your phone to **+14155238886**
- Set your ngrok webhook URL in Twilio console:
  ```
  https://xxxx.ngrok-free.app/whatsapp
  ```

---

## WhatsApp Registration Flow

Message **+14155238886** on WhatsApp to register a family:

1. Send any message to start
2. Enter your full name
3. Enter number of dependents under 18
4. Receive your personal QR code link

---

## Demo Walkthrough

Open `http://localhost:5000` in browser.

Run `py seed_data.py` first and note the printed user IDs.

| Scenario               | Who           | Expected                    |
| ---------------------- | ------------- | --------------------------- |
| Fresh scan             | Ali Raza      | ✅ Approved                 |
| Scan again immediately | Ali Raza      | ❌ Cooldown                 |
| Cooldown still active  | Nadia Hussain | ❌ Come back in ~22hrs      |
| Eligible again         | Bilal Ahmed   | ✅ Approved                 |
| Deactivated card       | Zara Khan     | ❌ Card inactive            |
| Reactivate + new QR    | Hamid Sheikh  | ✅ New QR works, old denied |

Scan URL format:

```
https://your-ngrok-url/scan?user_id=<user_id>
```

> **Note:** First visit via ngrok shows a one-time browser warning (free tier).
> Click "Visit Site" to proceed — it only appears once per device.

---

## API Endpoints

| Method | Endpoint           | Purpose                              |
| ------ | ------------------ | ------------------------------------ |
| GET    | `/scan?user_id=`   | Validate and approve/deny collection |
| POST   | `/register`        | Register new recipient               |
| POST   | `/deactivate`      | Deactivate a card                    |
| POST   | `/reactivate`      | Reissue card with new QR             |
| GET    | `/status?user_id=` | Check quota and claim status         |
| POST   | `/whatsapp`        | Twilio WhatsApp webhook              |

---

## Daily Units Formula

```
daily_units = max(3, 3 + (dependents_under_18 × 1.5))
```

| Dependents | Units |
| ---------- | ----- |
| 0          | 3     |
| 2          | 6     |
| 4          | 9     |

---

## Infrastructure

- LocalStack (DynamoDB + S3) via Docker
- Terraform for provisioning
- Flask backend
- Twilio WhatsApp Sandbox for registration
- ngrok for public URL tunneling
- No real AWS account needed for local dev

---

## Current Status

This is a working prototype — not a production system.

**Built and working:**

- User registration via WhatsApp bot (Twilio sandbox)
- QR code generation and delivery via WhatsApp
- QR scan flow with full screen approved/denied result
- 24-hour cooldown and per-family quota logic
- Card deactivation and reactivation with new QR
- Seed data for demo scenarios
- LocalStack infrastructure via Terraform

**Not built yet:**

- Real WhatsApp API via Meta Cloud API (currently Twilio sandbox)
- Production deployment on AWS
- NGO admin dashboard
- Mechanized chute hardware integration

---

## Roadmap

- [x] WhatsApp bot via Twilio
- [ ] Deploy to AWS (DynamoDB + S3 + EC2)
- [ ] NGO admin dashboard
- [ ] Pilot with one bakery in Lahore
