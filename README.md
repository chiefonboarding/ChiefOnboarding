# ChiefOnboarding

ChiefOnboarding is a free and open source employee onboarding platform. You can onboarding new hires through Slack or the dashboard. 

**Please note: this software is currently in beta. There might be bugs, please report them if you find any!**


## Features
- **Automatically provision user accounts**, such as Slack and Google (more integrations coming soon!)
- **Pre-boarding**: onboarding doesn't start on day 1, it starts before that. Build pre-boarding pages to welcome new hires before they start.
- **To do items**: keep track of the things that your new hires need to do and allow them to fill in forms.
- **Resources**: let them search through the knowledge base and complete courses so they are quickly up to speed with colleagues.
- **Sequences**: drip feeding items over time or based on the completion of a to do item. Avoid the overwhelming feeling.  
- **Badges**: reward new hires for the things they have done. This also helps to keep them motivated.
- **Introductions**: introduce people new hires should know.  
- **Admin to do items**: Collaborate with colleagues on things that need to be done for the new hire.
- **Multilingual** (WIP): English, Dutch, Portuguese, German, Turkey, French, Spanish, and Japanese are all supported.
- **Timezones**: It doesn't matter where your new hire lives. You can adjust the timezone per new hire, so they don't get messages in the middle of the night!
- **Slack bot and dashboard**: your new hires can use the dashboard or the Slack bot. Both provide all features and can be used standalone.
- **Customizable**: use your logo, add your color scheme and even customize the bot to your liking. No one will know you are using ChiefOnboarding.
- **Transparency, freedom, and privacy**: ChiefOnboarding is completely open-source and licensed under MIT.
- Host it yourself on your own infrastructure or [let us host it for you](https://chiefonboarding.com/pricing)!


### Technical features
- Easy deployment through Docker (server recommendation is at least 2GB of RAM and 1 vCPU).
- Build on Django (version 3.0.x) with NuxtJS (version 2.13.x) as the front end (VueJS).
- Celery is used for background tasks.
- Easily connect Sentry for error tracking. Obviously, this is disabled by default.
- File storage is done through the S3 adapter. You can use AWS, but it's compatible with other object storages that follow S3 standards. 
- File links are all temporary (signed) and therefore do expire.
- Twilio is used for sending text messages.
- Anymail is used for sending emails. You can choose between a wide variety of [email providers](https://anymail.readthedocs.io/en/stable/esps/#supported-esps). 
- Let's encrypt will automatically be set up for a secure connection.

## Getting started with self-hosting

You can easily deploy ChiefOnboarding through Docker (Docker-compose). Make sure that both Docker and Docker-compose are installed.

Point your domain name to your IP address and then run this on your server:

```
git clone https://github.com/chiefonboarding/chiefonboarding
cd ChiefOnboarding
chmod +x server_script.sh ssl_renew.sh
# Replace YOURDOMAIN with your domain. example: onboarding.yourcompany.com and EMAIL with your email address. 
sudo ./server_script.sh YOURDOMAIN EMAIL
```

That should get your server up and running. Then start Django shell:

```
docker-compose run web python3 manage.py shell
```

Then run this (please replace the items that are marked with `<` and `>`):

```
from organization.models import Organization
from users.models import User
Organization.objects.create(name="<organization name>")
User.objects.create_admin('<first name>', '<last name>', '<email>', '<password>')
```

At last, we need to add a bit of default data into the database:

```
docker-compose run web python3 manage.py loaddata welcome_message.json
```

That's it to get the base running! The SSL certificate needs to be renewed every so often, it's generally a good idea to set up a cron job for `ssl_renew.sh` to automate that.

Up next, you might want to configure a few things, like AWS, Google, Slack, and Twilio. If you don't, then feel free to skip this section.
I want to emphasise here that ChiefOnboarding does not ping home. Unless you set up error tracking through, there are no analytics, tracking, or data mining things in place. You can check this by yourself through the source code.
So, just like everything else you enter in ChiefOnboarding, none of the things you do below will be send to us.

### Setting up Slack, Google, AWS S3, and Twilio
All of the chapters below are independent (except for the Slack ones). They do not rely on another chapter. Feel free to skip the ones you don't want. This is probably obvious, but every time I use `YOURDOMAIN`, you should replace this with your domain name, example: `chiefonboarding.com`.

#### The Slack bot
This is the bot that will ping your new hires and colleagues with things they have to do. This is needed if you want to use ChiefOnboarding in Slack.
Since there is no centralized app, you will have to create an app in Slack yourself. The benefit of this is that you can use your own profile picture and name for the bot.

1. Go to https://api.slack.com/apps and click on 'Create New App' (big green button, can't be missed). Give it a fancy name and pick the Slack team you are in. Click on 'Submit'.
2. Scroll a bit on the new page and notice the `App credentials` part. You need the information there to fill in on the settings/integrations page in your ChiefOnboarding instance.
3. Fill in the details accordingly. The only thing you can't fill in is the 'Redirect URL'. This URL depends on your instances domain name. You will need to fill this in there: `https://YOURDOMAIN/api/integrations/slack`. **DON'T SUBMIT THE FORM YET.**
4. To make the bot work, we need to enabled a few things in the newly created Slack bot.
5. Go to "Interactivity & Shortcuts" and enable interactivity. Then add this `https://YOURDOMAIN/api/slack/callback`. Enter `https://YOURDOMAIN/api/integrations/slack` as the 'Redirect URL'. 
6. Go to "OAuth & Permissions" and under "Scopes" enable: `chat.write`, `im:read`, `im:write`, `users:read`, `users:read.email`. 
7. Go to "Event Subscription" and enable it. Use `https://YOURDOMAIN/api/slack/bot` as the request url. Under "Subscribe to event on behalf of users" and add `im_created` and `message.im`.
8. Now go back to your ChiefOnboarding instance and submit the form. You will get back a Slack button. Click it and verify that you want to install your bot in your Slack team.

That's it!

### Creating accounts for Slack
This will allow you to automatically create accounts for Slack for your new hire. We cannot use the same Slack app as the previous one as this one uses a permission that is not compatible with the other one.
We need to set up OAuth for this and then you will have to add this one to your Slack team as well, but it won't actually do anything in your Slack team, except for adding and removing team members. Annoying, I know.

Note: you can install this one standalone, BUT you will not be able to add Slack accounts afterwards. This is because we cannot add the correct scope to this app to check if a user is already in your team.
The scope needed for this app is for creating accounts is a legacy/undocumented scope and does not work along with the supported/documented scopes.

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click on 'Create New App' (big green button, can't be missed). Give it a fancy-pancy name and pick the Slack team you are in. Click on 'Submit'.
2. Go to 'OAuth & Permissions' and add this url as the redirect url: `http://YOURDOMAIN/api/integrations/slack/oauth`. 
2. Go back to the previous page and notice the `App credentials` part. You need the information there to fill in on the settings/integrations page in your ChiefOnboarding instance.
3. Fill in the details accordingly. The only thing you can't fill in is the 'Redirect URL'. You will need to fill this in there: `https://YOURDOMAIN/api/integrations/slack/oauth`.
4. Hit 'Submit' and click on the Slack button to add this app to your team.

You should be able to create new accounts now!

#### Google login
This will allow you to use the 'Log in with Google' button on the log in page.

1. Go to [https://console.developers.google.com/apis/consent](https://console.developers.google.com/apis/consent) and make sure you are logged in as the admin of the Google organization.
2. Create a new 'Project' and give it a fancy name. Once it's created make sure you are in that project (you can see that in the top bar).
3. You will be asked for what type of app you want to register. Choose 'Intern', only people from your organization should log in to your app. Click on 'Create'.
4. Fill in the details accordingly. You don't have to change the scopes, those are fine. Under 'Authorized domains', fill in your own site url and the url of the ChiefOnboarding instance.
5. Click on 'Create'. You will be taken back to the page you previously landed on.

We just set up our authentication screen for people that want to sign in. Up next, we need to create credentials that we can put into the ChiefOnboarding instance, so we can actually show that authentication dialog.

6. Go to [https://console.developers.google.com/apis/credentials](https://console.developers.google.com/apis/credentials)
7. Click on 'Create credentials' at the top of the page and choose Client-ID OAuth.
8. You will be asked for the type of app. Pick 'Web application'.
9. Under "Authorized JavaScript-sources" enter the domain name of where ChiefOnboarding is running on.
10. Under "Authorized redirect-URLs" enter this: `https://YOURDOMAIN/api/integrations/google_login`.
11. Click on 'Create' and you will get the `Client-ID` and `Client-secret` that you need to fill in on your ChiefOnboarding instance.
12. Submit the form on ChiefOnboarding and enable the Google login integration in settings->global and you should be good to go.

You will only be able to let people log in that already have an account in ChiefOnboarding.


#### Creating Google Accounts
This is for automatically provisioning Google accounts for new hires. Unfortunately, Google needs an OAuth key instead of a simple API key for this, so we need to setup the consent form as well.

Note: If you have already created a project, because of the previous section, then you can skip step 1 to 5. Please make sure you add the extra scopes from step 4!

1. Go to [https://console.developers.google.com/apis/consent](https://console.developers.google.com/apis/consent) and make sure you are logged in as the admin of the Google organization.
2. Create a new 'Project' and give it a fancy name. Once it's created make sure you are in that project (you can see that in the top bar).
3. You will be asked for what type of app you want to register. Choose 'Intern', only people from your organization should log in to your app. Click on 'Create'.
4. Fill in the details accordingly. You will have to add the following scopes: `https://www.googleapis.com/auth/admin.directory.user`. Under 'Authorized domains', fill in your own site url and the url of the ChiefOnboarding instance.
5. Click on 'Create'. You will be taken back to the page you previously landed on.

We just set up our authentication screen for you to sign in to. Up next, we need to create credentials that we can put into the ChiefOnboarding instance, so we can actually show that authentication dialog.

6. Go to [https://console.developers.google.com/apis/credentials](https://console.developers.google.com/apis/credentials)
7. Click on 'Create credentials' at the top of the page and choose Client-ID OAuth.
8. You will be asked for the type of app. Pick 'Web application'.
9. Under "Authorized JavaScript-sources" enter the domain name of where ChiefOnboarding is running on.
10. Under "Authorized redirect-URLs" enter this: `https://YOURDOMAIN/api/integrations/google_token`.
11. Click on 'Create' and you will get the `Client-ID` and `Client-secret` that you need to fill in on your ChiefOnboarding instance.
12. Submit the form on ChiefOnboarding and enable the Google login integration in settings->global. You will see a new link that you will have to click.
13. Once you clicked that link, you will have to verify that you want to give the application rights to add new Google accounts to your organization.
14. You will then have to enable the Admin SDK for your project here: [https://console.developers.google.com/apis/library/admin.googleapis.com](https://console.developers.google.com/apis/library/admin.googleapis.com), click on 'Enable'.




#### Creating AWS S3 bucket for file saving
This is required to be able to save files uploaded by new hires or yourself.

1. Go to [https://s3.console.aws.amazon.com/s3/home](https://s3.console.aws.amazon.com/s3/home) and click on 'Create bucket'.
2. Give it a fancy name and click on 'Next'.
3. Keep everything at the default (or change it to your liking) and click on 'Next'.
4. Keep everything at the default and click on 'Next'.
5. Click on 'Create bucket'.
6. In the bucket, go to 'Permissions' and then to 'CORS'.
7. Add this CORS configuration there (again, change YOURDOMAIN):

```
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
<CORSRule>
    <AllowedOrigin>https://YOURDOMAIN</AllowedOrigin>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedMethod>POST</AllowedMethod>
    <AllowedMethod>DELETE</AllowedMethod>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
</CORSRule>
</CORSConfiguration>
``` 

The bucket is now created. Up next, we need to create a user to be able to post and get from this bucket.

6. Go to [https://console.aws.amazon.com/iam/home#/users](https://console.aws.amazon.com/iam/home#/users).
7. Click on 'Add user'.
8. Give it a fancy user name and select 'Programmatic access', so we get the keys we need to enter in ChiefOnboarding. Click on 'Next'.
9. Go to 'Attach existing policies directly' and click then 'Create policy'.
10. For 'Service' pick 'S3'.
11. For 'Actions' pick 'GetObject', 'DeleteObject' and 'PutObject'. 
12. Under 'Resources', enter the correct bucket name and for the 'Object name' select 'Any'.
13. Click on 'Add'.
14. Click on 'Review policy'.
15. Give it a fancy name and click on 'Create policy'.
16. Go back to the set up screen of your IAM user and click on the refresh button to refresh policies. 
17. Add your newly created policy to the user and click on 'Next'.
18. Click on 'Next' again. Twice.
19. You will now get to see the Access key ID and the Secret access key. Add those to your environment variables or .env file. 
  

#### Adding Twilio for text messages
This is required to be able to save files uploaded by new hires or yourself.

1. Sign up at [Twilio](https://www.twilio.com) if you haven't yet.
2. Go to [https://www.twilio.com/console/phone-numbers](https://www.twilio.com/console/phone-numbers) and click on the red 'plus' icon.
3. Pick a number you like and purchase it. Make sure it allows text messages.
4. Go to [https://www.twilio.com/console/project/settings](https://www.twilio.com/console/project/settings)
5. You can take the account_sid and api key from there and add those to your environment variables or .env file.  

  
### Import fixtures
This is entirely optional, but if you want, you can import some examples with fixtures. Just run this:

```
docker-compose run web python3 manage.py loaddata content.json to_do.json preboarding.json external_messages.json sequence.json badge.json admin_task.json admin_task_comment.json category.json condition.json tag.json
```

### Local environment
If you want to contribute (this makes you pretty awesome, imho) or just play around with the source code, clone this repo to your computer and then run this to get it running with Docker:

```
docker-compose up
```

## Q&A

### I am not using Let's encrypt, can I still redirect everyone to https?
Yes, just set `SSL_REDIRECT` to `True` in your environment variables. This will redirect http queries on application level.

## Authors
See the list of [contributors](https://github.com/ChiefOnboarding/ChiefOnboarding/graphs/contributors). A big thanks to anyone that contributes!

## Security issues
Please do not create an issue if you found a potential security issue. Email me directly at security@chiefonboarding.com and I will get it resolved ASAP.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
