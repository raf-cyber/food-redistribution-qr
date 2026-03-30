# Food Redistribution QR System — MVP

Built for AllahWale Trust Foundation (or similar NGOs) to distribute
surplus food fairly, autonomously, and without abuse.

---

## Setup

### 1. Start LocalStack

```bash
docker compose up -d
```

### 2. Provision Infrastructure

```bash
terraform init
terraform apply
```

### 3. Activate virtual environment

```bash
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 4. Seed demo data

```bash
python seed_data.py
```

### 5. Start the server

```bash
python app.py
```

---

## Demo Walkthrough

Open `http://localhost:5000` in browser — hand this to your pitch audience.

Run `python seed_data.py` first and note the printed user IDs.

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
http://localhost:5000/scan?user_id=<user_id>
```

---

## API Endpoints

| Method | Endpoint           | Purpose                              |
| ------ | ------------------ | ------------------------------------ |
| GET    | `/scan?user_id=`   | Validate and approve/deny collection |
| POST   | `/register`        | Register new recipient               |
| POST   | `/deactivate`      | Deactivate a card                    |
| POST   | `/reactivate`      | Reissue card with new QR             |
| GET    | `/status?user_id=` | Check quota and claim status         |

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
- No real AWS account needed

```

---
```

## Current Status

This is a working prototype — not a production system.

**Built and working:**

- User registration with QR generation
- QR scan flow with full screen approved/denied result
- 24 hour cooldown and per-family quota logic
- Card deactivation and reactivation
- Seed data for demo scenarios
- LocalStack infrastructure via Terraform

**Not built yet:**

- Real WhatsApp API integration (simulated via direct URL)
- Production deployment on AWS
- Admin dashboard for NGO staff
- Mechanized chute hardware integration

## Roadmap

- [done] WhatsApp bot via Twilio
- [ ] Deploy to AWS (DynamoDB + S3 + EC2)
- [ ] NGO admin dashboard
- [ ] Pilot with one bakery in Lahore
