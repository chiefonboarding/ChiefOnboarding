# Exists
Exists is an option to check if a user is already part of a team. If you add this property to your manifest then it will show up under new hire -> access and employee -> access. From there, you will be able to manually enable/disable an account for them. Generally, you should only use this if you are checking for user accounts (so not with triggering custom webhooks). Either `status_code` or `expected` is required to check if the user exists.

`url`

The url to check if the user exists. Everything that comes back is parsed to a string and then checked against based on the `expect` value.

`method`

The method for lookup that is being used. E.g. `POST` or `GET`.

`expected`

Whatever we expect. Generally this will probably be a positive message or the new hire's email. You can use new hire values by wrapping them around double curly brackets.

`status_code`

(optionally) Expects an array with status codes. These would be checked against the response status code. You can add multiple status codes if those can sometimes differ based on the call. For example: `[200, 201]`.

`headers`

(optionally) This will overwrite the default headers.

`store_data`

(optional) This can be used to store data to the new hire. Let's say you need a specific ID to revoke the access of a user, but this user is already in the system (through import or manually added) then you won't have the ID. You can backfill these users through the settings -> integrations page. Key is the stored value, value is the key name in the returned JSON from the external service.

## Example
```
"exists": {
    "url": "https://app.asana.com/api/1.0/users/{{email}}",
    "method": "GET",
    "expected": "{{email}}"
    "status_code": [200, 201],
    "store_data": {"external_id": "id"}
}
```
