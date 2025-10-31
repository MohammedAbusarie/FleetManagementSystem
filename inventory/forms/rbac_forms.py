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
            except UserProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            # Update user profile
            try:
                profile = user.profile
                profile.user_type = self.cleaned_data['user_type']
                profile.is_active = self.cleaned_data['is_active']
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=user,
                    user_type=self.cleaned_data['user_type'],
                    is_active=self.cleaned_data['is_active']
                )

        return user


class PermissionAssignmentForm(forms.Form):
    """Form for assigning permissions to users"""

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Get all modules
        modules = ['cars', 'equipment', 'generic_tables']
        permissions = ['create', 'read', 'update', 'delete']

        for module in modules:
            for permission in permissions:
                field_name = f"{module}_{permission}"
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=f"{self.get_module_display(module)} - {self.get_permission_display(permission)}",
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )

                # Set initial value
                try:
                    user_permission = UserPermission.objects.get(
                        user=user,
                        module_permission__module_name=module,
                        module_permission__permission_type=permission
                    )
                    self.fields[field_name].initial = user_permission.granted
                except UserPermission.DoesNotExist:
                    self.fields[field_name].initial = False

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

    def save(self):
        """Save permission assignments"""
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
