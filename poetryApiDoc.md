**Poetry API**
---
Takes an image as input and returns poetry generated from the image. Currently it only supports images.

* **URL**

	`/poetry`
  
* **Method**

	`GET`

* **URL Params**

	`imageUri - uri to download the image from Transloadit`

	`idToken - Firebase Id token`

* **Success Response**

  * **Code:** 200
  * **Content:** `{poetry: <poetry content>}`

* **Error Response**
  * **Code:** 401 UNAUTHORIZED   
    **Content:** `{error: "login"}`  
  
  * **Code:** 402 INVALID INPUT  
    **Content:** `{error: "Invalid input type: audio or video"}`
    
  * **Code:** 404 NOT FOUND  
    **Content:** `{error: "Cannot find resource."}`

* **Sample Usage**

```nodejs
import request from 'superagent'

request.get('/poetry')
       .query({ imageUri: 'https://api2.transloadit.com/assemblies/myAssemblyId' })
       .query({ idToken: 'verysecritidtoken'})
       .end(function(err, res){
       		...
       });
```
