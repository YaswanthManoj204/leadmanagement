# LeadFlow CRM - Enterprise Lead Management Web Application

A full-featured, responsive **Lead Management Web Application** designed for sales teams to capture, track, nurture, and close deals efficiently.

Built with **Django** (Backend) and **HTML5, CSS3, JavaScript, Bootstrap 5.3 & Chart.js** (Frontend).

---

## 🌟 Key Features Mapped to Requirements

### 1. Lead Capture
- **Social Media Paid Campaigns & Google Ads Automated Ingestion**:
  - Secure REST Webhook API endpoint at `/api/leads/capture/` authenticated via `X-API-KEY`.
  - Automatically captures incoming lead payloads from Google Ads Webhook, Meta Lead Ads (Facebook/Instagram), LinkedIn Lead Gen, and Zapier/Make.
  - **All newly captured leads are automatically recorded in the centralized database and initially assigned the status `New Lead`**.
- **Manual Lead Entry**:
  - Intuitive, fully-validated UI form at `/leads/new/` with auto-default status `New Lead`.
- **Built-in Ads Ingestion Simulator & Tester**:
  - Located at `/leads/integrations/` with 1-click test simulation for Google Ads and Social Media campaigns, live cURL documentation, and response viewer.

### 2. Lead Management & Follow-ups
- **Comprehensive Lead Directory & Filter Suite**:
  - Filter tabs: *All Leads*, *New Leads*, *Hot Quality*, *Due Today*, *Overdue Follow-ups*, *Qualified*, *Closed Won*.
  - Multi-faceted search: by client name, business name, phone, email, location, status, quality, source, and assigned salesperson.
  - **Interactive Kanban Pipeline Board**: Visual drag-and-drop workflow across stages: `New Lead` ➔ `Contacted` ➔ `In Discussion` ➔ `Qualified` ➔ `Proposal Sent` ➔ `Negotiation` ➔ `Closed Won` ➔ `Closed Lost`.
- **Follow-up Management**:
  - Log follow-up interactions (Phone Call, WhatsApp, Email, Video Meeting, In-person Meeting, Demo).
  - Update lead quality (`Hot`, `Warm`, `Cold`, `Unqualified`) and current status after every follow-up.
  - Set next follow-up date and time with automated overdue / today alerts.
  - Chronological interactive follow-up history timeline on every lead.
- **Deal Closure & Complete Business Details Capture**:
  - When a deal is won, record complete business agreement details:
    - Deal Value (₹/$)
    - Closed Date
    - Products & Services Sold
    - Contract Period / Duration
    - Payment Terms
    - Registered Billing Address
    - Tax ID / GSTIN / VAT
    - Closure Remarks & Handover Notes

### 3. Lead Information Fields
Each lead contains:
- Client Name
- Business Name
- Location
- Contact Number
- WhatsApp Number (with 1-click direct chat link)
- Email Address (with 1-click mailto link)
- Business Category (IT, Healthcare, Real Estate, Retail, Manufacturing, Education, Finance, etc.)
- Lead Source (Social Media, Google Ads, Manual Entry, Website, Referral)
- Lead Quality (Hot, Warm, Cold, Unqualified)
- Current Lead Status
- Follow-up History Timeline
- Next Follow-up Date & Time (with Overdue & Due Today indicators)
- Salesperson Assigned

### 4. User Management & Permissions
- **Multi-user Login & Role-Based Permissions**:
  - **Admin / Manager**: Company-wide visibility of all leads, reassign leads, sales performance leaderboard, revenue totals, user account creation and permission management.
  - **Salesperson**: View and manage assigned leads, log follow-ups, close deals, manage personal tasks and daily follow-up queue.
- **Team Management Dashboard**:
  - Accessible to Admin at `/accounts/team/` to add new sales reps, view individual conversion rates, active workloads, and closed revenues.

### 5. Sales & Lead Intelligence Dashboard
- Summary KPI Cards: Total Leads, New Leads (Awaiting Follow-up), Qualified Prospects, Closed Won Deals, Closed Won Revenue, Overdue Actions, Conversion Rate.
- Real-time Interactive Charts (Chart.js):
  - Lead Pipeline Stages (Bar chart)
  - Lead Capture Sources Breakdown (Donut chart)
  - Lead Quality Distribution (Pie chart)
- Direct Action Queue for Today's Follow-ups with 1-click WhatsApp and Phone call shortcuts.
- Sales Leaderboard and Recent Ingestion Feed.
- Export all filtered leads to CSV.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Django 5.x

### 2. Run Migrations & Seed Sample Data
The database is configured with **SQLite** out of the box (zero server setup needed):

```bash
# Apply migrations
python3 manage.py migrate

# Seed realistic demo database (Admin + 3 Sales Reps + 8 Real-world Leads + Follow-ups)
python3 demo_seed.py

# Start development server
python3 manage.py runserver
```

### 3. Start Development Server
```bash
python3 manage.py runserver
```
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin / Manager** | `admin` | `admin123` | View all leads, team performance, assign/reassign, add users, system settings |
| **Salesperson (Senior)** | `vikram_sales` | `sales123` | Assigned leads, follow-ups, deal closures, personal dashboard |
| **Salesperson (Account Exec)** | `ananya_leads` | `sales123` | Assigned leads, follow-ups, deal closures, personal dashboard |
| **Salesperson (BDR)** | `rahul_biz` | `sales123` | Assigned leads, follow-ups, deal closures, personal dashboard |

*(A quick-click credentials filler is also available directly on the login screen for instant testing!)*

---

## 📡 Automated Lead Capture API (Requirement 1)

**Endpoint:** `POST /api/leads/capture/`  
**Header:** `X-API-KEY: leadflow_secure_webhook_key_2026`  
**Content-Type:** `application/json`

### Sample Request:
```bash
curl -X POST "http://127.0.0.1:8000/api/leads/capture/" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: leadflow_secure_webhook_key_2026" \
  -d '{
    "client_name": "Rohan Verma",
    "business_name": "Verma Cloud Technologies",
    "contact_number": "+91 99887 76655",
    "whatsapp_number": "+91 99887 76655",
    "email": "rohan@vermacloud.io",
    "location": "Bengaluru, Karnataka",
    "business_category": "Information Technology & Software",
    "lead_source": "Google Ads",
    "campaign_name": "Google Ads Q4 Enterprise",
    "notes": "Looking for lead management software for 15 sales reps."
  }'
```

---

## 🧪 Running Automated Unit Tests
To run the automated test suite verifying lead capture, follow-up logging, deal closure, and permissions:
```bash
python3 manage.py test leads
```

