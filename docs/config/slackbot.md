# Slack bot
This is the bot that will ping your new hires and colleagues with things they have to do. This is needed if you want to use ChiefOnboarding in Slack.
Since there is no centralized app, you will have to create an app in Slack yourself. The benefit of this is that you can use your own profile picture and name for the bot. 

Manifest (webhook) - replace XXX with your domain name:

```yaml
display_information:
  name: Onboardingbot
features:
  bot_user:
    display_name: Onboardingbot
    always_online: true
oauth_config:
  redirect_urls:
    - https://XXXXXXXXXXXXXXX/admin/integrations/slack
  scopes:
    bot:
      - im:history
      - im:read
      - users:read
      - users:read.email
      - im:write
      - chat:write
      - channels:read
      - groups:read
settings:
  event_subscriptions:
    request_url: https://XXXXXXXXXXXXXXX/api/slack/bot
    bot_events:
      - message.im
      - team_join
  interactivity:
    is_enabled: true
    request_url: https://XXXXXXXXXXXXXXX/api/slack/bot
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click on 'Create New App' (big green button, can't be missed). Click on "From an app manifest".
2. Select the workspace where you want to install ChiefOnboarding.
3. Copy and paste the manifest in the little text box.
4. Review the permissions and then click on 'Create'.
5. Scroll a bit on the new page and notice the `App credentials` part. You need the information there to fill in on the settings/integrations page in your ChiefOnboarding instance.
6. Fill in the details accordingly.
7. Submit the form. You will now get a "Add to your Slack team" button. Click it and verify that you want to install your bot in your Slack team.
8. Go back to your Slack bot and go to "App Home". Then scroll down till you see: "Show Tabs". Enable the "message tab" and check the "Allow users to send Slash commands and messages from the messages tab".

That's it!


## Importing channels

`SLACK_EXCLUDE_EXT_SHARED_CHANNELS`

Default: `False`. If you don't want to import channels that are being shared with external people, then you can set this to `True` to exclude those.
