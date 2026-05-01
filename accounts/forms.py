from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
import re
import bleach

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    role = forms.ChoiceField(choices=[('patient', 'Patient'), ('doctor', 'Doctor')])
    phone = forms.CharField(max_length=15, required=False)
    specialization = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        # A03 - only allow safe characters
        if not re.match(r'^[\w]{3,30}$', username):
            raise forms.ValidationError("Username: 3-30 characters, letters/numbers/underscore only.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_first_name(self):
        name = bleach.clean(self.cleaned_data.get('first_name', ''), tags=[], strip=True)
        if not re.match(r'^[A-Za-z\s]{2,50}$', name):
            raise forms.ValidationError("Name should contain letters only.")
        return name

    def clean_last_name(self):
        name = bleach.clean(self.cleaned_data.get('last_name', ''), tags=[], strip=True)
        if not re.match(r'^[A-Za-z\s]{2,50}$', name):
            raise forms.ValidationError("Name should contain letters only.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone and not re.match(r'^\+?[\d\s\-]{7,15}$', phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

class SecureLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Username', 'autocomplete': 'username'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Password', 'autocomplete': 'current-password'})

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    # A10 - no URL fields accepted freely

    class Meta:
        model = UserProfile
        fields = ['phone', 'date_of_birth', 'address', 'profile_pic', 'specialization']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone and not re.match(r'^\+?[\d\s\-]{7,15}$', phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_address(self):
        # A03 - sanitize address field
        return bleach.clean(self.cleaned_data.get('address', ''), tags=[], strip=True)

    def clean_profile_pic(self):
        pic = self.cleaned_data.get('profile_pic')
        if pic:
            # A08 - validate MIME type, not just extension
            import magic
            mime = magic.from_buffer(pic.read(1024), mime=True)
            pic.seek(0)
            if mime not in ['image/jpeg', 'image/png', 'image/gif']:
                raise forms.ValidationError("Only JPG, PNG, GIF images allowed.")
            if pic.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image must be under 2MB.")
        return pic