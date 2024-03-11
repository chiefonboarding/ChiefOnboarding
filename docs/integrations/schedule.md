# Schedule

You can run integrations with the `action` set to `create` manually (by going to people -> colleagues -> import...). If you provide a `schedule` prop (cron notation), then it will run this in the background. It will create/update the users automatically. 

## Example
```json
{
    "schedule": "* 1 * * * *"
}
```
