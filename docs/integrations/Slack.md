# Slack bot

This is the bot that will ping your new hires and colleagues with things they have to do. This is needed if you want to use ChiefOnboarding in Slack.
Since there is no centralized app, you will have to create an app in Slack yourself. The benefit of this is that you can use your own profile picture and name for the bot. 
There are two ways of create the Slack bot. Either do it automatically with the manifest (recommended) or go through it manually. We built the manifest with everything that you need to get up and running quickly. 

Use the manifest (recommended):

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click on 'Create New App' (big green button, can't be missed). Click on "From an app manifest".
2. Select the workspace where you want to install ChiefOnboarding.
3. Copy and paste the manifest below in the little text box that you get to see (change `XXXXXXXXXXXXXXX` with your domain name. Example: `demo.chiefonboarding.com`):

```
_metadata:
  major_version: 1
  minor_version: 1
display_information:
  name: Onboardingbot
features:
  bot_user:
    display_name: Onboardingbot
    always_online: true
oauth_config:
  redirect_urls:
    - https://XXXXXXXXXXXXXXX/api/integrations/slack
  scopes:
    bot:
      - im:history
      - im:read
      - users:read
      - users:read.email
      - im:write
      - chat:write
settings:
  event_subscriptions:
    request_url: https://XXXXXXXXXXXXXXX/api/slack/bot
    bot_events:
      - message.im
      - team_join
  interactivity:
    is_enabled: true
    request_url: https://XXXXXXXXXXXXXXX/api/slack/callback
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

4. Review the permissions and then click on 'Create'.
5. Scroll a bit on the new page and notice the `App credentials` part. You need the information there to fill in on the settings/integrations page in your ChiefOnboarding instance.
6. Fill in the details accordingly. The only thing you can't fill in is the 'Redirect URL'. This URL depends on your instances domain name. You will need to fill this in there: `https://YOURDOMAIN/api/integrations/slack` (again, change this url to match with your domain name!)
8. Submit the form. You will get back a Slack button. Click it and verify that you want to install your bot in your Slack team. (Try to say 'hello' to it)


If you used the manifest, then you can skip the manual part!

Manually:

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click on 'Create New App' (big green button, can't be missed). Give it a fancy name and pick the Slack team you are in. Click on 'Submit'.
2. To make the bot work, we need to enabled a few things in the newly created Slack bot.
3. Go to "Interactivity & Shortcuts" and enable interactivity. Then add this `https://YOURDOMAIN/api/slack/callback`.
4. Go to "OAuth & Permissions". Enter `https://YOURDOMAIN/api/integrations/slack` as the 'Redirect URL'. And under "Bot scopes" enable: `chat:write`, `im:read`, `im:write`, `users:read`, `users:read.email`.
5. Go to "Event Subscription" and enable it. Use `https://YOURDOMAIN/api/slack/bot` as the request url. Under 'Subscribe to bot events' add `message.im` and `team_join`.
6. Go back to "Basic Info" and scroll a bit on the new page and notice the `App credentials` part. You need the information there to fill in on the settings/integrations page in your ChiefOnboarding instance.
7. Fill in the details accordingly. The only thing you can't fill in is the 'Redirect URL'. This URL depends on your instances domain name. You will need to fill this in there: `https://YOURDOMAIN/api/integrations/slack`.
8. Submit the form. You will get back a Slack button. Click it and verify that you want to install your bot in your Slack team. (Try to say 'hello' to it)

That's it!
