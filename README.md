# Pillars

## Overview
Pillars was Created to give Slack's Nebula a simplified frontend.  

With it, you can create new nebulas (certificate authorities) and sign client certificates for your nebula endpoints.

Today, Pillars gathers your input, creates certificates and config files, and hands them back to you.

### Deployment

```
docker run --name pillars -d -p 80:80 natemellendorf/nebula-pillars
```

GitHub OAuth support has been added, but is not leveraged by Pillars yet.  
To test, you can [create your own OAuth App](https://developer.github.com/apps/building-oauth-apps/creating-an-oauth-app/) within GitHub and pass in your ID and Key: 
```
docker run --name pillars -d \
-p 80:80 \
-e GITHUB_CLIENT_ID='your_app_id' \
-e GITHUB_CLIENT_SECRET='your_app_secret' \
natemellendorf/nebula-pillars
```

### ToDo

- Add pipeline
  - linting
  - pytest
- Clone / build from the Nebula project vs. using the binary. (lazy)
- Use Alpine:Go vs. Ubuntu for container 
- Clean up requirements.txt
- Create API
- ~Add GitHub OAuth~
- Add No/SQL backed
  - Too much is happening within the local dir
- Fix socketio emits
- ~Add download button vs. using popup~
- Allow for cert overwrite (if needed)
- Look into small IPAM to report in pool size?
- Create demo docs
- Add in support for remaining Nebula features
  - Groups
  - Firewall
  - set local listening port
  - set local interface
  - ?

### Credit

Pillars is a personal project built to enhance Nebula.  
Nebula is an open source project published by Slack.   
Check out the [Nebula Project](https://github.com/slackhq/nebula) for more information.   

### Authors
Nate Mellendorf <br>
[https://www.linkedin.com/in/nathan-mellendorf/](https://www.linkedin.com/in/nathan-mellendorf/)<br>

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.me/natemellendorf/10)
