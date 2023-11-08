from importlib import import_module

from allauth.account import views as allauth_views
from allauth.mfa import views as allauth_mfa_views
from allauth.socialaccount import providers
from django.urls import include, path, re_path

from . import views

urlpatterns = [
    # allauth urls
    path("", allauth_views.login, name="account_login"),
    # mocking this one, it's necessary for loading the login page, but we actually never
    # use it, so just loop it back to the login page out of safety.
    path("", allauth_views.login, name="account_signup"),
    path("", allauth_views.login, name="account_signup"),
    path(
        "password/reset/", allauth_views.password_reset, name="account_reset_password"
    ),
    path(
        "password/reset/done/",
        allauth_views.password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        allauth_views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        allauth_views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
    path("authenticate/", allauth_mfa_views.authenticate, name="mfa_authenticate"),
    path(
        "reauthenticate/", allauth_views.reauthenticate, name="account_reauthenticate"
    ),
    path("logout/", allauth_views.LogoutView.as_view(), name="logout"),
    path(
        "redirect/", views.LoginRedirectView.as_view(), name="logged_in_user_redirect"
    ),
    path("social/", include("allauth.socialaccount.urls")),
]

# Provider urlpatterns, as separate attribute (for reusability).
provider_urlpatterns = []
provider_classes = providers.registry.get_class_list()

# We need to move the OpenID Connect provider to the end. The reason is that
# matches URLs that the builtin providers also match.
provider_classes = [cls for cls in provider_classes if cls.id != "openid_connect"] + [
    cls for cls in provider_classes if cls.id == "openid_connect"
]
for provider_class in provider_classes:
    try:
        prov_mod = import_module(provider_class.get_package() + ".urls")
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, "urlpatterns", None)
    if prov_urlpatterns:
        provider_urlpatterns += prov_urlpatterns

urlpatterns += provider_urlpatterns
