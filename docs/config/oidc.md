# OIDC Single Sign-On (SSO)

Please read the allauth docs here: [OIDC setup config](https://docs.allauth.org/en/latest/socialaccount/providers/openid_connect.html)

You can add that config in your environment variables under `SSO_PROVIDERS` (dict).

## Role Mapping

By default `OIDC_ROLE_PATH_IN_RETURN` is set to an empty string. You should change it depending on where it can find the info for mapping the user info.

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

1.  For `Admin`, apply `OIDC_ROLE_ADMIN_PATTERN`
2.  For `Manager`, apply `OIDC_ROLE_MANAGER_PATTERN`
2.  For `Newhire`, apply `OIDC_ROLE_NEW_HIRE_PATTERN`

You can use regex to match the pattern.

The default is a "other", this is a user with only access to the colleagues and resources page (resources page will be empty as none are assigned by default).

## Configuration example
Here's the updated configuration example:

```
SOCIALACCOUNT_PROVIDERS={"openid_connect": {"APPS": [{"provider_id": "other-server",...}]}}
SSO_AUTO_CREATE_USER=True # disable this if you don't want to create new users, you can ignore the ones below in that case
OIDC_ROLE_NEW_HIRE_PATTERN='^cn=Newhires.*'
OIDC_ROLE_ADMIN_PATTERN='^cn=Administrators.*'
OIDC_ROLE_MANAGER_PATTERN='^cn=Managers.*'
OIDC_ROLE_PATH_IN_RETURN='groups'
ALLAUTH_PROVIDERS="openid_connect"
```

