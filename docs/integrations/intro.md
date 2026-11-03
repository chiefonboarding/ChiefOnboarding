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

`department`: New hire's department

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

### Getting data from json responses
Besides, using the above, you can also select an item from a list of objects.

Say if a server returns you this list:
```
test_data = {
    "members": [
        {"email": "a@example.com", "name": "A"},
        {"email": "b@example.com", "name": "B"},
    ]
}
```
then you can do something like:
```
store_data: {
  "external_service_name": "members[email=b@example.com].name"
}
```
Which would store `B` in this case.


## Testing integrations with a mock endpoint
When building or debugging an integration, you can point it at a fake endpoint built into ChiefOnboarding instead of a real third-party API. You choose what it returns, and how slowly, through query parameters in the URL.

### Enabling it
Set this environment variable and restart ChiefOnboarding:

```
TEST_INTEGRATIONS_ENDPOINT=True
```

It defaults to `False`. When disabled, the endpoint does not exist and returns a 404.

!!!
The endpoint does not require a login. Only enable it on development or test instances, never on a publicly reachable production server.
!!!

### Usage
Use this URL in your integration manifest:

```
https://YOURDOMAIN/test-integrations/
```

It accepts `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` and `OPTIONS` requests.
Control the response with these query parameters:

| Parameter      | Description                                                        | Default            |
|----------------|--------------------------------------------------------------------|--------------------|
| `status`       | HTTP status code to return (100–599)                               | `200`              |
| `delay`        | Seconds to wait before responding (decimals allowed, max 10)       | `0`                |
| `body`         | Raw response body                                                  | `{}`               |
| `content_type` | `Content-Type` header of the response                              | `application/json` |
| `echo`         | If `true`, return the incoming request instead of `body` (see below) | off              |

If a parameter is invalid (for example `status=abc` or `delay=20`), the endpoint returns a `400` with an explanation.
Values in `body` must be URL-encoded if they contain characters like `&`, `#` or `+`.

### Examples
Simulate a user being created:

```
https://YOURDOMAIN/test-integrations/?status=201&body={"id":"abc123"}
```

Simulate a slow server error:

```
https://YOURDOMAIN/test-integrations/?status=500&delay=5&body=Internal error&content_type=text/plain
```

### Inspecting what your integration sends

With `echo=true`, the endpoint responds with what it received, so you can check
that your manifest fills in its values correctly:

```json
{
  "method": "POST",
  "query": {"echo": ["true"]},
  "body": "{\"email\": \"jane@example.com\"}"
}
```
