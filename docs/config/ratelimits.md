# Ratelimits of failed login attempts
By default, ChiefOnboarding uses allows users to attempt 10 times before the user gets blocked by IP. You can change the defaults:

`AXES_ENABLED`

Default: `True`. Set to `False` if you want to disable blocking users from trying again (not recommended).

`AXES_FAILURE_LIMIT`

Default: `10`. Sets the amount of attempts before user gets blocked.

`AXES_COOLOFF_TIME`

Default: `24` (in hours). After 24 hours the IP address gets cleared again.

In some cases, you might have issues with proxies. For those, please check this: [https://django-axes.readthedocs.io/en/latest/4_configuration.html#configuring-reverse-proxies](https://django-axes.readthedocs.io/en/latest/4_configuration.html#configuring-reverse-proxies).

These can be configured:

`AXES_IPWARE_PROXY_COUNT`

`AXES_IPWARE_META_PRECEDENCE_ORDER`

ChiefOnboarding specific one: 

`AXES_USE_FORWARDED_FOR`

Default: `True`. In many cases ChiefOnboarding is deployed behind a proxy (i.e. Docker or Heroku reverse proxy). This allows you to get the IP address from the refer header. Without this, it would log internal ip addresses, which means that users will share the same ip address and get locked out unintentionally.
This mimics the code in the `note` part of the documentation from django-axes.
It's setting: `HTTP_X_FORWARDED_FOR` and `REMOTE_ADDR` in the `AXES_IPWARE_META_PRECEDENCE_ORDER`.
