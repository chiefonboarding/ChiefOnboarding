# ChiefOnboarding

ChiefOnboarding is a free and open source employee onboarding platform. You can onboarding new hires through Slack or the dashboard. 

Documentation: [https://docs.chiefonboarding.com](https://docs.chiefonboarding.com)

## Features
- **Automatically provision user accounts**, such as Slack and Google (more integrations coming soon!)
- **Pre-boarding**: onboarding doesn't start on day 1, it starts before that. Build pre-boarding pages to welcome new hires before they start.
- **To do items**: keep track of the things that your new hires need to do and allow them to fill in forms.
- **Resources**: let them search through the knowledge base and complete courses so they are quickly up to speed with colleagues.
- **Sequences**: drip feeding items over time or based on the completion of a to do item. Avoid the overwhelming feeling.  
- **Badges**: reward new hires for the things they have done. This also helps to keep them motivated.
- **Introductions**: introduce people new hires should know.  
- **Admin to do items**: collaborate with colleagues on things that need to be done for the new hire.
- **Multilingual** (WIP): English, Dutch, Portuguese, German, Turkey, French, Spanish, and Japanese are all supported.
- **Timezones**: It doesn't matter where your new hire lives. You can adjust the timezone per new hire, so they don't get messages in the middle of the night!
- **Slack bot and dashboard**: your new hires can use the dashboard or the Slack bot. Both provide all features and can be used standalone.
- **Customizable**: use your logo, add your color scheme and even customize the bot to your liking. No one will know you are using ChiefOnboarding.
- **Transparency, freedom, and privacy**: ChiefOnboarding is completely open-source and licensed under MIT.
- Host it yourself on your own infrastructure or [let us host it for you](https://chiefonboarding.com/pricing)!


## Technical features
- Easy deployment through Docker (server recommendation is at least 2GB of RAM and 1 vCPU).
- Build on Django (version 3.1.x) with NuxtJS (version 2.14.x) as the front end (VueJS).
- Celery is used for background tasks.
- File storage is done through the S3 adapter. You can use AWS, but it's compatible with other object storages that follow S3 standards. 
- Twilio is used for sending text messages.
- Anymail is used for sending emails. You can choose between a wide variety of [email providers](https://anymail.readthedocs.io/en/stable/esps/#supported-esps). 
- Let's encrypt will automatically be set up for a secure connection.

## Deployment
Deploy ChiefOnboarding easily through **Docker** or on **Heroku**. Please see [the documentation for full details](https://docs.chiefonboarding.com).

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/chiefonboarding/ChiefOnboarding/tree/deploy)

## Security issues
Please do not create an issue if you found a potential security issue. Email me directly at security@chiefonboarding.com and I will get it resolved ASAP.

## License
This project is licensed under the AGPLv3 License - see the [LICENSE.md](LICENSE.md) file for details.
