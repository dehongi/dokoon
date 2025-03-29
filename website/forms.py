from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    """Form for the contact page"""

    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Your Name")}
        ),
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Your Email")}
        ),
    )

    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Your Phone (optional)")}
        ),
    )

    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Subject")}
        ),
    )

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": _("Your Message"), "rows": 6}
        ),
    )

    # Honeypot field to catch bots
    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "style": "display:none !important;",
                "tabindex": "-1",
                "autocomplete": "off",
            }
        ),
        label="Leave this field empty",
    )

    def clean_honeypot(self):
        """Check if honeypot field is empty (it should be for real users)"""
        honeypot = self.cleaned_data.get("honeypot")
        if honeypot:
            raise forms.ValidationError(
                _("Spam protection activated. Please try submitting the form again.")
            )
        return honeypot


class NewsletterSubscriptionForm(forms.Form):
    """Simple form for newsletter subscriptions"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Enter your email")}
        ),
    )
