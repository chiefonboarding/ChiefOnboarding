# Email

ChiefOnboarding is using the [django-anymail](https://github.com/anymail/django-anymail) package to support a wide [variety of email providers](https://anymail.readthedocs.io/en/stable/esps/) (Sparkpost is not supported in ChiefOnboarding).

If you want to enable emails (this is highly recommended), then you will first have to set the from email and choose one of the providers:

Example for the `email header` variable:

```
DEFAULT_FROM_EMAIL=Your company onboarding <onboarding@whatever.com>
```

Up next, you will have to pick your favorite email provider and add the required environment variables:

* Postmark:
```
POSTMARK_KEY=XXXXXXXXXXX
```
* Mailgun
```
MAILGUN_KEY=XXXXXXXXXXX
MAILGUN_DOMAIN=XXXXXXXXXXX
```
* Mailjet:
```
MAILJET_API_KEY=XXXXXXXXXXX
MAILJET_SECRET_KEY=XXXXXXXXXXX
```
* Mandrill:
```
MANDRILL_API_KEY=XXXXXXXXXXX
```
* SendGrid:
```
SENDGRID_KEY=XXXXXXXXXXX
```
* Sendinblue:
```
SENDINBLUE_KEY=XXXXXXXXXXX
```

* SMTP:
```
EMAIL_HOST=smtp.chiefonboarding.com
EMAIL_PORT=587
EMAIL_HOST_USER=exampleuser
EMAIL_HOST_PASSWORD=examplePass
EMAIL_USE_TLS=True
EMAIL_USE_SSL=True
```
For SMTP, you only need to set either `EMAIL_USE_TLS` OR `EMAIL_USE_SSL` to `True`. If you set both, then it will likely not send out any emails.
