# Headers
These headers will be send with every request, but can be overwritten by any headers set on a specific request. These could include some sort of token variable for authentication.

## Example:
```json
"headers": {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer {{TOKEN}}"
}
```
