**Poetry API**
---
Takes an image as input and returns poetry generated from the image. Currently it only supports images.

* **URL**

	`/poetry`
  
* **Method**

	`GET`

* **URL Params**

	`imageUri - uri to download the image from Transloadit`

* **Header Params**

	`Authorization: Token <Firebase Id token>`

* **Success Response**

  * **Code:** 200
  * **Content:** `{poetry: <poetry content>}`

* **Error Response**
  * **Code:** 401 UNAUTHORIZED   
    **Content:** `WWW-Authenticate: Token realm="Authentication Required"`

  
  * **Code:** 402 INVALID INPUT  
    **Content:** `{error: "Invalid input type: audio or video"}`
    
  * **Code:** 404 NOT FOUND  
    **Content:** `{error: "Cannot find resource."}`

* **Sample Usage**

```nodejs
import request from 'superagent'

request.get('/poetry')
       .set('Authorization': 'Token ' + verySecretIdToken)
       .query({ imageUri: 'https://api2.transloadit.com/assemblies/myAssemblyId' })
       .end(function(err, res){
       		...
       });
```
