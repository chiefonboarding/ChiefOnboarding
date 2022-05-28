---
order: 65 
---

# Integrations / Webhooks (Beta)
ChiefOnboarding allows you to create integrations or webhooks that can be triggered either manually or through a sequence. You can view some examples at https://integrations.chiefonboarding.com. You are free to copy them. If you created a cool new integrations, then please post it there. That way we can help eachother out by not re-inventing the wheel! Thanks a lot!

Here is an example of a manifest of an integration (in this case to add a user to an Asana team):

:::code source="static/manifest.json" :::

Let's go over the items:

## Form
This is the form that is shown to you when you add this to a sequence. The form should consist of items that you would like to have different for different type of people. In the example above, the form allows you to pick a specific team to add the user to. For example: you probably don't want to add a developer to the HR team in Asana. So, the team is what you can customize every time you add the integration to a user or in a sequence.

You can customize where we get the info from and what an admin should fill in. The `form` should always be an array and allows the following properties:

`id`: This value can be used in the other calls. Please do not use spaces or weird characters. A single word is prefered.

`name`: The form label shown to the admin.

`type`: options: `choice` or `input`. If you choose `choice`, you will be able to set the options yourself OR fetch from an external url.

For `choice`:

`url`: (if you have static items, then use `items` instead). The url it should fetch the options from. (always a GET request)

`data_from`: The property it should use from the response of the url. In some cases, it might happen that what you get more than just the options you need. For example, you get a dictionary instead of an array and need to go a little deeper in the data. For example: you get a dictionary that has the prop `options` which has an array with the items. You can then specify `options` as the value for `data_from` and it will use that. If you need to go deeper, you can use the dot notation to do that. E.g. `data.options.items`. Leave this field blank if you are using predefined items.

`choice_value`: The value it should take for using in other parts of the integration (for example the `id` property of the items you get from the server). Default: `id`.

`choice_name`: The name that should be displayed to the admin as an option. Default: `name`.

`items`: (if you are not fetching items from a url) You can add an array here with objects in them with the props: `id` and `name`. For example: `[{"id": "233", "name": "option 1"}, {"id": "234", "name": "option 2"}]`.


## Exists
Exists is an option to check if a user is already part of a team. If you add this property to your manifest then it will show up under new hire -> access. From there, you will be able to manaully enable/disable an account for them. Generally, you should skip this option if you are making any calls not related to account provisioning.

`url`: The url to check if the user exists. Everything that comes back is parsed to a string and then checked against.

`method`: The method for lookup that is being used. E.g. `POST` or `GET`.

`expected`: Whatever we expect. Generally this will probably be a positive message or the new hire's email. You can use new hire values by wrapping them around double curly brackets.

## Execute
These requests will be ran when this integration gets triggered.

`url`: The url where the request will be made to.

`data`: This is the data that will be send with it.

`method`: The request method. E.g. `POST` or `GET`.

## Headers
These headers will be send with every request. These could include some sort of token variable for authentication.

## Initial data form
This is a form that you can create to fill in when you add this integration to your instance. Any sensitive info should be filled in here, instead of in the manifest itself. Data that gets filled in here will be saved encrypted in the database. The manifest itself does not get encrypted. So, again, any tokens, authentication, sensitive info should be filled in through this form and not hardcoded!


You can obviously add as many as you want. You can use these variables by using the `id` in any of the other parts of the manifest.

`id`: Reference for any other part of the manifest. Wrap it around double curly brackets to use it. 

`name`: The label of the field. Please do not use spaces or weird characters. A single word is prefered.

`description`: Any other info you want to leave to make it clear where to find this value. Mainly used for documentation and/or sharing.


## Post execute notification
Defined as `post_execute_notification`. Gives you the ability to send a text message or email to someone after this integration has been completed.

`type`: Either `email`, or `text`. Depends if you want to send an email or text message.

`to`: Use a fixed email or (preferably) a placeholder.

`subject`: In case of an email, define the subject header.

`message`: The message that should be send (plain text).


## Variables
Throughout the manifest you can use the variables that you have defined in the `initial_data_form` or the `form` wrapped around in double curly brackets. On top of that, you can also use new hire values. You can use: 

`email`: New hire's email address

`manager`: The manager full name

`buddy`: The buddy's full name

`position`: New hire's position

`first_name`: New hire's first name

`last_name`: New hire's last name

`start`: New hire's start date

!!!
Please do not overwrite these with your own ids
!!!


## Notes
* If triggering an integration fails, then it will retry the entire integration again one hour after failing. If it fails again, it will not retry.
* Integrations/Webhooks are currently in beta. Features will be added to it (OAuth support soon!).
* If you are using any of the integrations from the repo at: https://integrations.chiefonboarding.com then you have to validate them yourself. This is a user repository and we do not actively moderate the submissions there. Please always validate the urls where requests are going to make sure it's legit. 
