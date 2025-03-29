from django import forms
from .models import Comment, Post, Author


class CommentForm(forms.ModelForm):
    """Form for blog comments"""

    parent_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Comment
        fields = ("author_name", "author_email", "content")
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Enter your comment here..."}
            ),
            "author_name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "author_email": forms.EmailInput(
                attrs={"placeholder": "Your email address"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required
        self.fields["author_name"].required = True
        self.fields["author_email"].required = True
        self.fields["content"].required = True
        # Add CSS classes
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"


class PostSearchForm(forms.Form):
    """Form for searching blog posts"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Search posts...", "class": "form-control"}
        ),
    )
    category = forms.ChoiceField(
        required=False, widget=forms.Select(attrs={"class": "form-select"})
    )
    tag = forms.ChoiceField(
        required=False, widget=forms.Select(attrs={"class": "form-select"})
    )
    post_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + list(Post.POST_TYPES),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate category and tag choices
        from .models import Category, Tag

        # Categories
        categories = Category.objects.filter(is_active=True)
        self.fields["category"].choices = [("", "All Categories")] + [
            (c.slug, c.name) for c in categories
        ]

        # Tags
        tags = Tag.objects.all()
        self.fields["tag"].choices = [("", "All Tags")] + [
            (t.slug, t.name) for t in tags
        ]


class AuthorProfileForm(forms.ModelForm):
    """Form for authors to update their profile"""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = Author
        fields = (
            "bio",
            "profile_picture",
            "website",
            "facebook",
            "twitter",
            "instagram",
            "linkedin",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

        # Initialize user data if author exists
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        author = super().save(commit=False)

        # Update user information
        user = author.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            author.save()

        return author
