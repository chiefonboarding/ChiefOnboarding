# Email
If you want to send emails to anyone, then you will need to add a provider. Technically, if you are using a VPS, you could start selfhosting your own SMTP server, however we recommend against that. In any case, you need to set up the email environment variables if you want to start sending any emails.

ChiefOnboarding is using the [django-anymail](https://github.com/anymail/django-anymail) package to support a wide [variety of email providers](https://anymail.readthedocs.io/en/stable/esps/) (Sparkpost is not supported in ChiefOnboarding).

If you want to enable emails (this is highly recommended), then you will first have to set the from email and choose one of the providers below or go with SMTP and use pretty much any provider.

Example for the `email header` variable:

```ini
DEFAULT_FROM_EMAIL=Your company onboarding <onboarding@whatever.com>
```

Email providers:

* Postmark:
```ini
POSTMARK_KEY=XXXXXXXXXXX
```
* Mailgun
```ini
MAILGUN_KEY=XXXXXXXXXXX
MAILGUN_DOMAIN=XXXXXXXXXXX
```
* Mailjet:
```ini
MAILJET_API_KEY=XXXXXXXXXXX
MAILJET_SECRET_KEY=XXXXXXXXXXX
```
* Mandrill:
```ini
MANDRILL_API_KEY=XXXXXXXXXXX
```
* SendGrid:
```ini
SENDGRID_KEY=XXXXXXXXXXX
```
* Sendinblue:
```ini
SENDINBLUE_KEY=XXXXXXXXXXX
```

* SMTP:
```ini
EMAIL_HOST=smtp.chiefonboarding.com
EMAIL_PORT=587
EMAIL_HOST_USER=exampleuser
EMAIL_HOST_PASSWORD=examplePass
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
```
For SMTP, you only need to set either `EMAIL_USE_TLS` OR `EMAIL_USE_SSL` to `True`. If you set both, then it will likely not send out any emails.

### Custom email template
You can set your own email template if you want. You can see the default one here: https://github.com/chiefonboarding/ChiefOnboarding/blob/master/back/users/templates/email/base.html

Some things are rendered dynamically. You can use this as an example:

```html
{% autoescape off %}
{% for i in content %}
  {% if i.type == 'paragraph' %}
    <p>{{i.data.text|personalize:user}}</p>
  {% endif %}
  {% if i.type == 'header' %}
    <h{{ i.data.level }}>{{ i.data.text|personalize:user }}</h{{ i.data.level }}>
  {% endif %}
  {% if i.type == 'list' %}
    {% if i.data.style == "ordered" %}
      <ol>
    {% else %}
      <ul>
    {% endif %}
    {% for j in i.data.items %}
      <li>{{ j.content|personalize:user }}</li>
    {% endfor %}
    {% if i.data.style == "ordered" %}
      </ol>
    {% else %}
      </ul>
    {% endif %}
  {% endif %}
  {% if i.type == 'quote' %}
     {{i.data.text|personalize:user}}
  {% endif %}
  {% if i.type == 'image' %}
    <img src="{{ i.data.file.url }}" />
  {% endif %}
  {% if i.type == 'file' %}
      <a href="{{ j.data.file.url }}">{{ i.data.file.name }}</a><br />
  {% endif %}
  {% if i.type == 'button' %}
    <a href="{{ i.data.url }}">{{i.data.text|personalize:user}}</a>
  {% endif %}
  {% if i.type == 'hr' %}
    <hr />
  {% endif %}
{% endfor %}
{% endautoescape %}
```

Don't change whatever is within the brackets. Feel free to customize everything around it however you would like!
