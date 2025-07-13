# Deployment Wheel Building Error Analysis

## Problem Identified

The "Getting requirements to build wheel: started" error occurs due to **dependency version conflicts** between your `requirements.txt` and `pyproject.toml` files. This creates confusion for pip during the wheel building process.

## Root Causes

### 1. **Version Conflicts Between Files**

Your project has conflicting dependency versions:

| Package | requirements.txt | pyproject.toml | Issue |
|---------|------------------|----------------|--------|
| Flask | 3.0.2 | >=3.1.1 | Version mismatch |
| gunicorn | 21.2.0 | >=23.0.0 | Major version jump |
| psycopg2-binary | 2.9.9 | >=2.9.10 | Minor version conflict |
| Pillow | 10.2.0 | >=11.2.1 | Major version jump |
| SQLAlchemy | 2.0.27 | >=2.0.41 | Minor version conflict |
| Werkzeug | 3.0.1 | >=3.1.3 | Minor version conflict |

### 2. **Missing Dependencies**

`pyproject.toml` specifies dependencies not in `requirements.txt`:
- `wtforms>=3.2.1`
- `apscheduler>=3.11.0`
- `flask-dance>=7.1.0`
- `pyjwt>=2.10.1`

### 3. **Inconsistent Dependency Management**

Having both `requirements.txt` and `pyproject.toml` with different specifications confuses dependency resolution.

## Solutions

### Option 1: Use requirements.txt Only (Recommended for Vercel)

1. **Remove pyproject.toml** (or rename it to keep as backup)
2. **Update requirements.txt** with compatible versions
3. **Add missing dependencies**

### Option 2: Use pyproject.toml Only (Modern Python approach)

1. **Remove requirements.txt**
2. **Update Vercel configuration** to use pyproject.toml
3. **Test dependency resolution**

### Option 3: Synchronize Both Files

1. **Align versions** between both files
2. **Use requirements.txt** for production dependencies
3. **Use pyproject.toml** for development setup

## Recommended Fix (Option 1)

### Step 1: Update requirements.txt

```
Flask==3.1.1
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.2
psycopg2-binary==2.9.10
SQLAlchemy==2.0.41
Werkzeug==3.1.3
python-dotenv==1.0.1
requests==2.32.3
gunicorn==23.0.0
email-validator==2.2.0
Flask-Migrate==4.0.5
Flask-Session==0.6.0
Pillow==11.2.1
oauthlib==3.2.2
WTForms==3.2.1
APScheduler==3.11.0
Flask-Dance==7.1.0
PyJWT==2.10.1
```

### Step 2: Remove or rename pyproject.toml

```bash
mv pyproject.toml pyproject.toml.backup
```

### Step 3: Test locally

```bash
pip install -r requirements.txt
python main.py
```

## Additional Considerations

### For Vercel Deployment:
- Vercel prefers `requirements.txt` for Python projects
- Ensure `runtime.txt` specifies a compatible Python version (✓ you have 3.11.10)
- Your `main.py` entry point is correctly configured

### For Future Development:
- Choose one dependency management approach
- Use `pip freeze > requirements.txt` to capture exact working versions
- Consider using `pip-tools` for dependency management

## Quick Test Command

After applying the fix, test dependency resolution:

```bash
pip install --dry-run -r requirements.txt
```

This will show if there are any remaining conflicts without actually installing packages.