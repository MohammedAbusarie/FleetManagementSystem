# RBAC Migration Scripts Documentation

This document describes the management commands available for setting up and managing the RBAC (Role-Based Access Control) system.

## Overview

The RBAC system provides granular permission control for the Fleet Management System. It includes user types (Super Admin, Admin, Normal User), module-specific permissions, and comprehensive system logging.

## Available Commands

### 1. Complete RBAC Setup
```bash
python manage.py setup_rbac_complete --create-super-admin
```

**Purpose**: Sets up the complete RBAC system in one command.

**Options**:
- `--skip-migration`: Skip database migration
- `--skip-permissions`: Skip permission setup
- `--skip-user-migration`: Skip user migration
- `--create-super-admin`: Create initial super admin user
- `--super-admin-username`: Username for super admin (default: admin)
- `--super-admin-email`: Email for super admin (default: admin@example.com)
- `--super-admin-password`: Password for super admin (default: admin123)

**Example**:
```bash
python manage.py setup_rbac_complete --create-super-admin --super-admin-username=myadmin --super-admin-email=admin@mycompany.com --super-admin-password=SecurePass123
```

### 2. Database Migration
```bash
python manage.py migrate inventory
```

**Purpose**: Applies the RBAC database schema changes.

**Note**: This is automatically handled by `setup_rbac_complete` unless `--skip-migration` is used.

### 3. Setup Default Permissions
```bash
python manage.py setup_rbac_permissions
```

**Purpose**: Creates default module permissions for cars, equipment, and generic_tables.

**What it creates**:
- cars: create, read, update, delete
- equipment: create, read, update, delete
- generic_tables: create, read, update, delete

### 4. Migrate Existing Users
```bash
python manage.py migrate_users_to_rbac --dry-run
python manage.py migrate_users_to_rbac --force
```

**Purpose**: Migrates existing users to the RBAC system.

**Options**:
- `--dry-run`: Show what would be done without making changes
- `--force`: Force migration even if profiles already exist

**Migration Logic**:
- `is_superuser=True` → `super_admin`
- Member of 'Admin' group → `admin`
- All other users → `normal`

### 5. Create Super Admin User
```bash
python manage.py setup_super_admin --username=admin --email=admin@example.com --password=admin123
```

**Purpose**: Creates an initial super admin user for system access.

**Options**:
- `--username`: Username (default: admin)
- `--email`: Email address (default: admin@example.com)
- `--password`: Password (default: admin123)
- `--first-name`: First name (default: Super)
- `--last-name`: Last name (default: Admin)
- `--force`: Force creation even if user exists

### 6. Clean Up Old Logs
```bash
python manage.py cleanup_old_logs --days=90 --dry-run
python manage.py cleanup_old_logs --days=30
```

**Purpose**: Removes old system logs to free up database space.

**Options**:
- `--days`: Delete logs older than this many days (default: 90)
- `--dry-run`: Show what would be deleted without making changes
- `--keep-login-logs`: Keep login logs (only delete action logs)
- `--keep-action-logs`: Keep action logs (only delete login logs)

### 7. Rollback RBAC System
```bash
python manage.py rollback_rbac_system --dry-run
python manage.py rollback_rbac_system --confirm --keep-logs
```

**Purpose**: Rolls back the RBAC system to the legacy Admin group system.

**Options**:
- `--dry-run`: Show what would be done without making changes
- `--keep-logs`: Keep system logs (do not delete them)
- `--confirm`: Confirm rollback operation (required for actual rollback)

**Warning**: This command will delete all RBAC data and revert to the legacy system.

## Migration Workflow

### For New Installations
1. Run the complete setup:
```bash
python manage.py setup_rbac_complete --create-super-admin
```

### For Existing Systems
1. **Backup your database first!**
2. Run the complete setup:
```bash
python manage.py setup_rbac_complete --create-super-admin
```
3. Verify user migration:
```bash
python manage.py migrate_users_to_rbac --dry-run
```
4. Test the system with existing users

### For Development/Testing
1. Create a test super admin:
```bash
python manage.py setup_super_admin --username=testadmin --password=test123
```
2. Set up permissions:
```bash
python manage.py setup_rbac_permissions
```

## Troubleshooting

### Common Issues

#### 1. Migration Fails
- Check database connectivity
- Ensure all previous migrations are applied
- Check for conflicting data

#### 2. User Migration Issues
- Use `--dry-run` to see what would happen
- Use `--force` to overwrite existing profiles
- Check for duplicate usernames

#### 3. Permission Issues
- Verify module permissions are created
- Check user profile creation
- Ensure proper user type assignment

### Rollback Procedure

If you need to rollback the RBAC system:

1. **Backup your database first!**
2. Run rollback with dry-run:
```bash
python manage.py rollback_rbac_system --dry-run
```
3. If satisfied, run actual rollback:
```bash
python manage.py rollback_rbac_system --confirm
```

## Maintenance Commands

### Regular Maintenance
- **Clean old logs monthly**:
```bash
python manage.py cleanup_old_logs --days=90
```

- **Check user statistics**:
```bash
python manage.py shell
>>> from inventory.models import UserProfile
>>> UserProfile.objects.count()
```

### Monitoring
- **Check system logs**:
```bash
python manage.py shell
>>> from inventory.models import LoginLog, ActionLog
>>> LoginLog.objects.count()
>>> ActionLog.objects.count()
```

## Security Considerations

1. **Change default passwords**: Always change default passwords after setup
2. **Regular backups**: Backup database before any migration operations
3. **Test rollback**: Test rollback procedures in development environment
4. **Monitor logs**: Regularly review system logs for security issues
5. **User permissions**: Regularly review and update user permissions

## Support

For issues with migration scripts:
1. Check the logs for error messages
2. Use `--dry-run` options to test changes
3. Verify database connectivity and permissions
4. Check Django version compatibility

---

**Last Updated**: Created with RBAC system implementation  
**Version**: 1.0.0
