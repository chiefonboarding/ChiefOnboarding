---
order: 65
---

ChiefOnboarding is build on top of Django (Python). It's mostly a "boring" app in the case that we don't use any type of frontend framework to decouple the frontend from the backend. It does use some sprinkles of JavaScript to create some moving elements. There is some HTMX, VueJS, jQuery, Bootstrap JS and a few other scripts.

A few things you should know about ChiefOnboarding:

- It uses Pytest for testing the code. For object creation, it uses `factoryboy`. You will find `factory.py` in almost every app.

- It relies heavily on background tasks. You can find those tasks in the `tasks.py` files in the apps folders. Especially the Slack bot and the `Sequence`s use those a lot.  

- Supervisord is set up for docker-compose. It will run two processes: the background worker (`Django-Q`) and `python manage.py runserver` for the server.

- Sequences are basically blueprints for new hires. The `Conditions` that are in there are all connected to the `Sequence`. Once a sequence gets assigned to a new hire, it will *duplicate* the `Condition` and assign it directly to the `User` model. This means that if an admin would change a `Condition` in a `Sequence`, then that won't affect new hires that are currently going through sequences.
There is one caveat with that though: if a template gets changes (i.e. a to do item or resource), then that will reflect for all people that don't have a custom one. Once you make changes to a template in a sequence, then it becomes a custom item and those items will not update when you update the original one.


Here is an overview of the database models of ChiefOnboarding:

![ChiefOnboarding models](static/database-design.png)


## Folder structure

In the root of the repo, there are a bunch of files and folder. The files are mostly there for deployment and development. The `bin` folder is purely for `Heroku` to generate the messages necessary for enabling multilanguage.The `.github/workflows` folder probably speaks for itself, that's for running workflows (tests, deploy to Docker, etc). The `docs` folder represents all the docs that are shown at https://docs.chiefonboarding.com. The `back` folder is where the actual application lives.

### back/admin
In this folder you will find only things that are mainly used by admins. These are all templates (`to_do`, `resources`, `introductions`, `appointments`, `badges`, `preboarding`), people options (`back/admin/people/views.py` and `back/admin/people/new_hire_views.py` for new hires), `admin_tasks` (things colleagues need to d for new hires), `sequences`, and `settings` (global as well as personal).

### back/back
This is just the core app that Django creates by default. You will find the `settings.py` file in there and the base `urls.py` file.

### back/fixtures
These are the default fixtures that are used for a limited part of testing and mostly for loading dummy and default data once someone installs ChiefOnboarding. This happens for both local developing and in production.

### back/locale
This is were all translations are stored.

### back/misc
This folder is pretty much used for everything that doesn't fit anywhere else. For example, uploading to object storage is used throughout the platform and isn't attached to anything specific. 

### back/new_hire
This covers the new hire portal. 

### back/organization
When someone installs ChiefOnboarding, it will create one `Organization` by default. You can see this as the `settings` model for the site. Everything that is configurable by the admins (i.e. color scheme, default email template and slack settings are all stored in the `Organization`. You can call the object for this everywhere, using `org`.

### back/slack_bot
This is used only for the Slack bot. For local development, there is an option to enable websocket support, though it can be a bit flaky.

### back/static
This is where all static files are stored. Things like CSS, JavaScript and images.

### back/user_auth
This is for authenticating the user. Be it through SSO or plain username/password. ChiefOnboarding mostly relies on the Django authentication module (and therefore uses sessions). `django-axes` is also installed to prevent brute-force attacks.

### back/users
This is where the `User` model can be found. It has been put in a separate folder as the `User` model contains all sorts of user accounts (i.e. new hire, admin, manager). Those are differenciated through an option field on the model.


