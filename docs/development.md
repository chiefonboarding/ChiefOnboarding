# Development

If you want to contribute or just play around with the source code, the first step would be to download the source code. 

Then move the example environment file to the real one:

```
cp .example_env .env
```

Then run this to get it all up and running: 

```bash
docker-compose up
```

Please note that it could take a few seconds everything is set up. Ignore any error messages you see, this is generally because the database hasn't been migrated yet. It will do that at the end automatically.

Once it's ready, go to [http://0.0.0.0:8000](http://0.0.0.0:8000) and you should see the setup screen. Fill in the details and you will get a bunch of dummy data as well!

## Enable better logging
If you want to start developing/debugging and need more verbose log messages, then you can enable debug log messages with this environment setting:

```ini
DEBUG_LOGGING = True
```

## Adding a new language

If you want to add a new language, then you will have to follow these steps:

Replace `lang` with the shortname of your language (e.g. `nl`, `en`, or `es`) in the command below

```bash
docker-compose run --rm web django-admin makemessages -l lang
```

It will generate a new file for you to fill in. It's a `.po` that you can edit (with a text editor or through one of the many tools).

Up next, you will need to add the language to the list of languages. Go to `back/back/settings.py` and add your language to this array `https://github.com/chiefonboarding/ChiefOnboarding/blob/v2.0/back/back/settings.py#L371`. That way, it will show up in the lists to choose the language.


## Updating existing translations
Simply run this command and it will update all current translations:

```bash
docker-compose run --rm web django-admin makemessages -a
```
