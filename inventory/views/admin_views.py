"""Admin panel views following project patterns"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import os

from ..utils.decorators import super_admin_required, admin_required, super_admin_required_with_message, admin_required_with_message
from ..utils.helpers import paginate_queryset, log_user_action
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
from ..services.rbac_service import (
    UserProfileService, PermissionService, LoggingService
)
from ..forms.rbac_forms import UserCreateForm, UserUpdateForm, PermissionAssignmentForm
from ..models import UserProfile, LoginLog, ActionLog


@admin_required_with_message()
def admin_panel_view(request):
    """Main admin panel dashboard"""
    try:
        # Get statistics using service layer
        user_service = UserProfileService()
        permission_service = PermissionService()
        logging_service = LoggingService()
        
        # User statistics
        total_users = User.objects.count()
        active_users = user_service.get_active_users().count()
        admin_users = user_service.get_users_by_type('admin').count()
        normal_users = user_service.get_users_by_type('normal').count()
        # Count super admins (include Django superusers even without profiles)
        super_admin_users = User.objects.filter(
            Q(profile__user_type='super_admin', profile__is_active=True) | Q(is_superuser=True)
        ).distinct().count()
        
        # Recent activity
        recent_logins = logging_service.get_recent_logins(limit=10)
        recent_actions = logging_service.get_recent_actions(limit=10)
        
        # Database storage info
        storage_info = get_database_storage_info()
        
        context = {
            'title': 'لوحة الإدارة',
            'total_users': total_users,
            'active_users': active_users,
            'super_admin_users': super_admin_users,
            'admin_users': admin_users,
            'normal_users': normal_users,
            'recent_logins': recent_logins,
            'recent_actions': recent_actions,
            'storage_info': storage_info,
        }
        
        # Log admin panel access
        log_user_action(
            request.user, 
            'admin_panel_access', 
            description="دخول إلى لوحة الإدارة"
        )
        
        return render(request, 'inventory/admin/admin_panel.html', context)
        
    except Exception as e:
        messages.error(request, f'خطأ في تحميل لوحة الإدارة: {str(e)}')
        return redirect('dashboard')


@admin_required_with_message()
def user_management_view(request):
    """User management interface"""
    try:
        user_service = UserProfileService()
        
        # Get search and filter parameters
        search_query = request.GET.get('search', '')
        user_type_filter = request.GET.get('user_type', '')
        page_number = request.GET.get('page', 1)
        
        # Get users with profiles
        users = User.objects.select_related('profile').all()
        
        # Apply search filter
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Apply user type filter
        if user_type_filter:
            users = users.filter(profile__user_type=user_type_filter)
        
        # Order by creation date
        users = users.order_by('-date_joined')
        
        # Paginate results
        users_page = paginate_queryset(users, page_number, per_page=20)
        
        # Calculate statistics for all users (not filtered)
        total_users = User.objects.count()
        active_users = user_service.get_active_users().count()
        admin_users = user_service.get_users_by_type('admin').count()
        normal_users = user_service.get_users_by_type('normal').count()
        # Count super admins (include Django superusers even without profiles)
        super_admin_users = User.objects.filter(
            Q(profile__user_type='super_admin', profile__is_active=True) | Q(is_superuser=True)
        ).distinct().count()
        
        context = {
            'title': 'إدارة المستخدمين',
            'users_page': users_page,
            'search_query': search_query,
            'user_type_filter': user_type_filter,
            'user_type_choices': UserProfile.USER_TYPE_CHOICES,
            'total_users': total_users,
            'active_users': active_users,
            'super_admin_users': super_admin_users,
            'admin_users': admin_users,
            'normal_users': normal_users,
        }
        
        return render(request, 'inventory/admin/user_management.html', context)
        
    except Exception as e:
        messages.error(request, f'خطأ في تحميل إدارة المستخدمين: {str(e)}')
        return redirect('admin_panel')


@super_admin_required_with_message()
def user_create_view(request):
    """Create new user"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST, created_by=request.user)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'تم إنشاء المستخدم "{user.username}" بنجاح.')
                
                # Log user creation
                log_user_action(
                    request.user,
                    'user_create',
                    object_id=str(user.id),
                    description=f"إنشاء مستخدم جديد: {user.username}"
                )
                
                return redirect('user_management')
            except Exception as e:
                messages.error(request, f'خطأ في إنشاء المستخدم: {str(e)}')
    else:
        form = UserCreateForm()
    
    context = {
        'title': 'إضافة مستخدم جديد',
        'form': form,
    }
    return render(request, 'inventory/admin/user_form.html', context)


