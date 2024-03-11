# Oauth
If you need to use OAuth2 to get a token, then you will need to use this. Just create a prop called `oauth` and then in that use these properties:

`authenticate_url`

This is the url that is used to send the user to the login/authorize the connection (this should be a url to the third party). This is always a `GET` request. It expects an url here.

`access_token`

This is used when you come back to our site with a token. With that token, it will need to fetch an access token from the third party (and perhaps a refresh token). Format is an object like the `execute` part.

`refresh`

Used to refresh the token to get a new one, if this is not added, then it will assume that the token is permanent. Format is an object like the `execute` part.

`without_code`

Default: `False`. Enable this is a valid callback won't return a `code` query in the url. In some cases, we don't get it and also not need it.


## Redirect url
Most oauth providers will require you to put the redirect url in one of the links. Every integrations has a unique redirect url and you can get the correct one by using:
```
{{ redirect_url }}
```
in the `oauth` part.

## Saved credentials
When done, you should have gotten credentials to authenticate other urls. If you need a specific token, then you can call those by prefixing it with `oauth.`. For example:

```
{{ oauth.refresh_token }}
```


## Example
```json
"oauth": {
    "refresh": {
        "url": "https://oauth2.googleapis.com/token",
        "data": {
            "client_id": "{{ CLIENT_ID }}",
            "grant_type": "refresh_token",
            "client_secret": "{{ CLIENT_SECRET }}",
            "refresh_token": "{{ oauth.refresh_token }}"
        },
        "method": "POST"
    },
    "access_token": {
        "url": "https://oauth2.googleapis.com/token?client_id={{CLIENT_ID}}&client_secret={{CLIENT_SECRET}}&grant_type=authorization_code&redirect_uri={{redirect_url}}",
        "method": "POST"
    },
    "authenticate_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id={{CLIENT_ID}}&redirect_uri={{redirect_url}}&response_type=code&scope=https://www.googleapis.com/auth/admin.directory.user&access_type=offline&prompt=consent"
},
```
