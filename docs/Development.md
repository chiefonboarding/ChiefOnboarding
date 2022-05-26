---
order: 70
---

# Development

If you want to contribute or just play around with the source code, the first step would be to download the source code. Then run this to get it all up and running: 

```
docker-compose up
```

Please note that it could take a few seconds everything is set up. Ignore any error messages you see, this is generally because the database hasn't been migrated yet. It will do that at the end automatically.
Once it's ready, it should also have a bunch of test data in there to get you started quickly.

Once it's ready, go to [http://0.0.0.0:8000](http://0.0.0.0:8000) and you should see the login screen.

The login credentials are:

```
Email: admin@example.com
Password: admin
```
