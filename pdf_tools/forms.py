from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

class ContactForm(forms.Form):
    CATEGORY_CHOICES = [
        ('', 'Select Category *'),
        ('technical_support', 'Technical Support'),
        ('billing', 'Billing & Pricing'),
        ('feature_request', 'Feature Request'),
        ('bug_report', 'Bug Report'),
        ('partnership', 'Partnership Inquiry'),
        ('general', 'General Question'),
        ('other', 'Other'),
    ]
    
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    company = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=20, required=False)
    subject = forms.CharField(max_length=200)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    message = forms.CharField(widget=forms.Textarea)
    attachment = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'])]
    )
    privacy = forms.BooleanField()
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise ValidationError('Please provide a more detailed message.')
        return message

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError('File size must be under 10MB.')
        return attachment