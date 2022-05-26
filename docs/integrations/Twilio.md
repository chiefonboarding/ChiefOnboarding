# Twilio

This is needed to be able to send text messages to new hires or colleagues (used for preboarding messages to new hire and text messages in sequences).

1. Sign up at [Twilio](https://www.twilio.com) if you haven't yet.
2. Go to [https://www.twilio.com/console/phone-numbers](https://www.twilio.com/console/phone-numbers) and click on the red 'plus' icon.
3. Pick a number you like and purchase it. Make sure it allows text messages.
4. Go to [https://www.twilio.com/console/project/settings](https://www.twilio.com/console/project/settings)
5. You can take the `account_sid` and `api key` from there and add those to your environment variables or .env file.  

Example variables:
```
TWILIO_FROM_NUMBER=+XXXXXXXXX
TWILIO_ACCOUNT_SID=ACXXXXXXXXX
TWILIO_AUTH_TOKEN=XXXXXXXXX
```
