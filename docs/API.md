---
order: 50
---

# API

!!!
The API does not work in v2.0 yet! It will still work for versions starting with v1
!!!

This API will give you full control over ChiefOnboarding. ChiefOnboarding is built with Django and VueJS. Django is used as an API and VueJS is for the front end. With the steps below, you will be able to call the whole API yourself. Currently, ChiefOnboarding uses sessions/cookies for authentication. We can't use those for the API, as those expire. Therefore, you will have to explicitly enable token authentication in the settings. 

Please note that tokens do not expire and endpoints are subjected to change with updates!

## Setup
Enable the API through the environment variable:

```
API_ACCESS=True
```

Just to be safe, run the migrations for the token table `docker-compose run web python3 manage.py migrate`. Up next, you will have to generate a token to authenticate with the API. You will have to attach a user to it, like this:

```
docker-compose run web python manage.py drf_create_token email@example.com
```
Use the email address from an (admin) user there. You will then get to see the newly created token. Now you can make calls to the API. 

Example:

```
curl -H "Authorization: Token xxxxxxxxxxxxxxx" https://YOURDOMAIN/api/users/admin
```

## API usage example

### Adding a new hire

1. We would like to assign a buddy to this new hire, so first we need to get a list of employees to find the id of our buddy. Getting all employees that are in ChiefOnboarding:

```
curl -H "Authorization: Token xxxxxxxxxxxxxxx" https://YOURDOMAIN/api/users/employee
```

2. Create the new hire:

```
curl -X POST -H "Authorization: Token xxxxxxxxxxxxxxx" -d {"first_name":"James","last_name":"Weller","email":"james@chiefonboarding.com","phone":"","position":"Technical lead","language":"en","message":"","start_day":"2020-12-04","buddy":4,"manager":null,"timezone":"UTC","google":{"create":false,"email":""},"slack":{"create":false,"email":""},"sequences":[{"id":5}]} -H "Content-Type: application/json" https://YOURDOMAIN/api/users/new_hire
```

The data part of that query (with explanation):

```
{ 
	"first_name": "James", # required
	"last_name": "Weller", # required
	"email": "james@chiefonboarding.com", # required and should be the business email address (even if not created yet)
	"phone": "",
	"position": "Technical lead",
	"language": "en",
	"message": "",
	"start_day": "2020-12-04", # required
	"buddy": 4, # the id of the employee taken from previous request
	"manager": null,
	"timezone": "UTC",
	"google": { # Google account creation, it will create the email address from the new hire
 		"create": false,
 		"email": "" # this should be the email where the login details are sent to (so, not the business email address)
 	},
	"slack": {
		"create": false,
		"email": "" # probably business email address (invite email is sent to this)
	},
	"sequences": [ # sequences that are automatically assigned to new hire
		{ "id": 5 } 
	]
}
```
It will return the full new hire object including the ID of the new hire.
