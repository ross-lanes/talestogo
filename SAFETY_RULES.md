# TALES Production Database Safety Rules

**CRITICAL: READ BEFORE ANY PRODUCTION DATABASE OPERATIONS**

## 🚨 NEVER DO THESE ON PRODUCTION FROM LOCALHOST

### 1. Database Migrations
```bash
# ❌ NEVER run this on production from localhost
alembic upgrade head

# ✅ Instead: Let Render deployment handle migrations automatically
# Or run migrations directly on Render via SSH/shell
```

**Why?**
- Migrations can break production if they fail mid-way
- Render deployment ensures migrations run in controlled environment
- Failed migrations from localhost are hard to recover from

### 2. Database Transactions - Testing on Production

When you need to test queries on production database, ALWAYS use transactions:

```python
# ✅ SAFE: Use transactions for testing
from app.database import SessionLocal

db = SessionLocal()

# Start transaction
db.begin()

# Make your test changes
user = db.query(User).filter_by(email="test@example.com").first()
user.is_active = False  # Test change
print(user.is_active)  # See the change

# CRITICAL: Roll back instead of committing
db.rollback()  # ← Undoes ALL changes since db.begin()
db.close()

# Database is unchanged - you just tested safely!
```

```python
# ❌ DANGEROUS: Without transaction
db = SessionLocal()

user = db.query(User).filter_by(email="test@example.com").first()
user.is_active = False
db.commit()  # ← PERMANENT change to production!

# Can't undo this easily!
```

**What is a transaction?**
- Like a "test mode" for database changes
- `db.begin()` = Start test mode
- `db.commit()` = Make changes permanent
- `db.rollback()` = Undo everything back to db.begin()

### 3. Bulk Data Changes
```python
# ❌ NEVER do bulk updates without transaction
db.query(User).filter(...).update({"is_active": False})
db.commit()

# ✅ SAFE: Use transaction + verify first
db.begin()
users_to_change = db.query(User).filter(...).all()
print(f"About to modify {len(users_to_change)} users:")
for u in users_to_change:
    print(f"  - {u.email}")

# Verify this is correct
response = input("Continue? (yes/no): ")
if response == "yes":
    db.query(User).filter(...).update({"is_active": False})
    db.commit()
else:
    db.rollback()
```

---

## ✅ SAFE Operations on Production

### Read-Only Queries (Always Safe)
```python
# ✅ These are always safe - they don't change data
users = db.query(User).all()
user_count = db.query(User).count()
brands = db.query(BrandInfo).filter_by(user_id=15).all()
```

### Backups Before Changes
```bash
# ✅ Always backup before making changes
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

---

## 🔒 Production Database Connection

### Current Production Database URL
```
# Set via DATABASE_URL environment variable - see .env file
```

### Connecting Localhost to Production

**Temporary connection (for quick checks):**
```bash
# 1. Backup your .env
cp .env .env.backup

# 2. Update DATABASE_URL in .env to production URL
# DATABASE_URL=postgresql://tales_3bh3_user:...

# 3. Restart your local server

# 4. When done, restore
cp .env.backup .env
```

**For scripts (recommended):**
```python
# Use DATABASE_URL environment variable
import os
PROD_DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(PROD_DB_URL)
SessionLocal = sessionmaker(bind=engine)
```

---

## 📦 Automatic Backup Strategy

### Option 1: Render Built-in Backups
- Render PostgreSQL plans include automatic daily backups
- Can restore from any backup point
- No code needed

### Option 2: Custom Backup Script
See `scripts/backup_database.py` for automated backups to:
- Local storage
- AWS S3
- Google Cloud Storage

### Option 3: GitHub Actions (Recommended)
- Automated daily backups via `.github/workflows/database-backup.yml`
- Runs at 2 AM UTC daily
- Stores in S3 with 30-day retention

---

## 🎯 Quick Reference

| Action | Safe? | Notes |
|--------|-------|-------|
| Read queries | ✅ Yes | Always safe |
| Update with transaction | ✅ Yes | Must use `db.begin()` and `db.rollback()` for testing |
| Update without transaction | ❌ No | Permanent changes! |
| `alembic upgrade head` | ❌ NEVER | Only on Render deployment |
| Backup before changes | ✅ Always | Use `pg_dump` first |
| Delete operations | ⚠️ Caution | Always use transaction + verify |

---

## 🚑 Emergency Recovery

If you accidentally modify production:

```bash
# 1. Stop immediately - don't commit more changes

# 2. Check if you have a recent backup
ls -lh backups/

# 3. Restore from backup
psql $DATABASE_URL < backup_YYYYMMDD.sql

# 4. Verify restoration worked
python check_production_users.py
```

---

## 📝 Testing Checklist

Before running ANY script on production:

- [ ] Created a backup
- [ ] Using transactions (`db.begin()` / `db.rollback()`)
- [ ] Tested on local database first
- [ ] Read-only operations? (If yes, skip transaction)
- [ ] Write operations? (Must use transaction)
- [ ] Verified the changes before committing
- [ ] Have rollback plan ready

---

**Last Updated:** 2025-11-15
**Owner:** Rachel Kremen
**Critical:** Review this document before ANY production database operations
