#!/usr/bin/env python
"""Quick script to check user permissions"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fleet_management.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import UserProfile, UserPermission, ModulePermission

email = 'user1@fleet.com'

try:
    user = User.objects.get(email=email)
    print(f"\n=== User Information ===")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Is Superuser: {user.is_superuser}")
    print(f"Is Active: {user.is_active}")
    
    # Check user profile
    try:
        profile = user.profile
        print(f"\n=== User Profile ===")
        print(f"User Type: {profile.user_type}")
        print(f"Profile Active: {profile.is_active}")
        
        user_type = profile.user_type
        
        if user_type == 'super_admin':
            print(f"\n=== PERMISSIONS: SUPER ADMIN ===")
            print("This user has ALL permissions automatically:")
            print("  - All modules: create, read, update, delete")
            print("  - Can manage all users")
            print("  - Full admin panel access")
            
        elif user_type == 'admin':
            print(f"\n=== PERMISSIONS: ADMIN ===")
            print("This user has ALL permissions automatically:")
            print("  - All modules: create, read, update, delete")
            print("  - Can manage normal users")
            print("  - Admin panel access")
            
        else:
            # Normal user - check specific permissions
            print(f"\n=== User Permissions (Normal User) ===")
            
            modules = ['cars', 'equipment', 'generic_tables']
            permissions = ['create', 'read', 'update', 'delete']
            
            # Get user's granted permissions
            user_permissions = UserPermission.objects.filter(
                user=user,
                granted=True
            ).select_related('module_permission')
            
            # Create a map of granted permissions
            granted_map = {}
            for up in user_permissions:
                module = up.module_permission.module_name
                perm_type = up.module_permission.permission_type
                if module not in granted_map:
                    granted_map[module] = []
                granted_map[module].append(perm_type)
            
            # Display permissions by module
            has_any_permissions = False
            for module in modules:
                module_perms = granted_map.get(module, [])
                if module_perms:
                    has_any_permissions = True
                    print(f"\n{module.upper()}:")
                    for perm in permissions:
                        status = "GRANTED" if perm in module_perms else "DENIED"
                        print(f"  {perm:10} : {status}")
                else:
                    print(f"\n{module.upper()}:")
                    print("  No permissions granted")
            
            if not has_any_permissions:
                print("\nWARNING: This user has NO permissions granted.")
                print("They will not be able to access any modules.")
            
            # Show all permission records
            all_user_permissions = UserPermission.objects.filter(
                user=user
            ).select_related('module_permission')
            
            if all_user_permissions.exists():
                print(f"\n=== All Permission Records ===")
                for up in all_user_permissions:
                    status = "GRANTED" if up.granted else "DENIED"
                    print(f"{up.module_permission.module_name:20} - {up.module_permission.permission_type:10} : {status}")
            else:
                print("\nNo permission records found for this user.")
                
    except UserProfile.DoesNotExist:
        print("\n=== User Profile ===")
        print("No user profile found.")
        if user.is_superuser:
            print("User is Django superuser - has all permissions")
        
except User.DoesNotExist:
    print(f'User with email "{email}" not found.')

print("\n")

