from django.shortcuts import render, redirect
from admin_argon.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, UserPasswordChangeForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, PasswordChangeView
from django.contrib.auth import logout


def _render_page(request, template, segment):
  return render(request, template, {'segment': segment})


PAGE_REGISTRY = {
    'index':   ('pages/dashboard.html',         'dashboard'),
    'billing': ('pages/billing.html',            'billing'),
    'profile': ('pages/profile.html',            'profile'),
    'tables':  ('pages/tables.html',             'tables'),
    'rtl':     ('pages/rtl.html',                'rtl'),
    'vr':      ('pages/virtual-reality.html',    'vr'),
}


def index(request):
  return _render_page(request, *PAGE_REGISTRY['index'])

def billing(request):
  return _render_page(request, *PAGE_REGISTRY['billing'])

def profile(request):
  return _render_page(request, *PAGE_REGISTRY['profile'])

def tables(request):
  return _render_page(request, *PAGE_REGISTRY['tables'])

def rtl(request):
  return _render_page(request, *PAGE_REGISTRY['rtl'])

def vr(request):
  return _render_page(request, *PAGE_REGISTRY['vr'])

def register(request):
  if request.method == 'POST':
    form = RegistrationForm(request.POST)
    if form.is_valid():
      form.save()
      print("Account created successfully!")
      return redirect('/accounts/login/')
    else:
      print("Registration failed!")
  else:
    form = RegistrationForm()

  context = { 'form': form }
  return render(request, 'accounts/sign-up.html', context)


class UserLoginView(LoginView):
  template_name = 'accounts/sign-in.html'
  form_class = LoginForm


class UserPasswordResetView(PasswordResetView):
  template_name = 'accounts/password_reset.html'
  form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(PasswordResetConfirmView):
  template_name = 'accounts/password_reset_confirm.html'
  form_class = UserSetPasswordForm

class UserPasswordChangeView(PasswordChangeView):
  template_name = 'accounts/password_change.html'
  form_class = UserPasswordChangeForm

def user_logout_view(request):
  logout(request)
  return redirect('/accounts/login/')