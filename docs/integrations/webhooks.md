# Trigger a third party url
Here is an example of a manifest of an integration (in this case to add a user to an Asana team):

```json
{
	"form": [
        {
            "id": "TEAM_ID",
            "url": "https://app.asana.com/api/1.0/organizations/{{ORG}}/teams",
            "name": "Select team to add user to",
            "type": "choice",
            "data_from": "data",
            "choice_value": "gid",
            "choice_name": "name"
        }
    ],
	"exists": {
		"url": "https://app.asana.com/api/1.0/users/{{email}}",
		"method": "GET",
		"expected": "{{email}}"
	},
	"execute": [
        {
			"url": "https://app.asana.com/api/1.0/workspaces/{{ORG}}/addUser",
			"data": {
				"data": {
					"user": "{{email}}"
				}
			},
			"method": "POST"
		},
		{
			"url": "https://app.asana.com/api/1.0/teams/{{TEAM_ID}}/addUser",
			"data": {
				"data": {
					"user": "{{email}}"
				}
			},
			"method": "POST"
		}
	],
	"headers": {
		"Accept": "application/json",
		"Content-Type": "application/json",
		"Authorization": "Bearer {{TOKEN}}"
	},
	"initial_data_form": [
        {
			"id": "TOKEN",
			"name": "Please put your token here",
			"description": "You can find your token here: https://...."
		},
		{
			"id": "ORG",
			"name": "Organization id",
			"description": "You can find your organization id here: https://..."
		}
	]
}
```

## Notes
* If triggering an integration fails, then it will retry the entire integration again one hour after failing. If it fails again, it will not retry.
* If you are using any of the integrations from the repo at: https://integrations.chiefonboarding.com then you have to validate them yourself. This is a user repository and we do not actively moderate the submissions there. Please always validate the urls where requests are going to make sure it's legit. 
