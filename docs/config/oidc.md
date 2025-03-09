# OIDC Single Sign-On (SSO)

To enable OIDC, you must enable "Allow users to login with OIDC" in the admin settings page at [https://example.com/admin/settings/general/](https://example.com/admin/settings/general/).

You may need the redirect URL for your Identity Provider (IdP). The `REDIRECT_URL` should be set to [https://example.com/api/auth/oidc\_login](https://example.com/api/auth/oidc_login).

If you set `OIDC_FORCE_AUTHN=True`, the login page will automatically redirect to the OIDC IdP.

## Role Mapping

In this example, we use CAS as the IdP and modify the `zoneinfo` field to display group information. You can see `OIDC_ROLE_PATH_IN_RETURN='zoneinfo'` is set accordingly.

If your groups (roles) are stored deeper in the JSON structure, like:

```json
{
    "A": "A",
    "B": {
        "roles": [
            "ROLE_A",
            "ROLE_B"
        ]
    }
}
```

You can set `OIDC_ROLE_PATH_IN_RETURN='B.roles'` using dots.

There are three patterns to map ChiefOnboarding's role with `OIDC_ROLE`:

1.  For `Admin`, apply `OIDC_ROLE_ADMIN_PATTERN` to `OIDC_ROLE`
2.  For `Manager`, apply `OIDC_ROLE_MANAGER_PATTERN` to `OIDC_ROLE`
2.  For `Newhire`, apply `OIDC_ROLE_NEW_HIRE_PATTERN` to `OIDC_ROLE`

`OIDC_ROLE_DEFAULT` is used to set other users' roles; you likely don't need to change it. If you don't want to use role mapping, simply leave it as a space.

If you do not want the OIDC provider to update roles, then you can disable it by setting `OIDC_ROLE_UPDATING` to `False`.

## Logout

Since this is an SSO implementation, we recommend setting `OIDC_LOGOUT_URL`. When you log out, it will redirect to the `OIDC_LOGOUT_URL`.

## Configuration example
Here's the updated configuration example:

```ini
OIDC_LOGIN_DISPLAY="Custom-OIDC"
OIDC_CLIENT_ID=XXXXX
OIDC_CLIENT_SECRET=XXXXXX
OIDC_AUTHORIZATION_URL=https://example.com/oidc/authorize
OIDC_TOKEN_URL=https://example.com/oidc/accessToken
OIDC_USERINFO_URL=https://example.com/oidc/profile
OIDC_LOGOUT_URL=https://example.com/cas/logout
OIDC_SCOPES='openid email name profile'
OIDC_FORCE_AUTHN=True
OIDC_ROLE_UPDATING=True
OIDC_ROLE_NEW_HIRE_PATTERN='^cn=Newhires.*'
OIDC_ROLE_ADMIN_PATTERN='^cn=Administrators.*'
OIDC_ROLE_MANAGER_PATTERN='^cn=Managers.*'
OIDC_ROLE_DEFAULT=3
OIDC_ROLE_PATH_IN_RETURN='groups'
```
