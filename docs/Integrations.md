---
order: 65 
---

# Integrations / Webhooks (Beta)
ChiefOnboarding allows you to create integrations or trigger webhooks that can be triggered either manually or through a sequence. You can view some examples at https://integrations.chiefonboarding.com. You are free to copy them. If you created a cool new integrations, then please post it there. That way we can help eachother out by not re-inventing the wheel! Thanks a lot!

There are two types of integrations:
1. An integration to trigger a URL on an third party service
2. An "import users" integration, which allows you to import users from a third party to ChiefOnboarding (manually)

## Integration to trigger a third party url
Here is an example of a manifest of an integration (in this case to add a user to an Asana team):

:::code source="static/manifest.json" :::

Let's go over the items:

### Form
This is the form that is shown to you when you add this to a sequence. The form should consist of items that you would like to have different for different type of people. In the example above, the form allows you to pick a specific team to add the user to. For example: you probably don't want to add a developer to the HR team in Asana. So, the team is what you can customize every time you add the integration to a user or in a sequence.

You can customize where we get the info from and what an admin should fill in. The `form` should always be an array and allows the following properties:

`id`: This value can be used in the other calls. Please do not use spaces or weird characters. A single word is prefered.

`name`: The form label shown to the admin.

`type`: options: `choice`, `multiple_choice` and `input`. If you choose `choice`, you will be able to set the options yourself OR fetch from an external url.

For `choice`:

`url`: (if you have static items, then use `items` instead). The url it should fetch the options from.

`method`: Default: `POST`. You can use any request method you would like.

`headers`: (optionally) This will overwrite the default headers.

`data_from`: The property it should use from the response of the url. In some cases, it might happen that what you get more than just the options you need. For example, you get a dictionary instead of an array and need to go a little deeper in the data. For example: you get a dictionary that has the prop `options` which has an array with the items. You can then specify `options` as the value for `data_from` and it will use that. If you need to go deeper, you can use the dot notation to do that. E.g. `data.options.items`. Leave this field blank if you are using predefined items.

`choice_value`: The value it should take for using in other parts of the integration (for example the `id` property of the items you get from the server). Default: `id`.

`choice_name`: The name that should be displayed to the admin as an option. Default: `name`.

`items`: (if you are not fetching items from a url) You can add an array here with objects in them with the props: `id` and `name`. For example: `[{"id": "233", "name": "option 1"}, {"id": "234", "name": "option 2"}]`.


### Exists
Exists is an option to check if a user is already part of a team. If you add this property to your manifest then it will show up under new hire -> access. From there, you will be able to manaully enable/disable an account for them. Generally, you should skip this option if you are making any calls not related to account provisioning.

`url`: The url to check if the user exists. Everything that comes back is parsed to a string and then checked against.

`method`: The method for lookup that is being used. E.g. `POST` or `GET`.

`expected`: Whatever we expect. Generally this will probably be a positive message or the new hire's email. You can use new hire values by wrapping them around double curly brackets.

`headers`: (optionally) This will overwrite the default headers.

`fail_when_4xx_response_code`: Default: True. If the server response with a 4xx status code, then that's considered a failing request. In some cases, apis will return a 404 if the user does not exist. In that case, set this to `False`, so it can check for the `expected` value.

### Execute
These requests will be ran when this integration gets triggered.

`url`: The url where the request will be made to.

`data`: This is the data that will be send with it.

`method`: The request method. E.g. `POST` or `GET`.

`headers`: (optional) This will overwrite the default headers.

`store_data`: (optional) This can be used to store data to the new hire. Let's say you create a document through an API and you need to store the document ID that is relevant to the new hire, then you can do that with this. You can put a dictionary here with a key and value of the new hire prop name and the notation of where to get the data. You can use a dot notation to go deeper in the json. This data is only available in items assigned to this new hire and can be used anywhere (in both content items (todo, resources etc) and integrations that get triggered later).

Example:
```
{
    "FORM_ID": "data.id",
    "DOCUMENT_HASH": "document_hash"
}
```

`continue_if`: (optional) This can be used as a blocked. If you want to block an integration if a response is not what you expect, then you can do that with this. If you need to wait for a response to come back (waiting for a background task for example), then you can use polling and continue with the call with the response changes. It will check every response and stop polling when it matches. 

Example:
```
{
    "response_notation": "detail.status",
    "value": "done"
}
```
With this config, it will check the response for the `status` property in the `detail` property (so for example: `{"detail": {"status": "done"}}`). It will check for the value `done`, which would be valid in this case and therefore continue with the integration.

`polling`: (optional) You can use this to poll a url if you are waiting for a background (async) task to be completed. It will retry fetching the url for as many times as you specify at the interval you want. Here is an example config:
```
{
    "interval": 5,
    "amount": 60,
}
```
This config will try to fetch the same url for 60 times and wait 5 seconds between each call (so max 300 seconds) and will keep going until the `status` of the response is `done`. If it exceeds the 300 seconds, then the integration will fail.


### Headers
These headers will be send with every request. These could include some sort of token variable for authentication.

### Oauth
If you need to use OAuth2 to get a token, then you will need to use this. Just create a prop called `oauth` and then in that use these properties:

