from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import FormView
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Page,
    FAQ,
    Testimonial,
    TeamMember,
    Banner,
    SiteSettings,
    ContactMessage,
)
from .forms import ContactForm
from shop.models import Product, Category


def get_common_context():
    """Helper function to get common context data for all pages"""
    try:
        site_settings = SiteSettings.objects.first()
    except:
        site_settings = None

    return {"site_settings": site_settings, "current_year": timezone.now().year}


class HomeView(TemplateView):
    """Home page view"""

    template_name = "website/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())

        # Featured products
        context["featured_products"] = Product.objects.filter(
            is_active=True, is_featured=True
        ).order_by("-created_at")[:8]

        # Product categories
        context["product_categories"] = Category.objects.filter(
            is_active=True
        ).order_by("name")

        # Banners
        context["banners"] = Banner.objects.filter(
            is_active=True, display_on="home"
        ).order_by("order")

        # Testimonials
        context["testimonials"] = Testimonial.objects.filter(
            is_active=True, display_on_homepage=True
        ).order_by("order")[:6]

        return context


class AboutView(TemplateView):
    """About page view"""

    template_name = "website/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())

        # Get about page content
        try:
            about_page = Page.objects.get(page_type="about", is_active=True)
        except Page.DoesNotExist:
            about_page = None

        context["page"] = about_page

        # Team members
        context["team_members"] = TeamMember.objects.filter(is_active=True).order_by(
            "order"
        )

        # Testimonials
        context["testimonials"] = Testimonial.objects.filter(is_active=True).order_by(
            "?"
        )[
            :3
        ]  # Random testimonials

        return context


class ContactView(FormView):
    """Contact page with form submission"""

    template_name = "website/contact.html"
    form_class = ContactForm
    success_url = "/contact/thank-you/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())
        return context

    def form_valid(self, form):
        # Save form data to ContactMessage model
        contact_message = ContactMessage(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data.get("phone", ""),
            subject=form.cleaned_data["subject"],
            message=form.cleaned_data["message"],
            ip_address=self.request.META.get("REMOTE_ADDR", None),
        )
        contact_message.save()

        # Send email notification
        try:
            # Get recipient email from site settings or use default
            site_settings = SiteSettings.objects.first()
            recipient_email = (
                site_settings.contact_email
                if site_settings
                else settings.DEFAULT_FROM_EMAIL
            )

            send_mail(
                subject=f"New Contact Form Submission: {form.cleaned_data['subject']}",
                message=f"Name: {form.cleaned_data['name']}\n"
                f"Email: {form.cleaned_data['email']}\n"
                f"Phone: {form.cleaned_data.get('phone', 'Not provided')}\n\n"
                f"Message:\n{form.cleaned_data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but don't show it to the user
            print(f"Email sending failed: {str(e)}")

        messages.success(
            self.request, "Your message has been sent. We'll get back to you soon!"
        )
        return super().form_valid(form)


class ContactThankYouView(TemplateView):
    """Thank you page after contact form submission"""

    template_name = "website/contact_thank_you.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())
        return context


class TermsView(TemplateView):
    """Terms and Conditions page"""

    template_name = "website/terms.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())

        try:
            terms_page = Page.objects.get(page_type="terms", is_active=True)
        except Page.DoesNotExist:
            terms_page = None

        context["page"] = terms_page
        return context


class PrivacyView(TemplateView):
    """Privacy Policy page"""

    template_name = "website/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())

        try:
            privacy_page = Page.objects.get(page_type="privacy", is_active=True)
        except Page.DoesNotExist:
            privacy_page = None

        context["page"] = privacy_page
        return context


class FAQView(TemplateView):
    """FAQ page"""

    template_name = "website/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())

        # Get FAQ page content if it exists
        try:
            faq_page = Page.objects.get(page_type="faq", is_active=True)
        except Page.DoesNotExist:
            faq_page = None

        context["page"] = faq_page

        # Get FAQs grouped by category
        faqs = FAQ.objects.filter(is_active=True).order_by("category", "order")

        # Group FAQs by category
        faq_categories = {}
        for faq in faqs:
            category = faq.get_category_display()
            if category not in faq_categories:
                faq_categories[category] = []
            faq_categories[category].append(faq)

        context["faq_categories"] = faq_categories
        return context


class HelpCenterView(TemplateView):
    """Help Center page"""

    template_name = "website/help.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())

        try:
            help_page = Page.objects.get(page_type="help", is_active=True)
        except Page.DoesNotExist:
            help_page = None

        context["page"] = help_page

        # Get a few common FAQs
        context["common_faqs"] = FAQ.objects.filter(
            is_active=True, category="general"
        ).order_by("order")[:5]

        return context


class CustomPageView(DetailView):
    """View for custom pages"""

    model = Page
    template_name = "website/custom_page.html"
    context_object_name = "page"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_common_context())
        return context

    def get_queryset(self):
        return Page.objects.filter(is_active=True, page_type="custom")
