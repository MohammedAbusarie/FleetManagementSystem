"""Authentication views"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from ..utils.decorators import admin_required
from ..utils.helpers import is_admin_user, log_user_login, get_client_ip, get_user_agent
from ..services.rbac_service import LoggingService


def is_admin(user):
    """Check if user is in Admin group or is superuser - BACKWARD COMPATIBLE"""
    # Use helper function for consistency but maintain backward compatibility
    return is_admin_user(user)


def login_view(request):
    """Login view with enhanced logging and user type support"""
    class ArabicAuthenticationForm(AuthenticationForm):
        username = forms.CharField(label='اسم المستخدم')
        password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput)
        
    if request.method == 'POST':
        form = ArabicAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            
            # Check user permissions using helper function (backward compatible)
            if is_admin_user(user):
                login(request, user)
                
                # Log successful login
                log_user_login(user, ip_address, user_agent, success=True)
                
                return redirect('dashboard')
            else:
                # Log failed login attempt
                log_user_login(user, ip_address, user_agent, success=False)
                messages.error(request, 'ليس لديك صلاحية للدخول إلى هذا النظام.')
        else:
            # Log failed login attempt (invalid credentials)
            if form.errors:
                ip_address = get_client_ip(request)
                user_agent = get_user_agent(request)
                # Try to get username from form data
                username = request.POST.get('username', 'unknown')
                try:
                    from django.contrib.auth.models import User
                    user = User.objects.get(username=username)
                    log_user_login(user, ip_address, user_agent, success=False)
                except User.DoesNotExist:
                    pass
    else:
        form = ArabicAuthenticationForm()
    return render(request, 'inventory/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view with enhanced logging"""
    user = request.user
    ip_address = get_client_ip(request)
    
    # Log logout
    logging_service = LoggingService()
    logging_service.log_logout(user, ip_address)
    
    logout(request)
    return redirect('login')
