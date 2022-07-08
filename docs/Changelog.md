---
order: 30
---

# Changelog

## v2.0.0
* Completely new look
* Dropped most dependency for VueJS
* Support for custom integrations created by you!
* Time triggers can now be triggered at a custom time (used to be always 8 am)
* Slack doesn't depend on webhooks anymore - websocket is now supported as well
* Notifications on both the new hire and admin side
* Change channel where bot sends messages to
* Change admin to manager and vise versa
* Change email template
* Assign admin tasks in sequence to admin/manager instead of person
* Webhook support

BREAKING CHANGES:
* Scheduled access items will not be executed anymore - table is dropped and functionality has been replaced
* Slack account creation integration will be dropped due to dropped support from Slack. It can be put back, but requires some changes.
* API is currently dropped, but will be back later.

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
