# Data structure
We then need to define where the data is stored in the users array (for each object). We can do that with `data_structure`. In there, you can define the values you want to copy.
Please note that only `email`, `first_name` and `last_name` can be used for now.

```json
"data_structure": {
    "email": "workEmail",
    "last_name": "lastName",
    "first_name": "firstName"
}
```

In combination with `"data_from":"employees"`, we expect a JSON response from the third party like this:
```json
{
    "employees": [
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
