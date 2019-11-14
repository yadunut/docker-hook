# Docker Hub Hook

This is a webhook for Docker Hub for automated deployments.

## Use case

1. My deployment is setup such that all the containers are proxied by a nginx-proxy container. This requires them to be on the same network.
2. I do not like running programs outside of docker

Thus, I wrote this script. It waits for a post request to this handle, ensures that the UUID passed in the URL is correct, ensures that the callback url is correct, and runs it.
