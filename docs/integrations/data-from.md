# Data from

Default: `""`. The property it should use from the response of the url. In some cases, it might happen that what you get more than just the options you need. 

If you get a dictionary instead of an array and need to go a little deeper in the data. For example: you get a dictionary that has the prop `options` which has an array with the items. You can then specify `options` as the value for `data_from` and it will use that. If you need to go deeper, you can use the dot notation to do that. E.g. `data.options.items`.

Let's say we get this back from the server:

```json
{
    "data": {
        "items": [
            {"email": "test@example.com", "first_name": "Stan"},
            {"email": "john@example.com", "first_name": "John"},
        ]
    }
}
```

You would need to set `data_from` to `data.items` to get to the list.