@super_admin_required_with_message()
def user_update_view(request, user_id):
    """Update user information"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            try:
                updated_user = form.save()
                messages.success(request, f'تم تحديث المستخدم "{updated_user.username}" بنجاح.')
                
                # Log user update
                log_user_action(
                    request.user,
                    'user_update',
                    object_id=str(user.id),
                    description=f"تحديث مستخدم: {user.username}"
                )
                
                return redirect('user_management')
            except Exception as e:
                messages.error(request, f'خطأ في تحديث المستخدم: {str(e)}')
    else:
        form = UserUpdateForm(instance=user)
    
    context = {
        'title': f'تعديل المستخدم: {user.username}',
        'form': form,
        'user': user,
    }
    return render(request, 'inventory/admin/user_form.html', context)


@super_admin_required_with_message()
def user_delete_view(request, user_id):
    """Delete user (soft delete)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            # Soft delete by deactivating profile
            user_service = UserProfileService()
            profile = user_service.get_user_profile(user)
            profile.is_active = False
            profile.save()
            
            messages.success(request, f'تم حذف المستخدم "{user.username}" بنجاح.')
            
            # Log user deletion
            log_user_action(
                request.user,
                'user_delete',
                object_id=str(user.id),
                description=f"حذف مستخدم: {user.username}"
            )
            
            return redirect('user_management')
        except Exception as e:
            messages.error(request, f'خطأ في حذف المستخدم: {str(e)}')
    
    context = {
        'title': f'حذف المستخدم: {user.username}',
        'user': user,
    }
    return render(request, 'inventory/admin/user_confirm_delete.html', context)


@super_admin_required_with_message()
def permission_management_view(request):
    """Permission management interface"""
    try:
        permission_service = PermissionService()
        
        # Get all users with profiles
        users = User.objects.select_related('profile').filter(
            profile__is_active=True
        ).order_by('username')
        
        # Get search parameter
        search_query = request.GET.get('search', '')
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Paginate results
        page_number = request.GET.get('page', 1)
        users_page = paginate_queryset(users, page_number, per_page=20)
        
        context = {
            'title': 'إدارة الصلاحيات',
            'users_page': users_page,
            'search_query': search_query,
            'modules': ['cars', 'equipment', 'generic_tables'],
            'permissions': ['create', 'read', 'update', 'delete'],
        }
        
        return render(request, 'inventory/admin/permission_management.html', context)
        
    except Exception as e:
        messages.error(request, f'خطأ في تحميل إدارة الصلاحيات: {str(e)}')
        return redirect('admin_panel')


