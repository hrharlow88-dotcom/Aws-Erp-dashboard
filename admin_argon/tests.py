import json
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.template import Context
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse

from admin_argon.forms import (
    LoginForm,
    RegistrationForm,
    UserPasswordChangeForm,
    UserPasswordResetForm,
    UserSetPasswordForm,
)
from admin_argon.templatetags.admin_argon import (
    checkbox,
    clean_text,
    get_direction,
    neg_num,
    sum_number,
)
from admin_argon.utils import (
    JsonResponse,
    context_to_dict,
    get_menu_item_url,
    get_possible_language_codes,
    user_is_authenticated,
)


# ---------------------------------------------------------------------------
# utils.py tests
# ---------------------------------------------------------------------------
class JsonResponseTest(TestCase):
    def test_dict_data(self):
        resp = JsonResponse({"key": "value"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        self.assertEqual(json.loads(resp.content), {"key": "value"})

    def test_non_dict_safe_true_raises(self):
        with self.assertRaises(TypeError):
            JsonResponse([1, 2, 3])

    def test_non_dict_safe_false(self):
        resp = JsonResponse([1, 2, 3], safe=False)
        self.assertEqual(json.loads(resp.content), [1, 2, 3])

    def test_empty_dict(self):
        resp = JsonResponse({})
        self.assertEqual(json.loads(resp.content), {})

    def test_nested_dict(self):
        data = {"a": {"b": [1, 2]}}
        resp = JsonResponse(data)
        self.assertEqual(json.loads(resp.content), data)

    def test_custom_status_code(self):
        resp = JsonResponse({"err": "not found"}, status=404)
        self.assertEqual(resp.status_code, 404)


class GetPossibleLanguageCodesTest(TestCase):
    @patch("admin_argon.utils.translation.get_language", return_value="en-us")
    def test_language_with_dialect(self, _mock):
        codes = get_possible_language_codes()
        self.assertIn("en-US", codes)
        self.assertIn("en", codes)

    @patch("admin_argon.utils.translation.get_language", return_value="en")
    def test_language_without_dialect(self, _mock):
        codes = get_possible_language_codes()
        self.assertEqual(codes, ["en"])

    @patch("admin_argon.utils.translation.get_language", return_value="pt-br")
    def test_portuguese_brazil(self, _mock):
        codes = get_possible_language_codes()
        self.assertIn("pt-BR", codes)
        self.assertIn("pt", codes)

    @patch("admin_argon.utils.translation.get_language", return_value="zh_Hans")
    def test_underscore_replaced(self, _mock):
        codes = get_possible_language_codes()
        self.assertIn("zh-HANS", codes)
        self.assertIn("zh", codes)

    @patch("admin_argon.utils.translation.get_language", return_value="fr-fr")
    def test_same_language_and_dialect(self, _mock):
        codes = get_possible_language_codes()
        # When language == dialect, the code collapses to just the base,
        # but both the collapsed code and the base are added.
        self.assertEqual(codes, ["fr", "fr"])


class ContextToDictTest(TestCase):
    def test_plain_dict(self):
        d = {"key": "val"}
        self.assertEqual(context_to_dict(d), d)

    def test_django_context(self):
        ctx = Context({"a": 1, "b": 2})
        result = context_to_dict(ctx)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"], 2)

    def test_empty_context(self):
        ctx = Context({})
        result = context_to_dict(ctx)
        self.assertIsInstance(result, dict)


class UserIsAuthenticatedTest(TestCase):
    def test_authenticated_property(self):
        user = MagicMock(spec=[])
        user.is_authenticated = True
        self.assertTrue(user_is_authenticated(user))

    def test_not_authenticated_property(self):
        user = MagicMock(spec=[])
        user.is_authenticated = False
        self.assertFalse(user_is_authenticated(user))

    def test_authenticated_callable(self):
        user = MagicMock()
        user.is_authenticated = MagicMock(return_value=True)
        self.assertTrue(user_is_authenticated(user))

    def test_not_authenticated_callable(self):
        user = MagicMock()
        user.is_authenticated = MagicMock(return_value=False)
        self.assertFalse(user_is_authenticated(user))


class GetMenuItemUrlTest(TestCase):
    def test_string_url(self):
        self.assertEqual(get_menu_item_url("/some/path/", {}), "/some/path/")

    def test_none_url(self):
        self.assertIsNone(get_menu_item_url(None, {}))

    def test_dict_app_type(self):
        original = {"myapp": {"url": "/admin/myapp/"}}
        url = get_menu_item_url({"type": "app", "app_label": "myapp"}, original)
        self.assertEqual(url, "/admin/myapp/")

    def test_dict_model_type(self):
        original = {
            "myapp": {
                "models": [{"name": "mymodel", "url": "/admin/myapp/mymodel/"}]
            }
        }
        url = get_menu_item_url(
            {"type": "model", "app_label": "myapp", "model": "mymodel"}, original
        )
        self.assertEqual(url, "/admin/myapp/mymodel/")

    @patch("admin_argon.utils.reverse", return_value="/resolved/")
    def test_dict_reverse_type(self, _mock_reverse):
        url = get_menu_item_url({"type": "reverse", "name": "index"}, {})
        self.assertEqual(url, "/resolved/")


class SuccessMessageMixinTest(TestCase):
    def test_get_success_message(self):
        from admin_argon.utils import SuccessMessageMixin

        mixin = SuccessMessageMixin()
        mixin.success_message = "Created %(name)s"
        msg = mixin.get_success_message({"name": "item"})
        self.assertEqual(msg, "Created item")

    def test_empty_success_message(self):
        from admin_argon.utils import SuccessMessageMixin

        mixin = SuccessMessageMixin()
        mixin.success_message = ""
        msg = mixin.get_success_message({})
        self.assertEqual(msg, "")


# ---------------------------------------------------------------------------
# forms.py tests
# ---------------------------------------------------------------------------
class RegistrationFormTest(TestCase):
    def test_valid_form(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        }
        form = RegistrationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "Str0ngP@ss!",
            "password2": "DifferentPass1!",
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_missing_username(self):
        data = {
            "username": "",
            "email": "a@b.com",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_widget_classes(self):
        form = RegistrationForm()
        self.assertIn("form-control", form.fields["username"].widget.attrs["class"])
        self.assertIn("form-control", form.fields["email"].widget.attrs["class"])
        self.assertIn("form-control", form.fields["password1"].widget.attrs["class"])
        self.assertIn("form-control", form.fields["password2"].widget.attrs["class"])

    def test_duplicate_username(self):
        User.objects.create_user("existing", "e@e.com", "pass1234")
        data = {
            "username": "existing",
            "email": "new@example.com",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())


class LoginFormTest(TestCase):
    def test_widget_classes(self):
        form = LoginForm()
        self.assertIn("form-control", form.fields["username"].widget.attrs["class"])
        self.assertIn("form-control", form.fields["password"].widget.attrs["class"])

    def test_placeholder_values(self):
        form = LoginForm()
        self.assertEqual(
            form.fields["username"].widget.attrs["placeholder"], "Username"
        )
        self.assertEqual(
            form.fields["password"].widget.attrs["placeholder"], "Password"
        )


class UserPasswordResetFormTest(TestCase):
    def test_widget_class(self):
        form = UserPasswordResetForm()
        self.assertIn("form-control", form.fields["email"].widget.attrs["class"])

    def test_valid_email(self):
        form = UserPasswordResetForm(data={"email": "user@example.com"})
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        form = UserPasswordResetForm(data={"email": "notanemail"})
        self.assertFalse(form.is_valid())


class UserSetPasswordFormTest(TestCase):
    def test_widget_classes(self):
        user = User.objects.create_user("u1", "u1@test.com", "oldpass123")
        form = UserSetPasswordForm(user=user)
        self.assertIn(
            "form-control", form.fields["new_password1"].widget.attrs["class"]
        )
        self.assertIn(
            "form-control", form.fields["new_password2"].widget.attrs["class"]
        )


class UserPasswordChangeFormTest(TestCase):
    def test_widget_classes(self):
        user = User.objects.create_user("u2", "u2@test.com", "oldpass123")
        form = UserPasswordChangeForm(user=user)
        self.assertIn(
            "form-control", form.fields["old_password"].widget.attrs["class"]
        )
        self.assertIn(
            "form-control", form.fields["new_password1"].widget.attrs["class"]
        )
        self.assertIn(
            "form-control", form.fields["new_password2"].widget.attrs["class"]
        )

    def test_valid_change(self):
        user = User.objects.create_user("u3", "u3@test.com", "OldStr0ng!")
        form = UserPasswordChangeForm(
            user=user,
            data={
                "old_password": "OldStr0ng!",
                "new_password1": "NewStr0ng!1",
                "new_password2": "NewStr0ng!1",
            },
        )
        self.assertTrue(form.is_valid())

    def test_wrong_old_password(self):
        user = User.objects.create_user("u4", "u4@test.com", "OldStr0ng!")
        form = UserPasswordChangeForm(
            user=user,
            data={
                "old_password": "WrongOld!",
                "new_password1": "NewStr0ng!1",
                "new_password2": "NewStr0ng!1",
            },
        )
        self.assertFalse(form.is_valid())


# ---------------------------------------------------------------------------
# views.py tests
# ---------------------------------------------------------------------------
class SimplePageViewsTest(TestCase):
    def test_index_view(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pages/dashboard.html")

    def test_billing_view(self):
        resp = self.client.get("/billing/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pages/billing.html")

    def test_profile_view(self):
        resp = self.client.get("/profile/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pages/profile.html")

    def test_tables_view(self):
        resp = self.client.get("/tables/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pages/tables.html")

    def test_rtl_view(self):
        resp = self.client.get("/rtl/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pages/rtl.html")

    def test_vr_view(self):
        resp = self.client.get("/vr/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "pages/virtual-reality.html")


class RegisterViewTest(TestCase):
    def test_get_register_page(self):
        resp = self.client.get("/accounts/register/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accounts/sign-up.html")
        self.assertIn("form", resp.context)

    def test_post_valid_registration(self):
        resp = self.client.post(
            "/accounts/register/",
            {
                "username": "testuser",
                "email": "test@test.com",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, "/accounts/login/")
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_post_invalid_registration(self):
        resp = self.client.post(
            "/accounts/register/",
            {
                "username": "",
                "email": "test@test.com",
                "password1": "pass",
                "password2": "different",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accounts/sign-up.html")


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("loginuser", "l@t.com", "Str0ngP@ss!")

    def test_get_login_page(self):
        resp = self.client.get("/accounts/login/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accounts/sign-in.html")

    def test_valid_login(self):
        resp = self.client.post(
            "/accounts/login/",
            {"username": "loginuser", "password": "Str0ngP@ss!"},
        )
        self.assertEqual(resp.status_code, 302)

    def test_invalid_login(self):
        resp = self.client.post(
            "/accounts/login/",
            {"username": "loginuser", "password": "wrong"},
        )
        self.assertEqual(resp.status_code, 200)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("logoutuser", "lo@t.com", "Str0ngP@ss!")

    def test_logout_redirects(self):
        self.client.login(username="logoutuser", password="Str0ngP@ss!")
        resp = self.client.get("/accounts/logout/")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, "/accounts/login/")


class PasswordResetViewTest(TestCase):
    def test_get_password_reset_page(self):
        resp = self.client.get("/accounts/password-reset/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accounts/password_reset.html")


class PasswordChangeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("pwuser", "pw@t.com", "OldStr0ng!")
        self.client.login(username="pwuser", password="OldStr0ng!")

    def test_get_password_change_page(self):
        resp = self.client.get("/accounts/password-change/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "accounts/password_change.html")


# ---------------------------------------------------------------------------
# templatetags/admin_argon.py tests
# ---------------------------------------------------------------------------
class CleanTextFilterTest(TestCase):
    def test_removes_newlines(self):
        self.assertEqual(clean_text("hello\nworld"), "hello world")

    def test_multiple_newlines(self):
        self.assertEqual(clean_text("a\n\nb"), "a  b")

    def test_no_newlines(self):
        self.assertEqual(clean_text("hello world"), "hello world")

    def test_empty_string(self):
        self.assertEqual(clean_text(""), "")


class CheckboxFilterTest(TestCase):
    def test_strips_td_tags(self):
        html = "<td>content</td>"
        self.assertEqual(checkbox(html), "content")

    def test_strips_td_with_attrs(self):
        html = '<td class="action-checkbox">content</td>'
        self.assertEqual(checkbox(html), "content")

    def test_no_td_tags(self):
        html = "<span>content</span>"
        self.assertEqual(checkbox(html), "<span>content</span>")


class GetDirectionTest(TestCase):
    def test_ltr_direction(self):
        ctx = Context({"LANGUAGE_BIDI": False})
        result = get_direction(ctx)
        self.assertEqual(result["panel"], "text-left")
        self.assertEqual(result["notify"], "right")
        self.assertEqual(result["float"], "float-right")
        self.assertEqual(result["reverse_panel"], "text-right")
        self.assertEqual(result["nav"], "ml-auto")

    def test_rtl_direction(self):
        ctx = Context({"LANGUAGE_BIDI": True})
        result = get_direction(ctx)
        self.assertEqual(result["panel"], "text-right")
        self.assertEqual(result["notify"], "left")
        self.assertEqual(result["float"], "")
        self.assertEqual(result["reverse_panel"], "text-left")
        self.assertEqual(result["nav"], "mr-auto")


class SumNumberFilterTest(TestCase):
    def test_basic_sum(self):
        self.assertEqual(sum_number(5, 3), 8)

    def test_zero(self):
        self.assertEqual(sum_number(0, 0), 0)

    def test_negative(self):
        self.assertEqual(sum_number(-1, 1), 0)


class NegNumFilterTest(TestCase):
    def test_basic_subtraction(self):
        self.assertEqual(neg_num(10, 3), 7)

    def test_zero(self):
        self.assertEqual(neg_num(0, 0), 0)

    def test_negative_result(self):
        self.assertEqual(neg_num(1, 5), -4)


# ---------------------------------------------------------------------------
# apps.py tests
# ---------------------------------------------------------------------------
class AppConfigTest(TestCase):
    def test_app_config(self):
        from django.apps import apps

        config = apps.get_app_config("admin_argon")
        self.assertEqual(config.name, "admin_argon")
        self.assertEqual(config.icon, "fa fa-user")
        self.assertEqual(config.default_auto_field, "django.db.models.BigAutoField")


# ---------------------------------------------------------------------------
# urls.py tests
# ---------------------------------------------------------------------------
class UrlPatternsTest(TestCase):
    def test_index_url_resolves(self):
        url = reverse("index")
        self.assertEqual(url, "/")

    def test_billing_url(self):
        self.assertEqual(reverse("billing"), "/billing/")

    def test_profile_url(self):
        self.assertEqual(reverse("profile"), "/profile/")

    def test_tables_url(self):
        self.assertEqual(reverse("tables"), "/tables/")

    def test_rtl_url(self):
        self.assertEqual(reverse("rtl"), "/rtl/")

    def test_vr_url(self):
        self.assertEqual(reverse("vr"), "/vr/")

    def test_login_url(self):
        self.assertEqual(reverse("login"), "/accounts/login/")

    def test_logout_url(self):
        self.assertEqual(reverse("logout"), "/accounts/logout/")

    def test_register_url(self):
        self.assertEqual(reverse("register"), "/accounts/register/")

    def test_password_change_url(self):
        self.assertEqual(reverse("password_change"), "/accounts/password-change/")

    def test_password_reset_url(self):
        self.assertEqual(reverse("password_reset"), "/accounts/password-reset/")
