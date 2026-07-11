from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm, PasswordResetForm, UsernameField
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


def _widget_attrs(css_class, placeholder):
    return {'class': css_class, 'placeholder': placeholder}


def _fc(placeholder):
    return _widget_attrs('form-control', placeholder)


def _fc_lg(placeholder):
    return _widget_attrs('form-control form-control-lg', placeholder)


def _password_field(placeholder, label, max_length=50, css_class='form-control'):
    return forms.CharField(
        max_length=max_length,
        widget=forms.PasswordInput(attrs=_widget_attrs(css_class, placeholder)),
        label=label,
    )


class RegistrationForm(UserCreationForm):
  password1 = forms.CharField(
      label=_("Password"),
      widget=forms.PasswordInput(attrs=_fc('Password')),
  )
  password2 = forms.CharField(
      label=_("Password Confirmation"),
      widget=forms.PasswordInput(attrs=_fc('Password Confirmation')),
  )

  class Meta:
    model = User
    fields = ('username', 'email', )

    widgets = {
      'username': forms.TextInput(attrs=_fc('Username')),
      'email': forms.EmailInput(attrs=_fc('Email')),
    }

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs=_fc_lg('Username')))
    password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs=_fc_lg('Password')))


class UserPasswordResetForm(PasswordResetForm):
  email = forms.EmailField(widget=forms.EmailInput(attrs=_fc('Email')))

class UserSetPasswordForm(SetPasswordForm):
    new_password1 = _password_field('New Password', 'New Password')
    new_password2 = _password_field('Confirm New Password', 'Confirm New Password')


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = _password_field('Old Password', 'Old Password')
    new_password1 = _password_field('New Password', 'New Password')
    new_password2 = _password_field('Confirm New Password', 'Confirm New Password')