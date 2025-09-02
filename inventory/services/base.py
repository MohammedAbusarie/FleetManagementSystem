"""Base service class with common CRUD operations"""
from django.core.paginator import Paginator
from django.db.models import Q


class BaseService:
    """Base service with common database operations"""
    model = None
    
    def get_all(self, select_related=None, prefetch_related=None):
        """Get all objects with optional related prefetching"""
        queryset = self.model.objects.all()
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return queryset
    
    def get_by_id(self, pk):
        """Get single object by primary key"""
        return self.model.objects.get(pk=pk)
    
    def search(self, queryset, search_field, search_query):
        """Apply search filter to queryset"""
        if not search_query:
            return queryset
        filter_kwargs = {f"{search_field}__icontains": search_query}
        return queryset.filter(**filter_kwargs)
    
    def sort(self, queryset, sort_by, sort_order='asc'):
        """Apply sorting to queryset"""
        if sort_by:
            prefix = '-' if sort_order == 'desc' else ''
            return queryset.order_by(f"{prefix}{sort_by}")
        return queryset
    
    def paginate(self, queryset, page_number, per_page=20):
        """Paginate queryset"""
        paginator = Paginator(queryset, per_page)
        return paginator.get_page(page_number)
