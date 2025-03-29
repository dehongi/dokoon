from django.urls import path
from . import views

app_name = "website"

urlpatterns = [
    # Main pages
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path(
        "contact/thank-you/",
        views.ContactThankYouView.as_view(),
        name="contact_thank_you",
    ),
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("faq/", views.FAQView.as_view(), name="faq"),
    path("help/", views.HelpCenterView.as_view(), name="help"),
    # Custom pages
    path("page/<slug:slug>/", views.CustomPageView.as_view(), name="custom_page"),
]
