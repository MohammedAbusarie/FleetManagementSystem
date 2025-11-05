# Logo Troubleshooting Guide

## Issue: Logo Not Showing

### Step 1: Verify File Location
Ensure the logo file is at: `static/images/company_logo.svg`

### Step 2: Collect Static Files
Run the following command to collect static files:
```bash
python manage.py collectstatic --noinput
```

### Step 3: Check Development Server
If using Django development server:
1. Make sure `DEBUG = True` in settings.py
2. Restart the development server
3. Check browser console for 404 errors

### Step 4: Verify URL Configuration
Check that `fleet_management/urls.py` includes static file serving in DEBUG mode.

### Step 5: Browser Cache
Clear your browser cache or do a hard refresh:
- Windows/Linux: `Ctrl + Shift + R` or `Ctrl + F5`
- Mac: `Cmd + Shift + R`

### Step 6: Check File Path
The logo should be accessible at: `/static/images/company_logo.svg`

### Step 7: Verify File Permissions
Ensure the file has read permissions.

### Debug: Check Static File URL
Add this to your template temporarily to debug:
```django
{% load static %}
<!-- Debug: Logo URL -->
<p>Logo URL: {% static 'images/company_logo.svg' %}</p>
<img src="{% static 'images/company_logo.svg' %}" alt="Logo">
```

### Common Issues:
1. **File name mismatch**: Ensure filename is exactly `company_logo.svg`
2. **Static files not collected**: Run `collectstatic` command
3. **DEBUG mode**: Static files only auto-served when DEBUG=True
4. **Browser cache**: Clear cache and hard refresh

