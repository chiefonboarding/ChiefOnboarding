# Action

This will either be `create` or `sync`. This depends on what you want it to do.
With `sync` it will sync users that don't exist yet to ChiefOnboarding. Those will be created as "other" people (they have no rights and cannot login).

With `create` users will be created and you can define what should be copied over to the user in ChiefOnboarding. It will not touch any other users 

Both options are based entirely on the `emailaddress`. If the API doesn't return the emailaddress, then you cannot use this at all.