@super_admin_required_with_message()
def user_permissions_view(request, user_id):
    """View and edit user permissions"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = PermissionAssignmentForm(user, request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'تم تحديث صلاحيات المستخدم "{user.username}" بنجاح.')
                
                # Log permission update
                log_user_action(
                    request.user,
                    'permission_update',
                    object_id=str(user.id),
                    description=f"تحديث صلاحيات مستخدم: {user.username}"
                )
                
                return redirect('permission_management')
            except Exception as e:
                messages.error(request, f'خطأ في تحديث الصلاحيات: {str(e)}')
    else:
        form = PermissionAssignmentForm(user)
    
    context = {
        'title': f'صلاحيات المستخدم: {user.username}',
        'form': form,
        'user': user,
    }
    return render(request, 'inventory/admin/user_permissions.html', context)


@admin_required_with_message()
def login_logs_view(request):
    """Display login history"""
    try:
        logging_service = LoggingService()
        
        # Get filter parameters
        search_query = request.GET.get('search', '')
        success_filter = request.GET.get('success', '')
        role_filter = request.GET.get('role', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')
        page_number = request.GET.get('page', 1)
        try:
            per_page = int(request.GET.get('per_page', 25))
        except (ValueError, TypeError):
            per_page = 25
        
        # Validate per_page to prevent abuse
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
        
        # Base queryset: avoid slicing before ordering to prevent errors when reordering
        login_logs = LoginLog.objects.select_related('user').all()
        
        # Apply search filter
        if search_query:
            login_logs = login_logs.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(ip_address__icontains=search_query)
            )
        
        # Apply success filter
        if success_filter != '':
            login_logs = login_logs.filter(success=success_filter == 'true')

        # Apply role filter (via user profile)
        if role_filter:
            login_logs = login_logs.filter(user__profile__user_type=role_filter)

        # Apply date range filter (inclusive)
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                login_logs = login_logs.filter(login_time__date__gte=start_date.date())
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                login_logs = login_logs.filter(login_time__date__lte=end_date.date())
            except ValueError:
                pass
        
        # Order by login time
        login_logs = login_logs.order_by('-login_time')
        
        # Paginate results
        logs_page = paginate_queryset(login_logs, page_number, per_page=per_page)
        
        context = {
            'title': 'سجل تسجيل الدخول',
            'logs_page': logs_page,
            'search_query': search_query,
            'success_filter': success_filter,
            'role_filter': role_filter,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'role_choices': getattr(UserProfile, 'USER_TYPE_CHOICES', []),
            'per_page': per_page,
        }
        
        return render(request, 'inventory/admin/login_logs.html', context)
        
    except Exception as e:
        messages.error(request, f'خطأ في تحميل سجل تسجيل الدخول: {str(e)}')
        return redirect('admin_panel')


@admin_required_with_message()
def action_logs_view(request):
    """Display system action logs"""
    try:
        logging_service = LoggingService()
        
        # Get filter parameters
        search_query = request.GET.get('search', '')
        action_type_filter = request.GET.get('action_type', '')
        module_filter = request.GET.get('module', '')
        role_filter = request.GET.get('role', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')
        page_number = request.GET.get('page', 1)
        try:
            per_page = int(request.GET.get('per_page', 25))
        except (ValueError, TypeError):
            per_page = 25
        
        # Validate per_page to prevent abuse
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
        
        # Base queryset: avoid slicing before ordering to prevent errors when reordering
        action_logs = ActionLog.objects.select_related('user').all()
        
        # Apply search filter
        if search_query:
            action_logs = action_logs.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(action_type__icontains=search_query)
            )
        
        # Apply action type filter
        if action_type_filter:
            action_logs = action_logs.filter(action_type=action_type_filter)
        
        # Apply module filter
        if module_filter:
            action_logs = action_logs.filter(module_name=module_filter)

        # Apply role filter (via user profile)
        if role_filter:
            action_logs = action_logs.filter(user__profile__user_type=role_filter)

        # Apply date range filter (inclusive)
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                action_logs = action_logs.filter(timestamp__date__gte=start_date.date())
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                action_logs = action_logs.filter(timestamp__date__lte=end_date.date())
            except ValueError:
                pass
        
        # Order by timestamp
        action_logs = action_logs.order_by('-timestamp')
        
        # Paginate results
        logs_page = paginate_queryset(action_logs, page_number, per_page=per_page)
        
        # Get action type choices (from model) and unique modules for filter dropdowns
        action_type_choices = getattr(ActionLog, 'ACTION_CHOICES', [])
        modules = (
            ActionLog.objects.order_by()
            .values_list('module_name', flat=True)
            .distinct()
        )
        modules = [m for m in modules if m]
        
        context = {
            'title': 'سجل العمليات',
            'logs_page': logs_page,
            'search_query': search_query,
            'action_type_filter': action_type_filter,
            'module_filter': module_filter,
            'action_type_choices': action_type_choices,
            'modules': modules,
            'role_filter': role_filter,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'role_choices': getattr(UserProfile, 'USER_TYPE_CHOICES', []),
            'per_page': per_page,
        }
        
        return render(request, 'inventory/admin/action_logs.html', context)
        
    except Exception as e:
        messages.error(request, f'خطأ في تحميل سجل العمليات: {str(e)}')
        return redirect('admin_panel')


@admin_required_with_message()
def login_logs_export(request):
    """Export login logs to CSV with optional filters and date range"""
    try:
        search_query = request.GET.get('search', '')
        success_filter = request.GET.get('success', '')
        role_filter = request.GET.get('role', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')

        logs = LoginLog.objects.select_related('user').all()

        if search_query:
            logs = logs.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(ip_address__icontains=search_query)
            )
        if success_filter != '':
            logs = logs.filter(success=success_filter == 'true')
        if role_filter:
            logs = logs.filter(user__profile__user_type=role_filter)
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                logs = logs.filter(login_time__date__gte=start_date)
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                logs = logs.filter(login_time__date__lte=end_date)
            except ValueError:
                pass

        logs = logs.order_by('-login_time')

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = 'سجل_تسجيل_الدخول.csv'
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename}"

        # Write UTF-8 BOM for Excel compatibility with Arabic
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow(['المستخدم', 'اسم المستخدم', 'عنوان IP', 'المتصفح', 'نجاح', 'وقت الدخول', 'وقت الخروج', 'الدور'])
        for l in logs:
            role = getattr(getattr(l.user, 'profile', None), 'user_type', '')
            writer.writerow([
                l.user.get_full_name() or '',
                l.user.username,
                l.ip_address,
                (l.user_agent or '')[:250],
                'نجح' if l.success else 'فشل',
                l.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                l.logout_time.strftime('%Y-%m-%d %H:%M:%S') if l.logout_time else '',
                role,
            ])

        return response
    except Exception as e:
        messages.error(request, f'خطأ في تصدير سجل تسجيل الدخول: {str(e)}')
        return redirect('login_logs')


@admin_required_with_message()
def action_logs_export(request):
    """Export action logs to CSV with optional filters and date range"""
    try:
        search_query = request.GET.get('search', '')
        action_type_filter = request.GET.get('action_type', '')
        module_filter = request.GET.get('module', '')
        role_filter = request.GET.get('role', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')

        logs = ActionLog.objects.select_related('user').all()

        if search_query:
            logs = logs.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(action_type__icontains=search_query)
            )
        if action_type_filter:
            logs = logs.filter(action_type=action_type_filter)
        if module_filter:
            logs = logs.filter(module_name=module_filter)
        if role_filter:
            logs = logs.filter(user__profile__user_type=role_filter)
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                logs = logs.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                logs = logs.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass

        logs = logs.order_by('-timestamp')

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = 'سجل_العمليات.csv'
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename}"

        # Write UTF-8 BOM for Excel compatibility with Arabic
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow(['المستخدم', 'اسم المستخدم', 'نوع العملية', 'الوحدة', 'الوصف', 'عنوان IP', 'الوقت', 'الدور'])
        for l in logs:
            role = getattr(getattr(l.user, 'profile', None), 'user_type', '')
            writer.writerow([
                l.user.get_full_name() or '',
                l.user.username,
                l.get_action_type_display() if hasattr(l, 'get_action_type_display') else l.action_type,
                l.module_name or '',
                (l.description or '')[:250],
                l.ip_address or '',
                l.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                role,
            ])

        return response
    except Exception as e:
        messages.error(request, f'خطأ في تصدير سجل العمليات: {str(e)}')
        return redirect('action_logs')


@admin_required_with_message()
def database_storage_view(request):
    """Database storage monitoring"""
    try:
        storage_info = get_database_storage_info()
        
        context = {
            'title': 'مراقب قاعدة البيانات',
            'storage_info': storage_info,
        }
        
        return render(request, 'inventory/admin/database_storage.html', context)
        
    except Exception as e:
        messages.error(request, f'خطأ في تحميل مراقب قاعدة البيانات: {str(e)}')
        return redirect('admin_panel')


def get_database_storage_info():
    """Get database storage information"""
    try:
        with connection.cursor() as cursor:
            # Get database size
            cursor.execute("""
                SELECT pg_database_size(current_database()) as size_bytes
            """)
            db_size_bytes = cursor.fetchone()[0] or 0
            # Pretty string (GB with 2 decimals)
            db_size_gb = round(db_size_bytes / (1024 ** 3), 2) if db_size_bytes else 0.0
            db_size = f"{db_size_gb:.2f} GB"
            
            # Get table sizes
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            table_sizes = cursor.fetchall()
            
            # Get media directory size
            media_size = 0
            media_size_pretty = "0 B"
            if hasattr(settings, 'MEDIA_ROOT') and os.path.exists(settings.MEDIA_ROOT):
                for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                    for file in files:
                        try:
                            media_size += os.path.getsize(os.path.join(root, file))
                        except OSError:
                            pass
                
                # Convert to human readable format
                if media_size > 0:
                    media_tmp = float(media_size)
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if media_tmp < 1024.0:
                            media_size_pretty = f"{media_tmp:.1f} {unit}"
                            break
                        media_tmp /= 1024.0
            media_size_gb = round(media_size / (1024 ** 3), 2) if media_size else 0.0
            
            return {
                'database_size': db_size,
                'database_size_bytes': db_size_bytes,
                'database_size_gb': db_size_gb,
                'table_sizes': table_sizes,
                'media_size': media_size_pretty,
                'media_size_bytes': media_size,
                'media_size_gb': media_size_gb,
            }
            
    except Exception as e:
        return {
            'database_size': 'غير متاح',
            'table_sizes': [],
            'media_size': 'غير متاح',
            'media_size_bytes': 0,
            'error': str(e)
        }


@admin_required_with_message()
def storage_data_api(request):
    """API endpoint for storage data"""
    try:
        storage_info = get_database_storage_info()
        
        # Capacity and quotas (override via settings if provided)
        capacity_gb = getattr(settings, 'STORAGE_CAPACITY_LIMIT_GB', 20)
        db_quota_gb = getattr(settings, 'DATABASE_QUOTA_GB', 5)

        capacity_bytes = int(capacity_gb * (1024 ** 3))
        db_quota_bytes = int(db_quota_gb * (1024 ** 3))

        db_bytes = int(storage_info.get('database_size_bytes') or 0)
        media_bytes = int(storage_info.get('media_size_bytes') or 0)
        total_size_bytes = db_bytes + media_bytes

        percentage = 0.0
        if capacity_bytes > 0:
            percentage = min((total_size_bytes / capacity_bytes) * 100.0, 100.0)
        
        total_gb = round(total_size_bytes / (1024 ** 3), 2)
        db_gb = round(db_bytes / (1024 ** 3), 2)
        media_gb = round(media_bytes / (1024 ** 3), 2)
        db_quota_used_pct = round((db_bytes / db_quota_bytes) * 100.0, 2) if db_quota_bytes > 0 else 0.0
        
        return JsonResponse({
            'success': True,
            'percentage': round(percentage, 1),
            'capacity_gb': float(capacity_gb),
            'capacity_bytes': capacity_bytes,
            'total_bytes': total_size_bytes,
            'total_gb': total_gb,
            'database_bytes': db_bytes,
            'database_gb': db_gb,
            'media_bytes': media_bytes,
            'media_gb': media_gb,
            'database_quota_gb': float(db_quota_gb),
            'database_quota_bytes': db_quota_bytes,
            'database_quota_used_pct': db_quota_used_pct,
            'database_size_pretty': storage_info.get('database_size', 'غير متاح'),
            'media_size_pretty': storage_info.get('media_size', '0 B'),
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        })
