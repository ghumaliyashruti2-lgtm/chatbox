from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


from django import forms
from django.contrib.auth.models import User

from django import forms
from django.contrib.auth.models import User
import re

class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        error_messages={"min_length": "Password must be at least 8 characters"},
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # 1️⃣ Email validation first
        if email:
            if User.objects.filter(email=email).exists():
                self.add_error("email", "Email already exists")
                # stop further validation if email is invalid
                return cleaned_data
        else:
            # email field is empty or invalid, stop password validation
            return cleaned_data

        # 2️⃣ Password validation only if email is valid
        if password:
            pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
            if not re.match(pattern, password):
                self.add_error(
                    "password",
                    "Password must include uppercase, lowercase, number & special character"
                )

        # 3️⃣ Confirm password
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get("first_name", "")
        name_parts = full_name.strip().split()
        user.first_name = name_parts[0] if name_parts else ""
        user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
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


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data
