"""Logging-related business logic"""
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .base import BaseService
from ..models import LoginLog, ActionLog
from ..utils.helpers import get_client_ip, get_user_agent


class LoggingService(BaseService):
    """Service for logging operations"""
    model = ActionLog

    def log_login(self, user, request, success=True):
        """
        Log user login attempt
        
        Args:
            user: User instance (None for failed login)
            request: HTTP request object
            success: Whether login was successful
            
        Returns:
            LoginLog: Created login log entry
        """
        try:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            
            login_log = LoginLog.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            return login_log
            
        except Exception as e:
            return None

    def log_logout(self, user, request):
        """
        Log user logout
        
        Args:
            user: User instance
            request: HTTP request object
            
        Returns:
            LoginLog: Updated login log entry
        """
        try:
            # Find the most recent login log without logout time
            login_log = LoginLog.objects.filter(
                user=user,
                logout_time__isnull=True
            ).order_by('-login_time').first()
            
            if login_log:
                login_log.logout_time = timezone.now()
                login_log.save()
                return login_log
            
            return None
            
        except Exception as e:
            return None

    def log_action(self, user, action_type, module_name=None, object_id=None, description="", request=None):
        """
        Log user action
        
        Args:
            user: User instance
            action_type: Type of action
            module_name: Module name
            object_id: Object ID
            description: Action description
            request: HTTP request object
            
        Returns:
            ActionLog: Created action log entry
        """
        try:
            ip_address = None
            if request:
                ip_address = get_client_ip(request)
            
            action_log = ActionLog.objects.create(
                user=user,
                action_type=action_type,
                module_name=module_name,
                object_id=object_id,
                description=description,
                ip_address=ip_address
            )
            
            return action_log
            
        except Exception as e:
            return None

    def get_user_login_history(self, user, limit=50):
        """
        Get user login history
        
        Args:
            user: User instance
            limit: Number of records to return
            
        Returns:
            QuerySet: Login history
        """
        try:
            return LoginLog.objects.filter(user=user).order_by('-login_time')[:limit]
        except Exception:
            return LoginLog.objects.none()

    def get_user_action_history(self, user, limit=50):
        """
        Get user action history
        
        Args:
            user: User instance
            limit: Number of records to return
            
        Returns:
            QuerySet: Action history
        """
        try:
            return ActionLog.objects.filter(user=user).order_by('-timestamp')[:limit]
        except Exception:
            return ActionLog.objects.none()

    def get_recent_logins(self, limit=100, days=30):
        """
        Get recent login attempts
        
        Args:
            limit: Number of records to return
            days: Number of days to look back
            
        Returns:
            QuerySet: Recent login logs
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            return LoginLog.objects.filter(
                login_time__gte=cutoff_date
            ).select_related('user').order_by('-login_time')[:limit]
        except Exception:
            return LoginLog.objects.none()

    def get_recent_actions(self, limit=100, days=30):
        """
        Get recent system actions
        
        Args:
            limit: Number of records to return
            days: Number of days to look back
            
        Returns:
            QuerySet: Recent action logs
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            return ActionLog.objects.filter(
                timestamp__gte=cutoff_date
            ).select_related('user').order_by('-timestamp')[:limit]
        except Exception:
            return ActionLog.objects.none()

    def get_login_statistics(self, days=30):
        """
        Get login statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict: Login statistics
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            total_logins = LoginLog.objects.filter(login_time__gte=cutoff_date).count()
            successful_logins = LoginLog.objects.filter(
                login_time__gte=cutoff_date, success=True
            ).count()
            failed_logins = LoginLog.objects.filter(
                login_time__gte=cutoff_date, success=False
            ).count()
            
            unique_users = LoginLog.objects.filter(
                login_time__gte=cutoff_date, success=True
            ).values('user').distinct().count()
            
            return {
                'total_logins': total_logins,
                'successful_logins': successful_logins,
                'failed_logins': failed_logins,
                'unique_users': unique_users,
                'success_rate': (successful_logins / total_logins * 100) if total_logins > 0 else 0
            }
            
        except Exception:
            return {
                'total_logins': 0,
                'successful_logins': 0,
                'failed_logins': 0,
                'unique_users': 0,
                'success_rate': 0
            }

    def get_action_statistics(self, days=30):
        """
        Get action statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict: Action statistics
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            total_actions = ActionLog.objects.filter(timestamp__gte=cutoff_date).count()
            
            # Actions by type
            actions_by_type = ActionLog.objects.filter(
                timestamp__gte=cutoff_date
            ).values('action_type').annotate(count=Count('id')).order_by('-count')
            
            # Actions by module
            actions_by_module = ActionLog.objects.filter(
                timestamp__gte=cutoff_date
            ).values('module_name').annotate(count=Count('id')).order_by('-count')
            
            # Most active users
            active_users = ActionLog.objects.filter(
                timestamp__gte=cutoff_date
            ).values('user__username').annotate(count=Count('id')).order_by('-count')[:10]
            
            return {
                'total_actions': total_actions,
                'actions_by_type': list(actions_by_type),
                'actions_by_module': list(actions_by_module),
                'active_users': list(active_users)
            }
            
        except Exception:
            return {
                'total_actions': 0,
                'actions_by_type': [],
                'actions_by_module': [],
                'active_users': []
            }

    def search_login_logs(self, queryset, search_field, search_query):
        """
        Apply search filter to login logs queryset
        
        Args:
            queryset: Login logs queryset
            search_field: Field to search in
            search_query: Search query
            
        Returns:
            QuerySet: Filtered queryset
        """
        if not search_query:
            return queryset
        
        if search_field == 'username':
            return queryset.filter(user__username__icontains=search_query)
        elif search_field == 'ip_address':
            return queryset.filter(ip_address__icontains=search_query)
        elif search_field == 'user_agent':
            return queryset.filter(user_agent__icontains=search_query)
        elif search_field == 'success':
            success_value = search_query.lower() in ['true', '1', 'yes', 'نجح', 'نعم']
            return queryset.filter(success=success_value)
        else:
            # Fallback to base search method
            return self.search(queryset, search_field, search_query)

    def search_action_logs(self, queryset, search_field, search_query):
        """
        Apply search filter to action logs queryset
        
        Args:
            queryset: Action logs queryset
            search_field: Field to search in
            search_query: Search query
            
        Returns:
            QuerySet: Filtered queryset
        """
        if not search_query:
            return queryset
        
        if search_field == 'username':
            return queryset.filter(user__username__icontains=search_query)
        elif search_field == 'action_type':
            return queryset.filter(action_type__icontains=search_query)
        elif search_field == 'module_name':
            return queryset.filter(module_name__icontains=search_query)
        elif search_field == 'description':
            return queryset.filter(description__icontains=search_query)
        elif search_field == 'ip_address':
            return queryset.filter(ip_address__icontains=search_query)
        else:
            # Fallback to base search method
            return self.search(queryset, search_field, search_query)

    def get_failed_login_attempts(self, ip_address=None, username=None, hours=24):
        """
        Get failed login attempts for security monitoring
        
        Args:
            ip_address: Filter by IP address
            username: Filter by username
            hours: Number of hours to look back
            
        Returns:
            QuerySet: Failed login attempts
        """
        try:
            cutoff_time = timezone.now() - timedelta(hours=hours)
            
            queryset = LoginLog.objects.filter(
                success=False,
                login_time__gte=cutoff_time
            ).select_related('user')
            
            if ip_address:
                queryset = queryset.filter(ip_address=ip_address)
            
            if username:
                queryset = queryset.filter(user__username=username)
            
            return queryset.order_by('-login_time')
            
        except Exception:
            return LoginLog.objects.none()

    def cleanup_old_logs(self, days=90):
        """
        Clean up old log entries
        
        Args:
            days: Number of days to keep logs
            
        Returns:
            dict: Cleanup statistics
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Count logs to be deleted
            old_login_logs = LoginLog.objects.filter(login_time__lt=cutoff_date).count()
            old_action_logs = ActionLog.objects.filter(timestamp__lt=cutoff_date).count()
            
            # Delete old logs
            deleted_login_logs = LoginLog.objects.filter(login_time__lt=cutoff_date).delete()[0]
            deleted_action_logs = ActionLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
            
            return {
                'deleted_login_logs': deleted_login_logs,
                'deleted_action_logs': deleted_action_logs,
                'total_deleted': deleted_login_logs + deleted_action_logs
            }
            
        except Exception:
            return {
                'deleted_login_logs': 0,
                'deleted_action_logs': 0,
                'total_deleted': 0
            }

    def get_user_activity_summary(self, user, days=30):
        """
        Get user activity summary
        
        Args:
            user: User instance
            days: Number of days to analyze
            
        Returns:
            dict: User activity summary
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Login statistics
            login_logs = LoginLog.objects.filter(
                user=user, login_time__gte=cutoff_date
            )
            
            total_logins = login_logs.count()
            successful_logins = login_logs.filter(success=True).count()
            last_login = login_logs.filter(success=True).first()
            
            # Action statistics
            action_logs = ActionLog.objects.filter(
                user=user, timestamp__gte=cutoff_date
            )
            
            total_actions = action_logs.count()
            actions_by_type = action_logs.values('action_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return {
                'total_logins': total_logins,
                'successful_logins': successful_logins,
                'last_login': last_login.login_time if last_login else None,
                'total_actions': total_actions,
                'actions_by_type': list(actions_by_type)
            }
            
        except Exception:
            return {
                'total_logins': 0,
                'successful_logins': 0,
                'last_login': None,
                'total_actions': 0,
                'actions_by_type': []
            }
