# Static Images Directory

This directory contains static images used throughout the application.

## Logo Placement

Place your company logo SVG file here with the name:
- `logo.svg` - Main company logo

After placing the logo file, reference it in templates using:
```django
{% load static %}
<img src="{% static 'images/logo.svg' %}" alt="Company Logo">
```

## Directory Structure

```
static/
└── images/
    └── logo.svg    # Company logo
```

## Deployment

After adding files here, run:
```bash
python manage.py collectstatic
```

This will copy the files to the `staticfiles/` directory for production use.

