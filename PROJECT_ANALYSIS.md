# วิเคราะห์โครงสร้างและการทำงานของโปรเจกต์ DCA Investment Platform

## 📋 สารบัญ
1. [โครงสร้างโปรเจกต์โดยรวม](#1-โครงสร้างโปรเจกต์โดยรวม)
2. [การไหลของข้อมูล (Data Flow)](#2-การไหลของข้อมูล)
3. [ตำแหน่งฟีเจอร์และฟังก์ชันหลัก](#3-ตำแหน่งฟีเจอร์และฟังก์ชันหลัก)
4. [การเชื่อมต่อระหว่างส่วนต่างๆ](#4-การเชื่อมต่อระหว่างส่วนต่างๆ)

---

## 1. โครงสร้างโปรเจกต์โดยรวม

### 🎯 จุดประสงค์โปรเจกต์
แพลตฟอร์มสำหรับวางแผนการลงทุน DCA (Dollar-Cost Averaging) ในหุ้นไทย โดยใช้ Genetic Algorithm (GA) ในการหาสัดส่วนน้ำหนักพอร์ตโฟลิโอที่เหมาะสม

### 📁 โครงสร้างไฟล์/โฟลเดอร์

```
MyThesisProject/
│
├── manage.py                          ← จุดเริ่มต้นหลักของ Django (Entry Point)
├── db.sqlite3                         ← ฐานข้อมูล SQLite
├── requirements.txt                   ← ไลบรารีที่ต้องใช้
├── README.md                          ← คู่มือการใช้งาน
│
├── dca_system/                        ← โฟลเดอร์ตั้งค่า Django หลัก
│   ├── settings.py                   ← ตั้งค่า Django (Database, Middleware, Apps)
│   ├── urls.py                       ← ต้นทางของ URL Routing หลัก
│   ├── wsgi.py                       ← WSGI Application สำหรับ Production
│   └── asgi.py                       ← ASGI Application สำหรับ Async
│
└── dashboard/                         ← แอปพลิเคชันหลัก
    ├── models.py                     ← โมเดล Database (7 Models)
    ├── views.py                      ← Logic เตรียมข้อมูลและแสดงผล
    ├── urls.py                       ← URL Routing ของแอป dashboard
    ├── services.py                   ← Business Logic (Helper Functions)
    ├── tasks.py                      ← Background Task (Celery/Async)
    ├── ga_optimizer.py               ← Genetic Algorithm Main Logic
    ├── admin.py                      ← Django Admin Configuration
    ├── tests.py                      ← Unit Tests
    │
    ├── optimizers/                   ← Strategy Pattern for Optimization
    │   ├── base.py                  ← Abstract Base Class
    │   ├── ga.py                    ← GA Optimizer Strategy
    │   ├── equal_weight.py          ← Equal Weight Optimizer Strategy
    │   └── mean_variance.py         ← Mean-Variance Optimizer Strategy
    │
    ├── management/
    │   └── commands/
    │       ├── setup_project.py     ← Command: python manage.py setup_project
    │       └── seed_initial_data.py ← Command: ดึงข้อมูลหุ้นเริ่มต้น
    │
    ├── migrations/                  ← Database Schema History
    │   ├── 0001_initial.py
    │   ├── 0002_remove_portfolioresult_plan_and_more.py
    │   ├── 0003_userplan_duration_years_userplan_target_amount.py
    │   ├── 0004_stock_change_stock_last_price_stock_percent_change_and_more.py
    │   ├── 0005_dcapreset_userplan_created_at_and_more.py
    │   ├── 0006_userplan_last_chart_data_userplan_last_chart_labels.py
    │   ├── 0007_garesultsnapshot.py
    │   ├── 0008_remove_userprofile_preferred_language.py
    │   └── 0009_add_userprofile_preferred_language.py
    │
    ├── templates/dashboard/         ← HTML Templates (13 Files)
    │   ├── index.html               ← หน้า Dashboard หลัก
    │   ├── login.html               ← หน้า Login
    │   ├── register.html            ← หน้า Register
    │   ├── profile.html             ← ดูโปรไฟล์
    │   ├── profile_edit.html        ← แก้ไขโปรไฟล์
    │   ├── password_change.html     ← เปลี่ยนรหัสผ่าน
    │   ├── investment_records.html  ← ดูบันทึกการลงทุน
    │   ├── add_investment_record.html ← เพิ่มบันทึกการลงทุน
    │   ├── ga_history.html          ← ประวัติ GA Results
    │   ├── ga_snapshot_detail.html  ← รายละเอียด GA Snapshot
    │   ├── statistics.html          ← สถิติและการวิเคราะห์
    │   ├── preset_plans.html        ← แผนการลงทุนสำเร็จรูป
    │   └── pdf_template.html        ← Template สำหรับ PDF Export
    │
    └── static/dashboard/            ← Static Files (CSS, JS, Images)
        └── css/                     ← Stylesheets
```

### 🔑 บทบาทของไฟล์/โฟลเดอร์หลัก

| ไฟล์/โฟลเดอร์ | บทบาท | รายละเอียด |
|---|---|---|
| `manage.py` | Entry Point | รัน command: `python manage.py` |
| `dca_system/` | Core Configuration | ตั้งค่า Database, Middleware, Routes |
| `dashboard/models.py` | Data Schema | 7 Models: Stock, UserProfile, UserPlan, DCAPreset, UserInvestmentRecord, GAResultSnapshot |
| `dashboard/views.py` | HTTP Handlers | 10+ View Functions สำหรับ handle requests |
| `dashboard/urls.py` | Route Mapping | เชื่อม URL path ไปยัง Views |
| `dashboard/ga_optimizer.py` | GA Algorithm | ฟังก์ชัน `run_genetic_algorithm()` หลัก |
| `dashboard/optimizers/` | Strategy Pattern | 3 Optimization Strategies (GA, Mean-Variance, Equal-Weight) |
| `dashboard/tasks.py` | Async Task | Celery Task สำหรับประมวลผล GA ในพื้นหลัง |
| `dashboard/services.py` | Business Logic | Helper Functions: `build_dca_projection()`, `normalize_selected_stocks()` |
| `dashboard/management/commands/` | Setup Scripts | CLI Commands สำหรับ setup และ seed data |

---

## 2. การไหลของข้อมูล (Data Flow)

### 🔄 ลำดับขั้นตอนการทำงานโดยรวม

```
User Browser
    ↓
Request → Django URL Router [dca_system/urls.py]
    ↓
Route to View [dashboard/urls.py]
    ↓
View Handler [dashboard/views.py]
    ├─→ Load Data from DB [dashboard/models.py]
    ├─→ Process with Services [dashboard/services.py]
    ├─→ Optimize Portfolio [GA/Optimizers]
    ├─→ Save Results to DB [GAResultSnapshot, UserPlan]
    └─→ Render Template [dashboard/templates/]
    ↓
Response → Browser
```

### 📊 Data Flow รายฟีเจอร์

#### **A. ฟีเจอร์ 1: User Registration & Login**

**ดึงข้อมูล:**
- ไม่ได้ดึงจากไหน แต่ input มาจากผู้ใช้ผ่าน form

**ประมวลผล:**
```
User fills register form
    ↓
[dashboard/views.py] register_view() : Line 295-330
    ├─ Validate ชื่อผู้ใช้ไม่ซ้ำ
    ├─ Validate รหัสผ่านตรงกัน
    ├─ Create User (Django Auth)
    ├─ Create UserPlan (Default)
    └─ Create UserProfile (with phone)
    ↓
Save to DB [User, UserPlan, UserProfile]
    ↓
Auto Login & Redirect to Dashboard
```

**ไฟล์ที่เกี่ยวข้อง:**
- [dashboard/views.py](dashboard/views.py#L295) - `register_view()` 
- [dashboard/models.py](dashboard/models.py#L19) - `UserProfile` model
- [dashboard/models.py](dashboard/models.py#L24) - `UserPlan` model
- [dashboard/urls.py](dashboard/urls.py#L26) - `register/` endpoint

---

#### **B. ฟีเจอร์ 2: Dashboard Main (Portfolio Optimization)**

**ดึงข้อมูล:**
```
1. ฐานข้อมูล (SQLite)
   - UserPlan ของผู้ใช้ปัจจุบัน
   - หุ้นที่เลือก (selected_stocks field)
   - ผลลัพธ์ GA ล่าสุด

2. ภายนอก (Yahoo Finance via yfinance)
   - ข้อมูลราคาหุ้น 3 ปี [.BK suffix for Thai stocks]
   - Historical returns, covariance matrix
```

**ประมวลผล:**
```
1. Load UserPlan
   [dashboard/views.py] dashboard_view() : Line 46-145
   
2. Normalize Selected Stocks
   [dashboard/services.py] normalize_selected_stocks() : Line 7-11
   
3. Run 3 Optimization Algorithms (Parallel):
   
   a. GA Optimizer:
      [dashboard/optimizers/ga.py] GAOptimizer.optimize() : Line 8-11
         ↓ call
      [dashboard/ga_optimizer.py] run_genetic_algorithm() : Line 6-160
         ├─ Fetch data: yfinance.download() (Line 26-28)
         ├─ Calculate returns & covariance (Line 40-62)
         ├─ Run GA loop 50 generations (Line 86-108)
         │  ├─ Selection (Roulette Wheel) 
         │  ├─ Crossover 
         │  ├─ Mutation (10% probability)
         │  └─ Fitness: Sharpe Ratio
         └─ Return best weights & metrics
   
   b. Mean-Variance Optimizer:
      [dashboard/optimizers/mean_variance.py]
      
   c. Equal-Weight Optimizer:
      [dashboard/optimizers/equal_weight.py]

4. Build DCA Projection:
   [dashboard/services.py] build_dca_projection() : Line 14-42
   - monthly_investment, duration_years, target_amount, expected_return (from GA)
   - Calculate yearly portfolio value
   - Check if target reached
   - Generate chart labels & data

5. Prepare Context for Template:
   [dashboard/views.py] : Line 92-142
   - Model comparison (GA vs Mean-Variance vs Equal-Weight)
   - Selected stocks & weights
   - Chart data & projection
   - Latest GA snapshot

6. Render Template
   [dashboard/templates/dashboard/index.html]
```

**บันทึกข้อมูล:**
```
Temporarily stored in Context (Not saved to DB yet)
- Result saved only when user clicks "Update Investment"
```

**แสดงผล:**
```
[dashboard/templates/dashboard/index.html]
├─ Stock Selection Form
├─ Model Comparison Table
├─ Portfolio Allocation Chart (Pie/Bar)
├─ DCA Projection Chart
├─ Investment Parameters Form
└─ GA History Section
```

**ไฟล์ที่เกี่ยวข้อง:**
- [dashboard/views.py](dashboard/views.py#L46) - `dashboard_view()` main logic
- [dashboard/urls.py](dashboard/urls.py#L48) - `dashboard/` endpoint
- [dashboard/ga_optimizer.py](dashboard/ga_optimizer.py#L6) - `run_genetic_algorithm()`
- [dashboard/services.py](dashboard/services.py#L14) - `build_dca_projection()`
- [dashboard/templates/dashboard/index.html](dashboard/templates/dashboard/index.html)

---

#### **C. ฟีเจอร์ 3: Update Investment Parameters & Start Optimization**

**ดึงข้อมูล:**
```
User Input from Form:
- monthly_investment_input
- duration_years_input
- target_amount_input
```

**ประมวลผล:**
```
1. User POST to update_investment()
   [dashboard/views.py] update_investment() : Line 147-174
   ├─ Parse form inputs
   ├─ Remove comma formatting
   ├─ Update UserPlan fields
   ├─ Validate (must be positive)
   ├─ Save to DB
   └─ Dispatch Celery Task (Async)

2. Celery Task: optimize_portfolio_task()
   [dashboard/tasks.py] optimize_portfolio_task() : Line 28-65
   ├─ Get UserPlan from DB
   ├─ Call run_genetic_algorithm()
   ├─ Build DCA Projection
   ├─ Create GAResultSnapshot (save history)
   ├─ Update UserPlan.last_* fields
   └─ Save all to DB

3. Alternative: Direct API Call
   [dashboard/views.py] start_optimization() : Line 177-183
   └─ Return JSON with task_id
```

**บันทึกข้อมูล:**
```
Database Models Updated:
- UserPlan.monthly_investment
- UserPlan.duration_years
- UserPlan.target_amount
- UserPlan.last_optimized_weights
- UserPlan.last_expected_return
- UserPlan.last_sharpe_ratio
- UserPlan.last_chart_labels
- UserPlan.last_chart_data
- UserPlan.updated_at

New Record Created:
- GAResultSnapshot (timestamp, weights, metrics, chart data)
```

**ไฟล์ที่เกี่ยวข้อง:**
- [dashboard/views.py](dashboard/views.py#L147) - `update_investment()`
- [dashboard/views.py](dashboard/views.py#L177) - `start_optimization()`
- [dashboard/urls.py](dashboard/urls.py#L52) - `update-investment/` endpoint
- [dashboard/tasks.py](dashboard/tasks.py#L28) - `optimize_portfolio_task()`

---

#### **D. ฟีเจอร์ 4: Profile Management**

**ดึงข้อมูล:**
```
From Database:
- User (from Django Auth)
- UserProfile (bio, phone, language preference)
```

**ประมวลผล:**

**View Profile:**
```
[dashboard/views.py] profile_view() : Line 239-242
├─ Get or Create UserProfile
└─ Render profile.html
```

**Edit Profile:**
```
[dashboard/views.py] profile_edit_view() : Line 244-269
├─ Parse form: first_name, last_name, email, phone, bio
├─ Update User object
├─ Update UserProfile object
├─ Save to DB
└─ Redirect to profile
```

**Change Password:**
```
[dashboard/views.py] password_change_view() : Line 271-288
├─ Verify old password
├─ Validate new passwords match
├─ Set new password (Django hashing)
├─ Update session hash (stay logged in)
└─ Save to DB
```

**บันทึกข้อมูล:**
```
Models Updated:
- User (first_name, last_name, email, password)
- UserProfile (phone, bio, updated_at)
```

**ไฟล์ที่เกี่ยวข้อง:**
- [dashboard/views.py](dashboard/views.py#L239) - Profile views
- [dashboard/urls.py](dashboard/urls.py#L69) - Profile endpoints
- [dashboard/models.py](dashboard/models.py#L19) - `UserProfile` model

---

#### **E. ฟีเจอร์ 5: Investment Records**

**ดึงข้อมูล:**
```
From Database:
- UserInvestmentRecord (filtered by current user)
```

**ประมวลผล:**

**View Records:**
```
[dashboard/views.py] investment_records_view() : Line 291-318
├─ Query records for current user
├─ Calculate total_invested (sum)
├─ Calculate average_per_month
├─ Sort by -month (newest first)
└─ Format with comma separators
```

**Add Record:**
```
[dashboard/views.py] add_investment_record_view() : Line 320-350
├─ Parse: month, amount_invested, notes
├─ Validate amount (must be positive)
├─ Check unique_together (user, month)
├─ Create UserInvestmentRecord
└─ Redirect to records list
```

**บันทึกข้อมูล:**
```
Model Created:
- UserInvestmentRecord (user, month, amount_invested, notes, timestamps)
```

**ไฟล์ที่เกี่ยวข้อง:**
- [dashboard/views.py](dashboard/views.py#L291) - Investment record views
- [dashboard/urls.py](dashboard/urls.py#L82) - Investment endpoints
- [dashboard/models.py](dashboard/models.py#L74) - `UserInvestmentRecord` model

---

#### **F. ฟีเจอร์ 6: GA History & Snapshots**

**ดึงข้อมูล:**
```
From Database:
- GAResultSnapshot (all snapshots for current user, ordered by -saved_at)
```

**ประมวลผล:**
```
[dashboard/views.py] (lines that reference GAResultSnapshot)
- safe_snapshot_first() : Line 23-26 (get latest)
- safe_snapshot_list() : Line 29-32 (get all)
- build_saved_ga_summary() : [dashboard/services.py] Line 46-83
  ├─ Compare snapshot stocks vs current selected stocks
  ├─ Process allocations (group < 1% as "other")
  ├─ Calculate diff from current metrics
  └─ Return display-safe summary
```

**บันทึกข้อมูล:**
```
Already stored when optimize_portfolio_task() runs:
- GAResultSnapshot.saved_at (auto_now_add)
- GAResultSnapshot.expected_return, sharpe_ratio
- GAResultSnapshot.weights (JSON)
- GAResultSnapshot.chart_labels, chart_data (JSON)
- GAResultSnapshot.monthly_investment, duration_years, target_amount
```

**ไฟล์ที่เกี่ยวข้อง:**
- [dashboard/models.py](dashboard/models.py#L100) - `GAResultSnapshot` model
- [dashboard/tasks.py](dashboard/tasks.py#L46) - Create snapshot
- [dashboard/services.py](dashboard/services.py#L46) - Build summary for display

---

### 🗄️ Database Schema (ทั้ง 7 Models)

```sql
┌─────────────────────────────────────────────────────────────┐
│ Stock (หุ้น)                                                 │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ symbol (CharField, unique)      ← "ADVANC", "AOT", etc    │
│ is_set50 (BooleanField)         ← True/False              │
│ last_price (DecimalField)       ← ราคาล่าสุด              │
│ change (DecimalField)           ← การเปลี่ยนแปลง          │
│ percent_change (FloatField)     ← % เปลี่ยนแปลง          │
│ updated_at (DateTimeField)      ← auto_now               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ User (Django Built-in) ← from django.contrib.auth.models │
├─────────────────────────────────────────────────────────────┤
│ id, username, password, email, first_name, last_name      │
│ is_active, is_staff, date_joined, last_login              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ UserProfile (One-to-One with User)                         │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ user (OneToOneField → User)     ← Link to User             │
│ bio (TextField)                 ← เกี่ยวกับตัวเอง        │
│ phone (CharField)               ← เบอร์โทร                │
│ preferred_language (CharField)  ← 'th' or 'en'            │
│ created_at (DateTimeField)      ← auto_now_add            │
│ updated_at (DateTimeField)      ← auto_now                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ UserPlan (One-to-One with User)                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ user (OneToOneField → User)     ← Link to User             │
│ monthly_investment (DecimalField) ← เงินต่อเดือน          │
│ duration_years (IntegerField)   ← ระยะเวลา (ปี)          │
│ target_amount (DecimalField)    ← เป้าหมาย               │
│ selected_stocks (TextField)     ← "ADVANC,AOT,CPALL,..."  │
│ last_optimized_weights (JSONField) ← {"ADVANC": 0.3...}   │
│ last_expected_return (FloatField) ← 0.12 (12%)            │
│ last_sharpe_ratio (FloatField)  ← 1.5                     │
│ last_chart_labels (JSONField)   ← ["ปีที่ 1", "ปีที่ 2"]   │
│ last_chart_data (JSONField)     ← [100000, 200000]        │
│ created_at (DateTimeField)      ← auto_now_add            │
│ updated_at (DateTimeField)      ← auto_now                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DCAPreset (แผนการลงทุนสำเร็จรูป)                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ name (CharField)                ← "Balanced SET50 DCA"     │
│ description (TextField)         ← อธิบาย                  │
│ monthly_investment (DecimalField) ← 5000                   │
│ duration_years (IntegerField)   ← 10                       │
│ target_amount (DecimalField)    ← 1000000                  │
│ selected_stocks (TextField)     ← "ADVANC,AOT,CPALL,..."  │
│ expected_return (FloatField)    ← 0.105 (10.5%)           │
│ risk_level (CharField)          ← 'low', 'medium', 'high' │
│ is_active (BooleanField)        ← True/False              │
│ created_at (DateTimeField)      ← auto_now_add            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ UserInvestmentRecord (บันทึกการลงทุน)                      │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ user (ForeignKey → User)        ← Link to User             │
│ month (DateField)               ← 2024-01-01              │
│ amount_invested (DecimalField)  ← 5000                     │
│ notes (TextField)               ← หมายเหตุ                │
│ created_at (DateTimeField)      ← auto_now_add            │
│ updated_at (DateTimeField)      ← auto_now                │
│ unique_together: (user, month)  ← Cannot duplicate        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ GAResultSnapshot (ประวัติผลลัพธ์ GA)                        │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ user (ForeignKey → User)        ← Link to User             │
│ saved_at (DateTimeField)        ← auto_now_add            │
│ expected_return (FloatField)    ← 0.12 (12%)              │
│ sharpe_ratio (FloatField)       ← 1.5                     │
│ weights (JSONField)             ← {"ADVANC": 0.3...}      │
│ chart_labels (JSONField)        ← ["ปีที่ 1", "ปีที่ 2"]   │
│ chart_data (JSONField)          ← [100000, 200000]        │
│ final_portfolio_value (DecimalField) ← 1234567.89         │
│ monthly_investment (DecimalField) ← 5000                   │
│ duration_years (IntegerField)   ← 10                       │
│ target_amount (DecimalField)    ← 1000000                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. ตำแหน่งฟีเจอร์และฟังก์ชันหลัก

### 🔍 ตารางสรุปฟีเจอร์ทั้งหมด

| # | ฟีเจอร์ | View Function | URL Pattern | Template | Model |
|---|--------|---------------|------------|----------|-------|
| 1 | Login | `auth_views.LoginView` | `''` | `login.html` | User |
| 2 | Logout | `auth_views.LogoutView` | `logout/` | - | - |
| 3 | Register | `register_view()` | `register/` | `register.html` | User, UserPlan, UserProfile |
| 4 | Dashboard | `dashboard_view()` | `dashboard/` | `index.html` | UserPlan, Stock, GAResultSnapshot |
| 5 | Update Investment | `update_investment()` | `update-investment/` | - | UserPlan |
| 6 | Start Optimization | `start_optimization()` | `start-optimization/<id>/` | - | UserPlan, GAResultSnapshot |
| 7 | View Profile | `profile_view()` | `profile/` | `profile.html` | UserProfile |
| 8 | Edit Profile | `profile_edit_view()` | `profile/edit/` | `profile_edit.html` | User, UserProfile |
| 9 | Change Password | `password_change_view()` | `profile/change-password/` | `password_change.html` | User |
| 10 | Investment Records | `investment_records_view()` | `investment-records/` | `investment_records.html` | UserInvestmentRecord |
| 11 | Add Investment | `add_investment_record_view()` | `investment-records/add/` | `add_investment_record.html` | UserInvestmentRecord |
| 12 | GA History | `ga_history_view()` | `ga-history/` | `ga_history.html` | GAResultSnapshot |
| 13 | GA Snapshot Detail | `ga_snapshot_detail_view()` | `ga-snapshot/<id>/` | `ga_snapshot_detail.html` | GAResultSnapshot |
| 14 | Statistics | `statistics_view()` | `statistics/` | `statistics.html` | GAResultSnapshot, UserInvestmentRecord |
| 15 | Preset Plans | `preset_plans_view()` | `preset-plans/` | `preset_plans.html` | DCAPreset |

---

### 📍 ตำแหน่งรายละเอียด

#### **Authentication & User Management**

| ฟีเจอร์ | ไฟล์ | Function/Class | ตำแหน่ง | บรรทัด |
|--------|------|--------|---------|-------|
| **Login** | views.py | (Django Built-in) | - | - |
| | urls.py | LoginView | [dashboard/urls.py](dashboard/urls.py#L12) | 12-20 |
| **Register** | views.py | `register_view()` | [dashboard/views.py](dashboard/views.py#L295) | 295-334 |
| | urls.py | path('register/') | [dashboard/urls.py](dashboard/urls.py#L26) | 26-30 |
| | templates | register.html | [dashboard/templates/dashboard/register.html](dashboard/templates/dashboard/register.html) | - |
| **Logout** | urls.py | LogoutView | [dashboard/urls.py](dashboard/urls.py#L34) | 34-39 |
| **Profile View** | views.py | `profile_view()` | [dashboard/views.py](dashboard/views.py#L239) | 239-242 |
| | urls.py | path('profile/') | [dashboard/urls.py](dashboard/urls.py#L69) | 69-74 |
| **Profile Edit** | views.py | `profile_edit_view()` | [dashboard/views.py](dashboard/views.py#L244) | 244-269 |
| | urls.py | path('profile/edit/') | [dashboard/urls.py](dashboard/urls.py#L76) | 76-81 |
| **Change Password** | views.py | `password_change_view()` | [dashboard/views.py](dashboard/views.py#L271) | 271-288 |
| | urls.py | path('profile/change-password/') | [dashboard/urls.py](dashboard/urls.py#L83) | 83-88 |

---

#### **Dashboard & Portfolio Management**

| ฟีเจอร์ | ไฟล์ | Function/Class | ตำแหน่ง | บรรทัด |
|--------|------|--------|---------|-------|
| **Dashboard Main** | views.py | `dashboard_view()` | [dashboard/views.py](dashboard/views.py#L46) | 46-145 |
| | urls.py | path('dashboard/') | [dashboard/urls.py](dashboard/urls.py#L48) | 48-53 |
| | templates | index.html | [dashboard/templates/dashboard/index.html](dashboard/templates/dashboard/index.html) | - |
| **Update Investment** | views.py | `update_investment()` | [dashboard/views.py](dashboard/views.py#L147) | 147-174 |
| | urls.py | path('update-investment/') | [dashboard/urls.py](dashboard/urls.py#L55) | 55-60 |
| **Start Optimization** | views.py | `start_optimization()` | [dashboard/views.py](dashboard/views.py#L177) | 177-183 |
| | urls.py | path('start-optimization/<id>/') | [dashboard/urls.py](dashboard/urls.py#L62) | 62-67 |
| **Background Task** | tasks.py | `optimize_portfolio_task()` | [dashboard/tasks.py](dashboard/tasks.py#L28) | 28-65 |
| | - | (Uses Celery or Fallback) | [dashboard/tasks.py](dashboard/tasks.py#L5) | 5-24 |

---

#### **Investment Records**

| ฟีเจอร์ | ไฟล์ | Function/Class | ตำแหน่ง | บรรทัด |
|--------|------|--------|---------|-------|
| **View Records** | views.py | `investment_records_view()` | [dashboard/views.py](dashboard/views.py#L291) | 291-318 |
| | urls.py | path('investment-records/') | [dashboard/urls.py](dashboard/urls.py#L97) | 97-102 |
| **Add Record** | views.py | `add_investment_record_view()` | [dashboard/views.py](dashboard/views.py#L320) | 320-350 |
| | urls.py | path('investment-records/add/') | [dashboard/urls.py](dashboard/urls.py#L104) | 104-109 |

---

#### **Optimization Algorithms**

| Optimizer | ไฟล์ | Function/Class | ตำแหน่ง | บรรทัด |
|-----------|------|--------|---------|-------|
| **GA Optimizer** | ga.py | `GAOptimizer.optimize()` | [dashboard/optimizers/ga.py](dashboard/optimizers/ga.py#L8) | 8-11 |
| **GA Main Logic** | ga_optimizer.py | `run_genetic_algorithm()` | [dashboard/ga_optimizer.py](dashboard/ga_optimizer.py#L6) | 6-160 |
| | - | Data fetching (yfinance) | [dashboard/ga_optimizer.py](dashboard/ga_optimizer.py#L26) | 26-28 |
| | - | GA loop (50 gen) | [dashboard/ga_optimizer.py](dashboard/ga_optimizer.py#L86) | 86-108 |
| | - | Fitness calculation | [dashboard/ga_optimizer.py](dashboard/ga_optimizer.py#L76) | 76-79 |
| **Mean-Variance** | mean_variance.py | `MeanVarianceOptimizer.optimize()` | [dashboard/optimizers/mean_variance.py](dashboard/optimizers/mean_variance.py) | - |
| **Equal Weight** | equal_weight.py | `EqualWeightOptimizer.optimize()` | [dashboard/optimizers/equal_weight.py](dashboard/optimizers/equal_weight.py) | - |
| **Base Class** | base.py | `BaseOptimizer` | [dashboard/optimizers/base.py](dashboard/optimizers/base.py) | - |

---

#### **Services & Helpers**

| ฟังก์ชัน | ไฟล์ | ตำแหน่ง | บรรทัด | จุดประสงค์ |
|---------|------|---------|-------|----------|
| `normalize_selected_stocks()` | services.py | [dashboard/services.py](dashboard/services.py#L7) | 7-11 | แยก stock symbols จาก string |
| `build_dca_projection()` | services.py | [dashboard/services.py](dashboard/services.py#L14) | 14-42 | คำนวณ DCA projection แบบ yearly |
| `build_saved_ga_summary()` | services.py | [dashboard/services.py](dashboard/services.py#L46) | 46-83 | เตรียมข้อมูล GA snapshot สำหรับแสดงผล |
| `safe_snapshot_first()` | views.py | [dashboard/views.py](dashboard/views.py#L23) | 23-26 | ดึง snapshot ล่าสุด safely |
| `safe_snapshot_list()` | views.py | [dashboard/views.py](dashboard/views.py#L29) | 29-32 | ดึง snapshots หลายตัว safely |

---

#### **Admin Panel & Management Commands**

| คำสั่ง/Admin | ไฟล์ | ตำแหน่ง | บรรทัด | จุดประสงค์ |
|------------|------|---------|-------|----------|
| `setup_project` | setup_project.py | [dashboard/management/commands/setup_project.py](dashboard/management/commands/setup_project.py) | - | Run migrations + seed data |
| `seed_initial_data` | seed_initial_data.py | [dashboard/management/commands/seed_initial_data.py](dashboard/management/commands/seed_initial_data.py) | - | Seed 8 stocks + 2 presets |
| **Stock Admin** | admin.py | [dashboard/admin.py](dashboard/admin.py#L10) | 10-45 | Manage stocks, update prices |
| **UserPlan Admin** | admin.py | [dashboard/admin.py](dashboard/admin.py) | - | View/edit user plans |
| **Profile Admin** | admin.py | [dashboard/admin.py](dashboard/admin.py) | - | Manage user profiles |

---

### 🎲 Call Chain Examples

#### **Example 1: User Registration Flow**

```
1. Browser: GET /register/
   ↓
2. [dashboard/urls.py:26-30] → route to register_view
   ↓
3. [dashboard/views.py:295-334] register_view()
   ├─ GET: render(register.html)
   ├─ POST: Parse form data
   │   ├─ Validate username unique
   │   ├─ Validate passwords match
   │   ├─ Create User (Django Auth)
   │   ├─ Create UserPlan [models.py:24]
   │   ├─ Create UserProfile [models.py:19]
   │   └─ Auto login & redirect to dashboard
   ↓
4. Browser: Redirect to /dashboard/
```

---

#### **Example 2: Optimize Portfolio Flow**

```
1. Browser: POST /update-investment/
   ↓
2. [dashboard/urls.py:55-60] → route to update_investment
   ↓
3. [dashboard/views.py:147-174] update_investment()
   ├─ Parse form inputs (monthly, duration, target)
   ├─ Validate & update UserPlan [models.py:24]
   ├─ Save to DB
   └─ Dispatch Celery task → optimize_portfolio_task(plan.id)
   ↓
4. [dashboard/tasks.py:28-65] optimize_portfolio_task() (Background)
   ├─ Get UserPlan from DB
   ├─ Extract assets: plan.selected_stocks.split(',')
   ├─ Call [dashboard/ga_optimizer.py:6] run_genetic_algorithm(assets)
   │   ├─ Download from yfinance (Line 26-28)
   │   ├─ Calculate returns & covariance (Line 40-62)
   │   ├─ Run GA loop (Line 86-108)
   │   │   └─ Selection, Crossover, Mutation
   │   └─ Return: {expected_return, sharpe_ratio, weights}
   ├─ Call [dashboard/services.py:14] build_dca_projection()
   ├─ Create GAResultSnapshot [models.py:100]
   ├─ Update UserPlan.last_* fields
   └─ Save all to DB
   ↓
5. Browser: GET /dashboard/
   ↓
6. [dashboard/views.py:46-145] dashboard_view()
   ├─ Load UserPlan
   ├─ Load latest GA results
   ├─ Prepare context with all optimization data
   └─ Render [dashboard/templates/dashboard/index.html]
```

---

#### **Example 3: View GA History Flow**

```
1. Browser: GET /ga-history/
   ↓
2. [dashboard/urls.py] → route to ga_history_view
   ↓
3. [dashboard/views.py] ga_history_view()
   ├─ Query: GAResultSnapshot.objects.filter(user=request.user)
   ├─ Order by -saved_at
   ├─ For each snapshot:
   │   └─ Call [dashboard/services.py:46] build_saved_ga_summary()
   │       ├─ Validate snapshot stocks == current selected stocks
   │       ├─ Process allocations
   │       └─ Calculate diffs (return, sharpe)
   └─ Render [dashboard/templates/dashboard/ga_history.html]
   ↓
4. Browser: Display list of GA results with timestamps
```

---

## 4. การเชื่อมต่อระหว่างส่วนต่างๆ

### 🔗 Database Connections (Foreign Keys & Relations)

```
User (Django Built-in)
  ├─ 1:1 → UserProfile
  ├─ 1:1 → UserPlan
  ├─ 1:N → UserInvestmentRecord (ForeignKey)
  └─ 1:N → GAResultSnapshot (ForeignKey)

Stock
  └─ Referenced by UserPlan.selected_stocks (TextField, not FK)

DCAPreset
  └─ Reference-only model (displayed in templates)
```

### 🌐 API Connections

#### **External API: Yahoo Finance**

```
Where Used:
[dashboard/ga_optimizer.py:26]
└─ yf.download(tickers, period="3y", progress=False)['Close']

Purpose:
- Download historical stock prices (3 years)
- Tickers format: "ADVANC.BK", "AOT.BK" (Thai suffix)

Returns:
- DataFrame with Close prices
- Used to calculate: returns, covariance matrix, expected return
```

#### **Internal API: Admin Endpoints**

```
Location:
[dashboard/admin.py]

Actions:
1. Update Stock Prices [admin.py:20]
   └─ Manually fetch latest prices from Yahoo Finance

2. Seed Missing Stocks [admin.py:24]
   └─ Create missing stock records with default symbols

Both accessible via Django Admin at: /admin/dashboard/stock/
```

### 🔀 Template Connections

```
Base Templates (if exists):
[dashboard/templates/dashboard/base.html] (assumed)

Child Templates:
├─ login.html
├─ register.html
├─ index.html (dashboard)
├─ profile.html
├─ profile_edit.html
├─ password_change.html
├─ investment_records.html
├─ add_investment_record.html
├─ ga_history.html
├─ ga_snapshot_detail.html
├─ statistics.html
├─ preset_plans.html
└─ pdf_template.html (for export)

Context Variables Flow:
dashboard_view() → context dict → index.html template variables
   ├─ selected_assets
   ├─ model_comparison
   ├─ weights_display
   ├─ chart_labels, chart_data
   ├─ saved_ga_summary
   └─ ... (15+ variables)
```

### 📊 Optimization Pipeline (Detailed)

```
User Input:
- selected_stocks: "ADVANC,AOT,CPALL,KBANK,PTT"
- monthly_investment: 5000
- duration_years: 10
- target_amount: 1000000

Processing Pipeline:
1. [services.py:7] normalize_selected_stocks()
   └─ Output: ['ADVANC', 'AOT', 'CPALL', 'KBANK', 'PTT']

2. [ga_optimizer.py:6] run_genetic_algorithm(assets)
   ├─ Add .BK suffix: ['ADVANC.BK', 'AOT.BK', ...]
   ├─ yfinance.download() → prices DataFrame
   ├─ pct_change() → returns DataFrame
   ├─ Calculate mean_returns (annual)
   ├─ Calculate cov_matrix (annual)
   ├─ Initialize population (random weights)
   ├─ For 50 generations:
   │   ├─ Fitness calculation (Sharpe Ratio)
   │   ├─ Selection (Roulette Wheel)
   │   ├─ Crossover
   │   └─ Mutation (10% probability)
   └─ Output: {'expected_return': 0.12, 'sharpe_ratio': 1.5, 'weights': {...}}

3. [services.py:14] build_dca_projection()
   Input: monthly_investment, duration_years, target_amount, expected_return
   ├─ monthly_rate = expected_return / 12
   ├─ For each month (1 to 120):
   │   ├─ current_value = (current_value + monthly_inv) * (1 + monthly_rate)
   │   ├─ Check if target reached
   │   └─ Every 12 months: append to chart_data
   └─ Output: {'chart_labels': [...], 'chart_data': [...], 'final_portfolio_value': ...}

4. Template Rendering
   └─ [index.html] displays all results

5. Optional: Save to DB
   └─ [tasks.py:46] GAResultSnapshot.objects.create(...)
```

### 🔐 Security & Authentication Flow

```
Django Auth System:
1. Login Request
   → [urls.py:12] LoginView
   → Django Session Management

2. @login_required decorator
   [views.py: lines 46, 147, 177, 239, 244, 271, 291, 320]
   └─ Redirects unauthenticated users to /login/

3. User Isolation
   └─ All queries filtered by request.user
   ├─ UserPlan: get_or_create(user=request.user)
   ├─ GAResultSnapshot: filter(user=request.user)
   ├─ UserInvestmentRecord: filter(user=request.user)
   └─ UserProfile: get_or_create(user=request.user)

4. Password Management
   [views.py:271] password_change_view()
   ├─ Check old password: request.user.check_password()
   ├─ Hash new password: request.user.set_password()
   └─ Update session: update_session_auth_hash()
```

### ⚙️ Configuration Connections

```
[dca_system/settings.py]
├─ INSTALLED_APPS: ['jazzmin', 'django.contrib.admin', 'dashboard']
├─ DATABASES: SQLite [BASE_DIR / 'db.sqlite3']
├─ MIDDLEWARE: Security, Sessions, Auth, Messages
├─ ROOT_URLCONF: 'dca_system.urls'
├─ TEMPLATES: APP_DIRS = True [templates/dashboard/]

[dca_system/urls.py]
├─ path('admin/', admin.site.urls)
└─ path('', include('dashboard.urls'))
   └─ All dashboard routes prefixed as per dashboard/urls.py
```

---

## 📈 Startup & Initialization Flow

### วิธีการ Setup & Run โปรเจกต์

```bash
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup project (run migrations + seed data)
python manage.py setup_project
   ↓ executes:
   [dashboard/management/commands/setup_project.py]
   ├─ Call: django.core.management.call_command('migrate')
   │   └─ [dashboard/migrations/] all .py files
   │       ├─ 0001_initial.py (create tables)
   │       ├─ 0002_remove_portfolioresult_plan_and_more.py
   │       ├─ ... (0003-0009)
   │       └─ Creates: Stock, User, UserProfile, UserPlan, etc.
   │
   └─ Call: django.core.management.call_command('seed_initial_data')
       [dashboard/management/commands/seed_initial_data.py]
       ├─ Create 8 stocks: ADVANC, AOT, BBL, CPALL, KBANK, PTT, SCB, TRUE
       └─ Create 2 DCA Presets: Balanced SET50 DCA, Conservative Growth

# 4. Run development server
python manage.py runserver
   ↓
Server starts on: http://127.0.0.1:8000

# 5. Access application
Dashboard: http://127.0.0.1:8000/dashboard/
Admin Panel: http://127.0.0.1:8000/admin/
Login: http://127.0.0.1:8000/
```

---

## 🎯 Summary: Key Takeaways

### 🏗️ Architecture Overview
- **Framework**: Django (MVT Pattern)
- **Database**: SQLite3
- **Async**: Celery (with fallback)
- **Frontend**: Django Templates (HTML)
- **External API**: Yahoo Finance (yfinance)

### 📊 Core Data Flow
1. User input → Views → Services → Optimizers → Database → Templates → Browser
2. Three parallel optimization algorithms on each dashboard load
3. Results cached in UserPlan and GAResultSnapshot

### 🔑 Main Components
- **7 Database Models**: Stock, User, UserProfile, UserPlan, DCAPreset, UserInvestmentRecord, GAResultSnapshot
- **10+ View Functions**: Covering Auth, Dashboard, Profile, Investment Records, GA History
- **3 Optimization Strategies**: GA (Primary), Mean-Variance, Equal-Weight
- **13+ Templates**: For different features and workflows

### 🌟 Special Features
- Genetic Algorithm with 50 generations for portfolio optimization
- DCA Projection with yearly breakdown
- Background task processing (Celery)
- GA History tracking with snapshots
- Profile management with language preference
- Admin panel for stock price updates

---

## 📚 File Structure Quick Reference

```
MyThesisProject/
├── manage.py ← Entry point
├── requirements.txt ← Dependencies
├── db.sqlite3 ← Database
├── dca_system/
│   ├── settings.py ← Configuration
│   ├── urls.py ← Main URL router
│   ├── wsgi.py ← Production WSGI
│   └── asgi.py ← Async ASGI
└── dashboard/
    ├── models.py ← 7 Data Models
    ├── views.py ← View logic (10+ functions)
    ├── urls.py ← App routing
    ├── services.py ← Business logic
    ├── tasks.py ← Background tasks
    ├── ga_optimizer.py ← GA algorithm (160 lines)
    ├── admin.py ← Admin panel
    ├── tests.py ← Tests
    ├── optimizers/ ← 3 optimizer strategies
    ├── management/commands/ ← CLI commands
    ├── migrations/ ← DB schema history
    ├── templates/dashboard/ ← 13 HTML templates
    └── static/dashboard/ ← CSS/JS
```

---

**สร้างวันที่**: 2024-09-01  
**เวอร์ชัน**: 1.0  
**ภาษา**: Thai (ไทย)
