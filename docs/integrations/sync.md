# Sync/Create users integration
You can define background tasks to sync/create users based on an external API. This could be Slack or Google for example.

## Create example
A configuration for creating users based on BambooHR would look like this:

```json
{
    "execute": [
        {
            "url": "https://api.bamboohr.com/api/gateway.php/{{COMPANY_ID}}/v1/reports/{{REPORT_ID}}",
            "method": "GET"
        }
    ],
    "headers": {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic {{KEY}}:x"
    },
    "action": "create",
    "data_from": "employees",
    "data_structure": {
        "email": "workEmail",
        "last_name": "lastName",
        "first_name": "firstName"
    },
    "initial_data_form": [
        {
            "id": "KEY",
            "name": "The BambooHR api key",
            "description": "Go to: https://<yourdomain>.bamboohr.com/settings/permissions/api.php to get one"
        },
        {
            "id": "REPORT_ID",
            "name": "The id of the report",
            "description": "Go to: https://<yourdomain>.bamboohr.com/app/reports/ to find the id of the report. click on the report and then look at the url. There is a number that will represent the ID of the report."
        },
        {
            "id": "COMPANY_ID",
            "name": "The id of the company",
            "description": "When you login you get a domain like this: https://<yourdomain>.bamboohr.com/. The '<yourdomain>' is your domain name. "
        }
    ]
}
```


## Update example
This will allow you to save additional data from a third party to your user. This can be helpful in case you need a specific ID in an integration that is tied to this user for example. You cannot update core attributes of a user (such as their email or first name). You can only save extra information to the user, which can then be used in integrations or content boxes. 

A configuration to update users would look like this:

```json
{
    "execute": [
        {
            "url": "https://api.bamboohr.com/api/gateway.php/{{COMPANY_ID}}/v1/reports/{{REPORT_ID}}",
            "method": "GET"
        }
    ],
    "headers": {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic {{KEY}}:x"
    },
    "data_from": "employees",
    "data_structure": {
        "bamboohr_id": "id"
    },
    "action": "update",
    "schedule": "0 * * * *",
    "initial_data_form": [
        {
            "id": "KEY",
            "name": "The BambooHR api key",
            "description": "Go to: https://<yourdomain>.bamboohr.com/settings/permissions/api.php to get one"
        },
        {
            "id": "REPORT_ID",
            "name": "The id of the report",
            "description": "Go to: https://<yourdomain>.bamboohr.com/app/reports/ to find the id of the report. click on the report and then look at the url. There is a number that will represent the ID of the report."
        },
        {
            "id": "COMPANY_ID",
            "name": "The id of the company",
            "description": "When you login you get a domain like this: https://<yourdomain>.bamboohr.com/. The '<yourdomain>' is your domain name. "
        }
    ]
}
```

That configuration would add the `id` from the bambooHR user to the ChiefOnboarding user account.

The schedule prop is mandatory here as it would otherwise never run, you cannot trigger this manually. The other main difference with the create option is the "action". It's "update" in this case.
You will also have to provide the `email` key in the `data_structure`, so ChiefOnboarding knows how to match the user. If no user can be found with the provided `email`, then it will get skipped.
