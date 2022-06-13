from django import forms
from ohq.models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

MAX_UPLOAD_SIZE = 2500000


class LoginForm(forms.Form):
    username = forms.CharField(max_length = 20, widget=forms.TextInput(attrs={'style': 'font-size: 18px',}))
    password = forms.CharField(max_length = 200, widget = forms.PasswordInput(attrs={'style': 'font-size: 18px',}))

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid username/password")

        return cleaned_data

class RegisterForm(forms.Form):
    username = forms.CharField(max_length = 20, widget=forms.TextInput(attrs={'style': 'font-size: 18px',}))
    password = forms.CharField(max_length = 200, widget = forms.PasswordInput(attrs={'style': 'font-size: 18px',}))
    confirm_password = forms.CharField(max_length = 200, widget = forms.PasswordInput(attrs={'style': 'font-size: 18px',}))
    email = forms.CharField(max_length = 50, widget=forms.TextInput(attrs={'style': 'font-size: 18px',}))
    first_name = forms.CharField(max_length = 20, widget=forms.TextInput(attrs={'style': 'font-size: 18px',}))
    last_name = forms.CharField(max_length = 20, widget=forms.TextInput(attrs={'style': 'font-size: 18px',}))

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('confirm_password')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")

        return username


class AnnouncementForm(forms.Form):
    class Meta:
        model = Announcement
        fields = ("content",)


class UploadFileForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        this_file = self.cleaned_data['file']
        if not this_file or not hasattr(this_file, 'content_type'):
            raise forms.ValidationError('You must upload a csv file')
        if not this_file.content_type or not this_file.content_type.startswith('text/csv'):
            raise forms.ValidationError('File type is not a csv file')
        if this_file.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
        return this_file
