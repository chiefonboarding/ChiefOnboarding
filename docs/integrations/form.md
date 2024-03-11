---
outline: deep
---

# Form
This is the form that is shown to you when you add this to a sequence. The form should consist of items that you would like to have different for different type of people. In the example above, the form allows you to pick a specific team to add the user to. For example: you probably don't want to add a developer to the HR team in Asana. So, the team is what you can customize every time you add the integration to a user or in a sequence.

You can customize where we get the info from and what an admin should fill in. The `form` should always be an array (so you can add multiple items) and requires the following attributes:

`id`

This value can be used in the other calls. Please do not use spaces or weird characters. A single word in capitals is prefered.

`name`

The form label shown to the admin.

## Options
The form can consist of a text field for manual input, or you can use predefined options. Options can be fetched either by getting them from a third party url or using fixed options. You can define this by setting the `type` option:

`type`

Options: `choice` and `input`. If you choose `choice`, you will be able to set the options yourself OR fetch from an external url.


### Fixed options
If you want to use a predefined static list, then you can set the `items` field.

`items`

You can add an array here with objects in them with the props: `id` and `name`. For example: 

```json
[
    {"id": "233", "name": "option 1"}, 
    {"id": "234", "name": "option 2"}
]
```

### Dynamic options
To fetch from a third party API, you will need to set a few things. Please not that you will need to get an array with objects back from the server. It won't work with a normal list of strings or object.

`url`

The url it should fetch the options from.

`method` 

You can use any request method you would like (e.g. `POST`, `GET`, `PUT`, `DELETE`).

`headers`

(optionally) This will overwrite the default headers.

`data_from`

Default: `""`. The property it should use from the response of the url. In some cases, it might happen that what you get more than just the options you need. 

If you get a dictionary instead of an array and need to go a little deeper in the data. For example: you get a dictionary that has the prop `options` which has an array with the items. You can then specify `options` as the value for `data_from` and it will use that. If you need to go deeper, you can use the dot notation to do that. E.g. `data.options.items`.

Let's say we get this back from the server:

```json
{
    "data": {
        "items": [
            {"id": "123", "name": "option"},
            {"id": "124", "name": "option2"}
        ]
    }
}
```

You would need to set `data_from` to `data.items` to get to the list.

`choice_value`

Default: `"id"`. The value it should take for using in other parts of the integration (for example the `id` property of the items you get from the server).

`choice_name`

Default: `"name"`. The name that should be displayed to the admin as an option.
