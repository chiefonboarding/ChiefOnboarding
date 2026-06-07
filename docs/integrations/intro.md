# Integrations
ChiefOnboarding allows you to create integrations or trigger webhooks that can be triggered either manually or through a sequence. You can view some examples at https://integrations.chiefonboarding.com. You are free to copy them. If you created a cool new integrations, then please post it there. That way we can help eachother out by not re-inventing the wheel! Thanks a lot!

There are two types of integrations:
1. An integration to trigger a URL on an third party service
2. An "sync users" integration, which allows you to import users from a third party to ChiefOnboarding (manually or through a background cron job) or update specific information to the user (for example, save an external ID per user)


### Variables
Throughout the manifest you can use the variables that you have defined in the `initial_data_form` or the `form` wrapped around in double curly brackets. On top of that, you can also use new hire values. You can use: 

`email`: New hire's email address

`manager`: The manager's full name

`manager_email`: The manager's email address

`buddy`: The buddy's full name

`buddy_email`: The buddy's email address

`position`: New hire's position

`department`: New hire's department(s), if multiple it will be concatenated like: dep1, dep2 and dep3

`first_name`: New hire's first name

`last_name`: New hire's last name

`start`: New hire's start date

`access_overview`: This will be a list of all the access the user could have access to. This includes previously assigned manual access and automated access (all of the automated items). It will result in a string like this: `Asana (no access), Google (has access), Teams (unknown)`. `unknown` is used when we couldn't reach the service.

::: warning
Please do not overwrite these with your own ids
:::

You can also use data from previous requests. If you have an integration with 3 requests, you can use the data from the request 1 in request 2 and the data from request 1 and 2 in request 3. 
You can do that by using: 
``` 
{{ responses.0.the_data_you_need }}
``` 
(index starts at 0). So for example, you get this response from the first request:
```json
{
    "form_id": 134
}
```
You can then use 
```
{{ responses.0.form_id }}
``` 
in any of the following requests in the same integration.