`authenticate_url`: This is the url that is used to send the user to the login/authorize the connection (this should be a url to the third party). This is always a `GET` request. It expects an url here.

`access_token`: This is used when you come back to our site with a token. With that token, it will need to fetch an access token from the third party (and perhaps a refresh token). Format is an object like the `execute` part.

`refresh`: Used to refresh the token to get a new one, if this is not added, then it will assume that the token is permanent. Format is an object like the `execute` part.

`without_code`: Default: `False`. Enable this is a valid callback won't return a `code` query in the url. In some cases, we don't get it and also not need it.


### Initial data form
This is a form that you can create to fill in when you add this integration to your instance. Any sensitive info should be filled in here, instead of in the manifest itself. Data that gets filled in here will be saved encrypted in the database. The manifest itself does not get encrypted. So, again, any tokens, authentication, sensitive info should be filled in through this form and not hardcoded!


You can obviously add as many as you want. You can use these variables by using the `id` in any of the other parts of the manifest.

`id`: Reference for any other part of the manifest. Wrap it around double curly brackets to use it. 

`name`: The label of the field. Please do not use spaces or weird characters. A single word is prefered. Use `generate` to generate a secret value, use this for i.e. one-time password.

`description`: Any other info you want to leave to make it clear where to find this value. Mainly used for documentation and/or sharing.


### Post execute notification
Defined as `post_execute_notification`. Gives you the ability to send a text message or email to someone after this integration has been completed.

`type`: Either `email`, or `text`. Depends if you want to send an email or text message.

`to`: Use a fixed email or (preferably) a placeholder.

`subject`: In case of an email, define the subject header.

`message`: The message that should be send (plain text).


### Variables
Throughout the manifest you can use the variables that you have defined in the `initial_data_form` or the `form` wrapped around in double curly brackets. On top of that, you can also use new hire values. You can use: 

`email`: New hire's email address

`manager`: The manager's full name

`manager_email`: The manager's email address

`buddy`: The buddy's full name

`buddy_email`: The buddy's email address

`position`: New hire's position

`department`: New hire's department

`first_name`: New hire's first name

`last_name`: New hire's last name

`start`: New hire's start date

!!!
Please do not overwrite these with your own ids
!!!


## Notes
* If triggering an integration fails, then it will retry the entire integration again one hour after failing. If it fails again, it will not retry.
* If you are using any of the integrations from the repo at: https://integrations.chiefonboarding.com then you have to validate them yourself. This is a user repository and we do not actively moderate the submissions there. Please always validate the urls where requests are going to make sure it's legit. 


## Import user integration
You can create custom import integrations to pull users from a third party and put them in ChiefOnboarding. This is fairly universal and will work with most APIs. A sample integration config will look like this:

:::code source="static/import_user_manifest.json" :::

The setup is very similar to what we have for other integrations to trigger a webhook. The most notable differences are:

`"type": "import_users"`: this is to indicate that this integration is only used to import users into ChiefOnboarding.

`data_from`: this is to indicate where the users are located in the response. You can use a dot notation if need to go deep into the json to get the data.

We then also need to define where the data is stored in the users array (for each object). We can do that with `data_structure`. In there, you can define the values you want to copy.
Please note that only `email`, `first_name` and `last_name` can be used for now.

```
"data_structure": {
    "email": "workEmail",
    "last_name": "lastName",
    "first_name": "firstName"
},
```

So for the current config, we expect a JSON response from the third party like this:
```
{
    employees: [
        {
            "firstName: "John",
            "lastName: "Do",
            "workEmail": "john@do.com"
        },
        {
            "firstName: "Jane",
            "lastName: "Do",
            "workEmail": "jane@do.com"
        }
    ]
}
```

Other values in the JSON will be ignored.

### Paginated response
Sometimes, we might not get all items at once. We have something to cover that too.

`amount_pages_to_fetch`: Default: 5. Maximum amount of page to fetch. It will stop earlier if there are no users found anymore. There is a limit to this number. Please see the note below.

There are two ways of fetching a new page: 
1. Sometimes an API will only return a token and we will have to build the url ourselves. (Google does this for example)
2. In most cases, you will get a full url that you can use to fetch the new page of users.

For case 1, you will need to provide two items (the url and where the token is):

`next_page_token_from`: the place to look for the next page token. You can use the dot notation to do go deeper into the JSON. If it's not found, it will stop.
`next_page`: This should be a fixed url that you should put here. You can use `{{ NEXT_PAGE_TOKEN }}` as the variable to include the previously found `next_page_token_from` value.

For example, this is necessary for Google:

```
"next_page": "https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&pageToken={{ NEXT_PAGE_TOKEN }}",
"next_page_token_from": "nextPageToken"
```

For case 2, you will only need to provide the place where we need to look for the URL with this item:

`next_page_from`: the place to look for the next page url. You can use the dot notation to do go deeper into the JSON. If it's not found, it will stop.

Note: fetching users is being done live when you visit the page. If you set a high amount of pages to be fetched, then this might cause a timeout on the server. It makes rendering all users on the client also very sluggish. We recommend to not load more than 5000 users or not more than 10 pages (if a timeout of 30 seconds is set on your server (like Heroku for example)), whichever comes first. If you do need more, then we recommend going for an alternative method of importing users.
