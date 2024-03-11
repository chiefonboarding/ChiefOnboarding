# Object storage (up/downloading files)
You can use AWS S3 for this, but you are also free to use any other provider who provides the same API. For example: Wasabi, Vultr, Digital Ocean, or Fuga cloud.

The instructions below will set everything up by using client/secret token. You can also use a profile/role if you prefer. Under the hood, ChiefOnboarding uses `boto3`, which means that it will search for credentials by itself as well. Please see the documentation for those boto3 environment variables here: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html

Note that you might still need to set some of the environment variables below (such as the bucket).

Here is a step-by-step for AWS:

1. Go to [https://s3.console.aws.amazon.com/s3/home](https://s3.console.aws.amazon.com/s3/home) and click on 'Create bucket'.
2. Give it a fancy name and click on 'Next'.
3. Keep everything at the default (or change it to your liking) and click on 'Next'.
4. Keep everything at the default and click on 'Next'.
5. Click on your newly created bucket.
6. In the bucket, go to 'Permissions' and then to 'CORS'.
7. Add this CORS configuration there (change YOURDOMAIN):

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "PUT",
            "POST",
            "DELETE",
            "GET"
        ],
        "AllowedOrigins": [
            "https://YOURDOMAIN"
        ],
        "ExposeHeaders": []
    }
]
``` 

The bucket is now created. Up next, we need to create a user to be able to post and get from this bucket.

6. Go to [https://console.aws.amazon.com/iam/home#/users](https://console.aws.amazon.com/iam/home#/users).
7. Click on 'Add user'.
8. Give it a fancy user name and select 'Programmatic access', so we get the keys we need to enter in ChiefOnboarding. Click on 'Next'.
9. Go to 'Attach existing policies directly' and click then 'Create policy'.
10. For 'Service' pick 'S3'.
11. For 'Actions' pick 'GetObject', 'DeleteObject' and 'PutObject'. 
12. Under 'Resources', enter the correct bucket name and for the 'Object name' select 'Any'.
13. Click on 'Add'.
14. Click on 'Review policy'.
15. Give it a fancy name and click on 'Create policy'.
16. Go back to the set up screen of your IAM user and click on the refresh button to refresh policies. 
17. Add your newly created policy to the user and click on 'Next'.
18. Click on 'Next' again. Twice.
19. You will now get to see the Access key ID and the Secret access key. Add those to your environment variables or .env file. 

Example variables:

```ini
AWS_S3_ENDPOINT_URL=https://s3.eu-west-1.amazonaws.com
AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXX
AWS_STORAGE_BUCKET_NAME=bucket-name
AWS_DEFAULT_REGION=eu-west-1
```

If you want to use Minio (self-hosted), then you could use something like this as an example for both ChiefOnboarding and Minio:

```yaml
# docker-compose.yml
version: '3'                  
                                                                                                                   
services:                      
  db:                                   
    image: postgres:latest                 
    restart: always         
    expose:    
      - "5432"
    volumes: 
      - pgdata:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=chiefonboarding
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    networks:
      - global 
                                                         
  web:      
    image: chiefonboarding/chiefonboarding:latest
    restart: always   
    expose:             
      - "8000"              
    environment:
      - SECRET_KEY=somethingsupersecret
      - DATABASE_URL=postgres://postgres:postgres@db:5432/chiefonboarding
      - ALLOWED_HOSTS=test.chiefonboarding.com
      - AWS_S3_ENDPOINT_URL=https://minio.chiefonboarding.com
      - AWS_ACCESS_KEY_ID=chief
      - AWS_SECRET_ACCESS_KEY=chiefpass
      - AWS_STORAGE_BUCKET_NAME=test-bucket
      - AWS_DEFAULT_REGION=us-east-1
    depends_on:                                      
      - db                                                                                                         
    networks:
      - global

  caddy:
    image: caddy:2.3.0-alpine
    restart: unless-stopped
    ports:     
      - "80:80"
      - "443:443"
    volumes:
      - $PWD/Caddyfile:/etc/caddy/Caddyfile
      - $PWD/site:/srv
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - global

  minio-server:
    image: minio/minio
    expose:
      - "9000"
      - "9001"
    volumes:
      - ./storage/minio:/data
    environment:
      - MINIO_ROOT_USER=chief
      - MINIO_ROOT_PASSWORD=chiefpass
      - MINIO_DOMAIN=http://minio.chiefonboarding.com
    command: server --address 0.0.0.0:9000 --console-address 0.0.0.0:9001 /data
    networks:
      - global

volumes:
  pgdata:
  caddy_data:
  caddy_config:

networks:
  global:
```

Caddyfile

```bash
test.chiefonboarding.com {
  reverse_proxy web:8000
}
minio.chiefonboarding.com {
  reverse_proxy minio-server:9000
}
minio-console.chiefonboarding.com {
  reverse_proxy minio-server:9001
}
```
