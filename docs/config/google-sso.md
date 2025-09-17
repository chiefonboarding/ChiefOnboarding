# Google SSO
This will allow you to use the 'Log in with Google' button on the log in page.

1. Go to [https://console.developers.google.com/apis/consent](https://console.developers.google.com/apis/consent) and make sure you are logged in as the admin of the Google organization.
2. Create a new 'Project' and give it a fancy name. Once it's created make sure you are in that project (you can see that in the top bar).
3. You will be asked for what type of app you want to register. Choose 'Intern', only people from your organization should log in to your app. Click on 'Create'.
4. Fill in the details accordingly. You don't have to change the scopes, those are fine. Under 'Authorized domains', fill in your own site url and the url of the ChiefOnboarding instance.
5. Click on 'Create'. You will be taken back to the page you previously landed on.

We just set up our authentication screen for people that want to sign in. Up next, we need to create credentials that we can put into the ChiefOnboarding instance, so we can actually show that authentication dialog.

6. Go to [https://console.developers.google.com/apis/credentials](https://console.developers.google.com/apis/credentials)
7. Click on 'Create credentials' at the top of the page and choose Client-ID OAuth.
8. You will be asked for the type of app. Pick 'Web application'.
9. Under "Authorized JavaScript-sources" enter the domain name of where ChiefOnboarding is running on.
10. Under "Authorized redirect-URLs" enter this: `https://YOURDOMAIN/accounts/google/login/callback/`.
11. Click on 'Create' and you will get the `Client-ID` and `Client-secret` that you need to add to your environment variables:

```
ALLOW_GOOGLE_SSO=True
GOOGLE_SSO_CLIENT_ID=xxxxx
GOOGLE_SSO_SECRET=xxxxx
```
Optional if you want to auto create the user if they do not exist yet (they will be an "other" user, no admin rights):
```
SSO_AUTO_CREATE_USER=True
```

If you want to completely disable normal login with username/password, set:
```
ALLOW_LOGIN_WITH_CREDENTIALS=False
```
