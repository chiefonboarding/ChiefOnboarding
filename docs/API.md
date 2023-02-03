---
order: 50
---

# API

This API will allow you to programmatically create new hires. The API does not work when you are logged in with sessions (logging in through the log in form), you will need to use a token to get access. These tokens do not expire and you can create them through shell.

## Setup
Enable the API through the environment variable:

```
API_ACCESS=True
```

Just to be safe, run the migrations for the token table `docker-compose run --rm web python3 manage.py migrate` (docker) or redeploy on Render/Heroku. Up next, you will have to generate a token to authenticate with the API. You will have to attach a user to it, like this:

```
docker-compose run --rm web python manage.py drf_create_token email@example.com
```
Use the email address from an admin user there. You will then get to see the newly created token. Now you can make calls to the API. Please note that if you ever remove this person, then the token will also be revoked.

Example:

```
curl -H "Authorization: Token xxxxxxxxxxxxxxx" https://YOURDOMAIN/api/employees/
```

## API usage example

### Adding a new hire

1. We would like to assign a buddy to this new hire, so first we need to get a list of employees to find the id of our buddy. Getting all employees that are in ChiefOnboarding:

```
curl -H "Authorization: Token xxxxxxxxxxxxxxx" https://YOURDOMAIN/api/employees/
```

2. We might also want to add some sequences to the new hire. In that case, we need the ids of the sequences we want to add. We can get all sequences with this request:

```
curl -H "Authorization: Token xxxxxxxxxxxxxxx" https://YOURDOMAIN/api/sequences/
```

2. Create the new hire:

```
curl -X POST -H 'Content-Type: application/json' -H 'Accept: application/json' -H "Authorization: Token xxxxxxxxxxxxxxx" -d '{"first_name":"James","last_name":"Weller","email":"james@chiefonboarding.com","phone":"","position":"Technical lead","language":"en","message":"","start_day":"2020-12-04","buddy":4,"timezone":"UTC","sequences":[3], "role":0}' https://YOURDOMAIN/api/newhires/
```

!!!
`first_name`, `last_name`, `role` and `email` are required
!!!

Role options (note: keep an eye on updates, this will likely change soon):

`0`: new hire

`1`: administrator

`2`: manager 

`3`: other (user will not get notified and does not have any meaningful permissions, no slack connection either)


The data part of that query (with explanation):

```
{ 
	"first_name": "James", # required
	"last_name": "Weller", # required
	"email": "james@chiefonboarding.com", # required and should be the business email address (even if not created yet)
	"phone": "1233444",
	"position": "Technical lead",
	"language": "en",
	"message": "This is our new hire....",
	"start_day": "2020-12-04", # if not provided, it will default to the day you create this request
	"buddy": 4, # the id of the employee taken from previous request
	"manager": 3, # the id of the employee taken from previous request
	"timezone": "UTC", # if not provided, it will default to the organization timezone
	"sequences": [5, 3], # Array of sequence ids that should be assigned to the user
    "role": 0 # role of the user (see above)
}
```

It will return the full new hire object including the ID of the new hire.
