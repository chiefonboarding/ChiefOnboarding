# Error logging
This is entirely optional, but if you want to catch errors comming from your instance, then Sentry is ready to be used for that. No system is ever bug-free. Errors happen. This is really useful if something happens with your instance and you want to give us a detailed log about it. You can share the error log and we can then fix it much quicker. Obviously, we are not connected to your Sentry account, so you will have to let us know about it!

You will have to provide a URL to send the requests to. This URL may be from the hosted version of Sentry or the on-premise one. Both will work just fine. 

1. Go to [sentry.io](https://sentry.io)
2. Sign up and then create a new 'Project'.
3. Select 'Django' and give it a name.
4. Copy the value of the DSN url. Example: `https://xxxxxx.ingest.sentry.io/xxxxxx`.

Example variable:

```ini
SENTRY_URL=https://xxxxxx.ingest.sentry.io/xxxxxx
```
