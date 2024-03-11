# Revoke
Revoke is an option to revoke access of a user to a third party. If you add this property to your manifest then you will be able to revoke access through the dashboard. Generally, you should only use this option if you want to deactivate an account from someone.

It expects an array with requests in it. If neither `status_code` nor `expected` is provided, then it will always mark it as succeeded.

`url`

The url to trigger. 

`method`

The method for lookup that is being used. E.g. `POST` or `PUT`.

`data`

This is the data that will be send with it.

For example:
```
{
    "id": 123
}
```

`expected`

Whatever we expect. Generally this will probably be a positive message that the user was removed. You can use user values by wrapping them around double curly brackets.

`status_code`

(optionally) Expects an array with status codes. These would be checked against the response status code. You can add multiple status codes if those can sometimes differ based on the call. For example: `[200, 201]`. The call would fail if the status code does not match any of the options.

`headers`

(optionally) This will overwrite the default headers.

## Example
```
"revoke": [
    {
        "url": "https://app.asana.com/api/1.0/users/{{email}}",
        "method": "POST",
        "expected": "{{email}}"
        "status_code": [200, 201]
    }
]
```
