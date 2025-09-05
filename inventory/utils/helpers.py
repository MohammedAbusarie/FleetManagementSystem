"""Helper functions and utilities"""
from django.core.paginator import Paginator
from django.db.models import Q


def paginate_queryset(queryset, page_number, per_page=20):
    """Helper function to paginate a queryset"""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)


def apply_search_filter(queryset, search_field, search_query):
    """Apply search filter to queryset"""
    if not search_query or not search_field:
        return queryset
    filter_kwargs = {f"{search_field}__icontains": search_query}
    return queryset.filter(**filter_kwargs)


def apply_sorting(queryset, sort_by, sort_order='asc'):
    """Apply sorting to queryset"""
    if sort_by:
        prefix = '-' if sort_order == 'desc' else ''
        return queryset.order_by(f"{prefix}{sort_by}")
    return queryset
