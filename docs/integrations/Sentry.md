# Sentry

Sentry is used for error tracking. No system is ever bug-free. Errors happen. If you want to track errors that come from your instance, then you can use Sentry for that. You will have to provide a URL to send the requests to. This URL may be from the hosted version of Sentry or the on-premise one. Both will work. 

1. Go to [sentry.io](https://sentry.io)
2. Sign up and then create a new 'Project'.
3. Select 'Django' and give it a name.
4. Copy the value of the DSN url. Example: `https://xxxxxx.ingest.sentry.io/xxxxxx`.

Example variable:
```
SENTRY_URL=https://xxxxxx.ingest.sentry.io/xxxxxx
```
