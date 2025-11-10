"""Static informational pages."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def about_view(request):
    """Display project credits, roles, and contact information."""
    context = {
        "developer_name": "محمد أبوسريع",
        "developer_title_name": "م/ محمد أبوسريع",
        "roles": [
            "مطوّر المشروع",
            "مهندس قواعد البيانات",
            "مصمّم واجهات الويب",
            "مختبر البرمجيات",
            "مطوّر الواجهة الخلفية",
            "مدير المنتج",
        ],
        "technologies": [
            "Django 5.2.7",
            "Python 3.11",
            "PostgreSQL",
            "HTML5",
            "CSS3",
            "Bootstrap 5",
            "Bootstrap Icons",
            "Crispy Bootstrap 5",
            "GSAP",
        ],
        "contacts": [
            {
                "label": "حساب لينكدإن",
                "value": "mohammed-abusarie-a39a60223",
                "href": "https://www.linkedin.com/in/mohammed-abusarie-a39a60223/",
                "icon": "bi bi-linkedin",
                "is_external": True,
                "is_ltr": True,
            },
            {
                "label": "البريد الإلكتروني",
                "value": "new.is.new55@gmail.com",
                "href": "mailto:new.is.new55@gmail.com",
                "icon": "bi bi-envelope-fill",
                "is_external": False,
                "is_ltr": True,
            },
            {
                "label": "الهاتف الرئيسي",
                "value": "+201226953418",
                "href": "tel:+201226953418",
                "icon": "bi bi-telephone-fill",
                "is_external": False,
                "is_ltr": True,
            },
            {
                "label": "الهاتف البديل",
                "value": "+201111314509",
                "href": "tel:+201111314509",
                "icon": "bi bi-telephone-plus-fill",
                "is_external": False,
                "is_ltr": True,
            },
        ],
    }
    return render(request, "inventory/about.html", context)


