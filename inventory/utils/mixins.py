"""Mixins for common functionality"""
from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin privileges for class-based views"""
    
    def test_func(self):
        return self.request.user.groups.filter(name='Admin').exists() or self.request.user.is_superuser
