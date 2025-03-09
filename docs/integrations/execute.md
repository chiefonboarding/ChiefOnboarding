# Execute
These requests will be ran when this integration gets triggered. This expects an array with objects.

`url`

The url where the request will be made to.

`data`

This is the data that will be send with it.

`method`

The request method. E.g. `POST` or `GET`.

`headers`

(optional) This will overwrite the default headers.

`store_data`

(optional) This can be used to store data to the new hire. Let's say you create a document through an API and you need to store the document ID that is relevant to the new hire, then you can do that with this. You can put a dictionary here with a key and value of the new hire prop name and the notation of where to get the data. You can use a dot notation to go deeper in the json. This data is only available in items assigned to this new hire and can be used anywhere (in both content items (todo, resources etc) and integrations that get triggered later).

Example:
```json
{
    "FORM_ID": "data.id",
    "DOCUMENT_HASH": "document_hash"
}
```

`continue_if`

(optional) This can be used as a blocked. If you want to block an integration if a response is not what you expect, then you can do that with this. If you need to wait for a response to come back (waiting for a background task for example), then you can use polling and continue with the call with the response changes. It will check every response and stop polling when it matches. 

Example:
```json
{
    "response_notation": "detail.status",
    "value": "done"
}
```

With this config, it will check the response for the `status` property in the `detail` property (so for example: `{"detail": {"status": "done"}}`). It will check for the value `done`, which would be valid in this case and therefore continue with the integration.

`polling`

(optional) You can use this to poll a url if you are waiting for a background (async) task to be completed. It will retry fetching the url for as many times as you specify at the interval you want. Here is an example config:

```json
{
    "interval": 5,
    "amount": 60,
}
```

This config will try to fetch the same url for 60 times and wait 5 seconds between each call (so max 300 seconds) and will keep going until the `status` of the response is `done`. If it exceeds the 300 seconds, then the integration will fail.

`save_as_file`

(optional) If you expect a file as a response from the server, then you can define this with the filename you want it to have. For example: `"save_as_file": "filename.png"`. You can then use this filename in the `files` parameter for any requests that you make after this one.

`files`

(optional) You can use this to define what you want to send to the api as files. Note that you will have to download the files in the same integration before you are able to use this. This item needs to be defined like this:

```json
{
    "field_name": "filename.png"
}
```

It will search the previous responses by the key of the `files` dictionary. In this case that would be `filename.png`, so you would need to have `"save_as_file": "filename.png"` in any of the previous requests.
