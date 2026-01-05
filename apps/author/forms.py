from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Split full name into first_name and last_name
        full_name = self.cleaned_data.get("first_name", "")
        name_parts = full_name.strip().split()
        if len(name_parts) == 0:
            user.first_name = ""
            user.last_name = ""
        elif len(name_parts) == 1:
            user.first_name = name_parts[0]
            user.last_name = ""
        else:
            user.first_name = name_parts[0]
            user.last_name = " ".join(name_parts[1:])  # everything else goes to last_name

        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid email")

        user = authenticate(username=user.username, password=password)
        if not user:
            raise forms.ValidationError("Invalid password")

        cleaned_data["user"] = user
        return cleaned_data
