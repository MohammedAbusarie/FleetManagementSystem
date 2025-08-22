"""Authentication views"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from ..utils.decorators import admin_required


def is_admin(user):
    """Check if user is in Admin group or is superuser"""
    return user.groups.filter(name='Admin').exists() or user.is_superuser


def login_view(request):
    """Login view"""
    class ArabicAuthenticationForm(AuthenticationForm):
        username = forms.CharField(label='اسم المستخدم')
        password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput)
        
    if request.method == 'POST':
        form = ArabicAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if is_admin(user):
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'ليس لديك صلاحية للدخول إلى هذا النظام.')
    else:
        form = ArabicAuthenticationForm()
    return render(request, 'inventory/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')
