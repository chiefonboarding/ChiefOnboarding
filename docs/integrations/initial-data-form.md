# Initial data form
This is a form that you can create to fill in when you add this integration to your instance. Any sensitive info should be filled in here, instead of in the manifest itself. Data that gets filled in here will be saved encrypted in the database. The manifest itself does not get encrypted. So, again, any tokens, authentication, sensitive info should be filled in through this form and not hardcoded!

You can obviously add as many as you want. You can use these variables by using the `id` in any of the other parts of the manifest.

`id`

Reference id, so it can be used in any part of the manifest. For example, an id called `DOMAIN`, can be used like this:

```
{{ DOMAIN }}
```
So, wrap it around double curly brackets to use it. 

`name`

The label of the field. A short description of what it is, for example: "The domain name to where the requests should be made". Use `generate` to generate a secret value, use this for i.e. one-time password. Items with the name `generate` will not show up in the form to fill in by an admin. These are only use for reference and generated on the fly.

`description`

Any other info you want to leave to make it clear where to find this value. Mainly used for documentation and/or sharing (shown under the input box as help text).


## Example

```json
"initial_data_form": [
    {
        "id": "TOKEN",
        "name": "Please put your token here",
        "description": "You can find your token here: https://...."
    },
    {
        "id": "ORG",
        "name": "Organization id",
        "description": "You can find your organization id here: https://..."
    },
    {
        "id": "PASSWORD",
        "name": "generate"
    },
    {
        "id": "EMAIL_HASH",
        "name": "generate"
    }
]
```
