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
            
            # Check if user is active and has proper permissions
            # All users with profiles should be able to login to main system
            # Admin panel access is controlled separately
            try:
                profile = user.profile
                if profile.is_active:
                    login(request, user)
                    
                    # Log successful login
                    log_user_login(user, ip_address, user_agent, success=True)
                    
                    return redirect('dashboard')
                else:
                    # User profile is inactive
                    log_user_login(user, ip_address, user_agent, success=False)
                    messages.error(request, 'حسابك غير نشط. يرجى التواصل مع المدير.')
            except Exception:
                # Fallback: check if user is in Admin group (backward compatibility)
                if user.groups.filter(name='Admin').exists() or user.is_superuser:
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


@login_required
def account_profile_view(request):
    """View for users to see their account information and change password"""
    from ..forms.rbac_forms import UserPasswordChangeForm
    
    user = request.user
    password_form = None
    password_changed = False
    
    # Get user profile information
    try:
        profile = user.profile
        user_type = profile.get_user_type_display()
        is_active = profile.is_active
    except Exception:
        # Fallback for users without profile
        user_type = 'مدير' if user.is_superuser else 'مستخدم عادي'
        is_active = user.is_active
    
    # Handle password change
    if request.method == 'POST':
        password_form = UserPasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            password_form.save()
            messages.success(request, 'تم تغيير كلمة المرور بنجاح.')
            password_changed = True
            # Clear the form after successful password change
            password_form = UserPasswordChangeForm(user)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
    else:
        password_form = UserPasswordChangeForm(user)
    
    context = {
        'user': user,
        'user_type': user_type,
        'is_active': is_active,
        'password_form': password_form,
        'password_changed': password_changed,
    }
    
    return render(request, 'inventory/account_profile.html', context)