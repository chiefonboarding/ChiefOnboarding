# Paginated response
Sometimes, we might not get all items at once. We have something to cover that too

`amount_pages_to_fetch`

Default: `5`. Maximum amount of page to fetch. It will stop earlier if there are no users found anymore. There might be a limit to this number. Please see the note below.

There are two ways of fetching a new page: 
1. Sometimes an API will only return a token and we will have to build the url ourselves. (Google does this for example)
2. In most cases, you will get a full url that you can use to fetch the new page of users.

For case 1, you will need to provide two items (the url and where the token is):

`next_page_token_from`

The place to look for the next page token. You can use the dot notation to do go deeper into the JSON. If it's not found, it will stop.

`next_page`

This should be a fixed url that you should put here. You can use `{{ NEXT_PAGE_TOKEN }}` as the variable to include the previously found `next_page_token_from` value.

For example, this is necessary for Google:

```json
"next_page": "https://admin.googleapis.com/admin/directory/v1/users?customer=my_customer&maxResults=500&pageToken={{ NEXT_PAGE_TOKEN }}",
"next_page_token_from": "nextPageToken"
```

For case 2, you will only need to provide the place where we need to look for the URL with this item:

`next_page_from`

The place to look for the next page url. You can use the dot notation to do go deeper into the JSON. If it's not found, it will stop.

Note: fetching users is being done live when you visit the page. If you set a high amount of pages to be fetched, then this might cause a timeout on the server. It makes rendering all users on the client also very sluggish. We recommend to not load more than 5000 users or not more than 10 pages (if a timeout of 30 seconds is set on your server (like Heroku for example)), whichever comes first. If you do need more, then we recommend going for an alternative method of importing users.
