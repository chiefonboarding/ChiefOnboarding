# Changelog

## v2.1.1 (2023-03-26)
* add feature to make test integration active

## v2.1.0 (2023-03-26)
* Improved live builder for both normal requests and sync options
* Many bug fixes
* Moved docs to VitePres
* Add option to mask secret initial data forms
* Integration tracker
* global search

BREAKING CHANGES:
* integrations now use user defined status_code to check on instead of the raise for 400 exception.

## v2.0.0
* Completely new look
* Moved from SPA back to MPA (dropped almost all javascript requirements)
* Support for custom integrations and webhooks created by you (https://integrations.chiefonboarding.com / https://github.com/chiefonboarding/ChiefOnboarding/blob/v2.0/docs/Integrations.md)!
* Sequence timed based triggers can now be triggered at a custom time (used to be always at 8 am)
* Slack doesn't need to depend on webhooks anymore - websocket is now supported as well (so you can also use it without having a public access point).
* Notifications on both the new hire and admin side on various actions
* Change channel where bot sends messages to
* Change admin to manager and vise versa
* Change email template
* Assign admin tasks in sequence to admin/manager instead of a specific person
* Docs have been updated and moved to the ChiefOnboardig repo (instead of a standalone repo)

BREAKING CHANGES:

* Scheduled access items that have been scheduled on the old version will not be executed anymore - table is dropped and functionality has been replaced
* API has breaking changes. Please see the dedicated API page for that.
* Some urls will not be accessible (like preboarding links). I am not setting up a redirect for this. These will return 404.
* Slack account creation will temporarily be removed. You can add it back when you go to our integrations site (see above). If you need the old key, then you can find it in Slack under your apps list (api.slack.com).
* Google account creation will be temporarily removed. Record will still be in the database and will be available for use when we create this integration again. You could also remove this integration before migrating if you want to.
* Selectboxes have been dropped temporarily from forms. Those will be gone after migration.
* You can update Slack to use the internal websocket instead of the HTTPS calls webhooks. That way, you remove one open endpoint (technically, you could use the app now with Slack behind a VPN). Webhooks is the default as we have noticated that they are more stable.
* SLACK BOT: Under "Interactivity & Shortcuts" in the config of your bot (https://api.slack.com/apps), change "callback" to "bot" in the URL. It should now be the same URL as you have under "Event Subscriptions". You will also need to change the redirect url. Change "api" to "admin" in the url and save it.
* Buttons posted in Slack before this migrations might become invalid.

## v1.2.23
* Fix email default from field for password reset
* Fix not being able to remove external messages (slack/email/text)

## v1.2.22
* Fix related to v.1.2.20

## v1.2.21
* Bump Django version

## v1.2.20
* Fix bug with sending custom email (replacing variables)

## v1.2.19
* Fix render database not in same region as app

## v1.2.18
* Remove DO as DO won't work with Django Q (no support for multiprocessors). For reference: https://www.digitalocean.com/community/questions/app-platform-multiprocessing-python?answer=69003
* Fixed Render to work with supervisor setup (no need to create an extra worker).
* Fixed Docker hub link.

## v1.2.17
* Forcing Python 3.7 to avoid SemLock error on DO/Render

## v1.2.16
* Django version update
* Fix resources in Slack

## v1.2.15
* Limit auth with url only to new hires
* Fix missing import
* Fix Slack authentication bug

## v1.2.14
* Remove google delete user

## v1.2.13
* Add deploy to DigitalOcean button
* Add deploy to Render button

## v1.2.12
* healthcheck url + allowed hosts fix
* Update docker image number

## v1.2.11
* additional update regarding v1.2.10

## v1.2.10
* Update slack add bot redirect button - remove legacy bot permissions

## v1.2.9
* Fix bug with adding introduction/appointment items

## v1.2.8
* Remove old signals file (old setup)
* Fix not being able to add to do items through 'add sequence' button
* Fix showing empty 'to do' conditions on new hire timeline

## v1.2.7
* Adding default username/password to dev docker-compose file
* Adding migrate cache table to dev docker-compose file
* Adding `node_modules` to gitignore
* Updates for Django Q. Stop having it redo every failing task indefinitely.

## v1.2.6
* Show error message when trying to send Slack test message without Slack account attached
* Fix showing preboarding preview part in a sequence
* Fix Slack syncing issue
* Update Django dep to newest version
* Update Docker version number (routine task)
* Fix showing old data in sequences (when adding a new one)

## v1.2.5
* Fix docker copy command

## v1.2.4
* Simplify docker setup (remove folders that are not necessary in container)

## v1.2.3
* Putting new hire start date further in the future (fixtures)
* Fix for blocking collectstatic on restart of container
* Enforcing email address of admin account to be lowercase. The email address would always be registered as lowercase and could therefore output incorrect info (on first run - creating admin account).
* Updated Docker version

## v1.2.2
* Another docker build fix

## v1.2.1
* A docker build fix 

## v1.2.0
* TOTP 2FA support. You can now use andOTP, Aegis authenticator, Google authenticator, Authy or any other OTP app that you use to set up 2FA (with QR code). 
* New editor and video support TipTap. We now support native video upload to S3. It will show up as a video in the portal and as a normal link in Slack.
* SMTP support
* Refactor Docker setup. Swapping Celery with Django Q. All running with supervisor now. Redis is now deprecated.

## v1.1.0
* Docker image
* Heroku deployment

## v1.0.0
* Automatically add new hires when they join Slack (optionally)
* Subject to custom email message. Used to be "Here is a quick update"
* Default sequences. Sequences that are always added to new hires by default.
