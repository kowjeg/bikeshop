from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from users.models import Profile


class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        user = User(
            username=self.cleaned_data.get('username', ''),
            email=self.cleaned_data.get('email', ''),
        )
        validate_password(password, user=user)
        return password

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already registered')
        return username

    def save(self):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        username = self.cleaned_data['username']
        return User.objects.create_user(username=username, email=email, password=password)


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'Input', 'placeholder': 'example@mail.com'}))

    class Meta:
        model = Profile
        fields = ('full_name', 'phone', 'city', 'address')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'Input'}),
            'phone': forms.TextInput(attrs={'class': 'Input'}),
            'city': forms.TextInput(attrs={'class': 'Input'}),
            'address': forms.Textarea(attrs={'class': 'Textarea', 'rows': 3}),
        }
