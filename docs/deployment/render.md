# Deploy with Render
You will have to login to Render or create an account there. Then, you will need to click this link to start the process: [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/chiefonboarding/chiefonboarding/) 

You will then need to fill in the following details:

`ALLOWED_HOSTS`

This needs to be the domain you want to use for the platform. Either your Render subdomain or your own subdomain. You can add multiple urls if you want to make it available with multiple urls (example: `domain.example.com,domain2.example.com`). Do **not** add the protocol (`https://`) before the url. If you don't have a url, use `test.chiefonboarding.com` and change it later to your `xxxx.onrender.com` link.

Click on deploy and let it run. This will take about 10 minutes before it's ready, though it could take a few hours, so be patient please. 

**If you DO have a domain name**:

Go to the `chiefonboarding` service and go to `settings`. Scroll down until you see the `Custom domain` setting. Add your domain there and configure your DNS to link to it.

**If you DO NOT have a domain name**:

Go to environment variables and swap the `ALLOWED_HOSTS` and `BASE_URL` with the url that has been given to you by Render. Wait for it to automatically redeploy.

That's all!
