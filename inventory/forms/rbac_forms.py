"""RBAC forms following project patterns"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from ..models import UserProfile, ModulePermission, UserPermission
from .base import Select2Widget


class UserCreateForm(UserCreationForm):
    """Form for creating new users"""

    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=Select2Widget(),
        label="نوع المستخدم"
    )
    first_name = forms.CharField(max_length=30, label="الاسم الأول")
    last_name = forms.CharField(max_length=30, label="الاسم الأخير")
    email = forms.EmailField(label="البريد الإلكتروني")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'user_type')
        labels = {
            'username': 'اسم المستخدم',
            'password1': 'كلمة المرور',
            'password2': 'تأكيد كلمة المرور',
        }

    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop('created_by', None)
        super().__init__(*args, **kwargs)

        # Add Arabic styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                user_type=self.cleaned_data['user_type'],
                created_by=self.created_by,
                is_active=True
            )

        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""

    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=Select2Widget(),
        label="نوع المستخدم"
    )
    is_active = forms.BooleanField(
        required=False,
        label="نشط"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')
        labels = {
            'username': 'اسم المستخدم',
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        # Extract current_user from kwargs if provided (needed for validation)
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # Add Arabic styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})

        # Set initial values from profile
        if self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['user_type'].initial = profile.user_type
                self.fields['is_active'].initial = profile.is_active
                
                # Disable fields for protected users
                from ..utils.helpers import is_super_admin
                
                # If user is super admin, disable user_type field (can't change super admin type easily)
                if is_super_admin(self.instance):
                    self.fields['user_type'].widget.attrs['disabled'] = True
                    self.fields['user_type'].widget.attrs['title'] = 'لا يمكن تغيير نوع المدير العام بسهولة. يجب تغييره من قبل مدير عام آخر.'
                
                # If current_user is admin (not super admin), disable user_type field
                # (admins can't change user types - only super admins can)
                if self.current_user:
                    current_user_type = None
                    try:
                        changer_profile = self.current_user.profile
                        current_user_type = changer_profile.user_type
                    except (UserProfile.DoesNotExist, AttributeError):
                        current_user_type = 'admin' if self.current_user.is_superuser else 'normal'
                    
                    if current_user_type == 'admin' and not is_super_admin(self.current_user):
                        self.fields['user_type'].widget.attrs['disabled'] = True
                        self.fields['user_type'].widget.attrs['title'] = 'يمكن فقط للمدير العام تغيير نوع المستخدم.'
                        
            except UserProfile.DoesNotExist:
                pass

    def clean_user_type(self):
        """Validate user type changes"""
        from django.core.exceptions import ValidationError
        from django.contrib.auth.models import User
        from ..utils.helpers import is_super_admin, is_admin_user
        
        if not self.instance.pk:
            # New user - validation handled in UserCreateForm
            return self.cleaned_data['user_type']
        
        new_user_type = self.cleaned_data['user_type']
        
        # Get current user type
        try:
            current_profile = self.instance.profile
            current_user_type = current_profile.user_type
        except UserProfile.DoesNotExist:
            # Fallback: check if user is superuser
            current_user_type = 'admin' if self.instance.is_superuser else 'normal'
        
        # If user type hasn't changed, no validation needed
        if new_user_type == current_user_type:
            return new_user_type
        
        # Check if current_user (person making the change) is provided
        if not self.current_user:
            # If current_user not provided, only allow if user is super admin (for backward compatibility)
            # In production, current_user should always be provided
            return new_user_type
        
        current_user_type_changer = None
        try:
            changer_profile = self.current_user.profile
            current_user_type_changer = changer_profile.user_type
        except (UserProfile.DoesNotExist, AttributeError):
            current_user_type_changer = 'admin' if self.current_user.is_superuser else 'normal'
        
        # Validation rules:
        # 1. Only super admins can change users to super_admin
        if new_user_type == 'super_admin' and current_user_type_changer != 'super_admin':
            raise ValidationError('فقط المدير العام يمكنه تغيير نوع المستخدم إلى مدير عام.')
        
        # 2. Only super admins can change users to admin
        if new_user_type == 'admin' and current_user_type_changer != 'super_admin':
            raise ValidationError('فقط المدير العام يمكنه تغيير نوع المستخدم إلى مدير.')
        
        # 3. Prevent changing super admin to lower privilege (unless done by another super admin)
        if current_user_type == 'super_admin' and new_user_type != 'super_admin':
            if current_user_type_changer != 'super_admin':
                raise ValidationError('لا يمكن تغيير نوع المدير العام إلا بواسطة مدير عام آخر.')
            
            # Check if this is the last super admin
            from ..models import UserProfile
            active_super_admins = UserProfile.objects.filter(
                user_type='super_admin',
                is_active=True
            ).exclude(user=self.instance).count()
            
            # Also count Django superusers
            django_superusers = User.objects.filter(
                is_superuser=True
            ).exclude(id=self.instance.id).count()
            
            if active_super_admins == 0 and django_superusers == 0:
                raise ValidationError('لا يمكن تغيير نوع آخر مدير عام في النظام. يجب أن يكون هناك مدير عام واحد على الأقل.')
        
        return new_user_type
    
    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            # Update user profile
            try:
                profile = user.profile
                old_user_type = profile.user_type
                # Handle disabled fields - if user_type was disabled, use current value
                # Django doesn't submit disabled fields, so we need to get it from initial or current value
                if 'user_type' in self.fields and self.fields['user_type'].widget.attrs.get('disabled'):
                    # Field was disabled - use the current value (not from POST data)
                    new_user_type = old_user_type
                elif 'user_type' not in self.cleaned_data:
                    # Field not in cleaned_data (might be disabled) - use current value
                    new_user_type = old_user_type
                else:
                    new_user_type = self.cleaned_data.get('user_type', old_user_type)
                
                profile.user_type = new_user_type
                profile.is_active = self.cleaned_data['is_active']
                profile.save()
                
                # Cascade permission cleanup based on user type changes
                if old_user_type != new_user_type:
                    # User upgraded to admin/super_admin - permissions are automatic
                    # Clean up UserPermission records since they're not needed
                    if old_user_type == 'normal' and new_user_type in ['admin', 'super_admin']:
                        UserPermission.objects.filter(user=user).delete()
                        
                    # User downgraded from admin/super_admin to normal
                    # Keep UserPermission records - they define the user's actual permissions
                    # (They might be upgraded again, but for now permissions should remain)
                    elif old_user_type in ['admin', 'super_admin'] and new_user_type == 'normal':
                        # Permissions remain - they define what the normal user can do
                        pass
                    
                    # User changed from admin to super_admin or vice versa
                    # Both have all permissions automatically, so clean up records
                    elif old_user_type in ['admin', 'super_admin'] and new_user_type in ['admin', 'super_admin']:
                        UserPermission.objects.filter(user=user).delete()
                        
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=user,
                    user_type=self.cleaned_data['user_type'],
                    is_active=self.cleaned_data['is_active']
                )
                
                # If creating profile as admin/super_admin, clean up any existing permissions
                if self.cleaned_data['user_type'] in ['admin', 'super_admin']:
                    UserPermission.objects.filter(user=user).delete()

        return user


class PermissionAssignmentForm(forms.Form):
    """Form for assigning permissions to users"""

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Get all modules
        modules = ['cars', 'equipment', 'generic_tables']
        permissions = ['create', 'read', 'update', 'delete']

        # Check if user is admin or super_admin (they have all permissions automatically)
        is_admin = False
        try:
            profile = user.profile
            user_type = profile.get_user_type()
            is_admin = user_type in ['super_admin', 'admin']
        except (UserProfile.DoesNotExist, AttributeError):
            # Fallback: check if user is superuser or in Admin group
            is_admin = user.is_superuser or user.groups.filter(name='Admin').exists()

        # Fetch all user permissions at once for efficiency
        # This avoids N+1 query problem and ensures we get all existing permissions
        # Note: Admin/super_admin users may not have UserPermission records since they have all permissions automatically
        user_permissions = UserPermission.objects.filter(
            user=user
        ).select_related('module_permission').values_list(
            'module_permission__module_name',
            'module_permission__permission_type',
            'granted'
        )
        
        # Create a dictionary mapping (module, permission) -> granted status
        permission_map = {
            (mp_module, mp_permission): granted
            for mp_module, mp_permission, granted in user_permissions
        }

        # Create form fields and set initial values
        # Django forms use self.initial to populate unbound form fields
        # When form is unbound (GET request), Django uses self.initial to set field values
        # When form is bound (POST request), Django uses POST data instead
        for module in modules:
            for permission in permissions:
                field_name = f"{module}_{permission}"
                
                # If user is admin/super_admin, they have all permissions (show as checked)
                # Otherwise, check UserPermission records
                if is_admin:
                    granted = True  # Admins have all permissions automatically
                else:
                    granted = permission_map.get((module, permission), False)
                
                # Set initial value for unbound forms (when no POST data)
                # This ensures checkboxes show the correct checked state on initial page load
                if not self.is_bound:
                    self.initial[field_name] = granted
                
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=f"{self.get_module_display(module)} - {self.get_permission_display(permission)}",
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )

    def get_module_display(self, module):
        """Get Arabic display name for module"""
        module_names = {
            'cars': 'السيارات',
            'equipment': 'المعدات',
            'generic_tables': 'الجداول العامة'
        }
        return module_names.get(module, module)

    def get_permission_display(self, permission):
        """Get Arabic display name for permission"""
        permission_names = {
            'create': 'إنشاء',
            'read': 'قراءة',
            'update': 'تحديث',
            'delete': 'حذف'
        }
        return permission_names.get(permission, permission)

    def save(self, current_user=None):
        """Save permission assignments"""
        from django.core.exceptions import ValidationError
        from ..utils.helpers import is_super_admin, is_admin_user
        
        # Prevent saving permissions for super admins
        # Super admins have all permissions automatically and shouldn't have UserPermission records
        if is_super_admin(self.user):
            # Clean up any existing UserPermission records for super admins
            UserPermission.objects.filter(user=self.user).delete()
            raise ValidationError(
                'لا يمكن حفظ صلاحيات للمدير العام. المديرون العامون لديهم جميع الصلاحيات تلقائياً.'
            )
        
        # Permission assignment validation
        # Check if current_user (person assigning permissions) has permission to do so
        if current_user:
            current_user_type = None
            try:
                changer_profile = current_user.profile
                current_user_type = changer_profile.user_type
            except (UserProfile.DoesNotExist, AttributeError):
                current_user_type = 'admin' if current_user.is_superuser else 'normal'
            
            # Only super admins can assign permissions to admin users
            target_user_type = None
            try:
                target_profile = self.user.profile
                target_user_type = target_profile.user_type
            except UserProfile.DoesNotExist:
                target_user_type = 'admin' if self.user.is_superuser else 'normal'
            
            # Super admins can assign permissions to anyone (except super admins, handled above)
            if current_user_type == 'super_admin':
                pass  # Allow
            # Admins can only assign permissions to normal users
            elif current_user_type == 'admin':
                if target_user_type in ['admin', 'super_admin']:
                    raise ValidationError(
                        'لا يمكنك تعيين صلاحيات للمديرين أو المديرين العامين. يمكنك فقط تعيين صلاحيات للمستخدمين العاديين.'
                    )
            else:
                # Normal users cannot assign permissions
                raise ValidationError('ليس لديك صلاحية لتعيين الصلاحيات.')
        
        modules = ['cars', 'equipment', 'generic_tables']
        permissions = ['create', 'read', 'update', 'delete']

        for module in modules:
            for permission in permissions:
                field_name = f"{module}_{permission}"
                granted = self.cleaned_data.get(field_name, False)

                try:
                    module_permission = ModulePermission.objects.get(
                        module_name=module,
                        permission_type=permission
                    )
                except ModulePermission.DoesNotExist:
                    module_permission = ModulePermission.objects.create(
                        module_name=module,
                        permission_type=permission,
                        description=f"Permission {permission} for {module}"
                    )

                user_permission, created = UserPermission.objects.get_or_create(
                    user=self.user,
                    module_permission=module_permission,
                    defaults={'granted': granted}
                )

                if not created:
                    user_permission.granted = granted
                    user_permission.save()

        return True


class UserProfileForm(forms.ModelForm):
    """Form for user profile management"""

    class Meta:
        model = UserProfile
        fields = ('user_type', 'is_active', 'permissions_json')
        labels = {
            'user_type': 'نوع المستخدم',
            'is_active': 'نشط',
            'permissions_json': 'الصلاحيات',
        }
        widgets = {
            'user_type': Select2Widget(),
            'permissions_json': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Arabic styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control'})
