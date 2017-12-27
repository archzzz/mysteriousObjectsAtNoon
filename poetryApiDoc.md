**Poetry API**
---
Takes an image as input and returns poetry generated from the image. Currently it only supports images.

* **URL**

	`/poetry`
  
* **Method**

	`GET`

* **URL Params**

	`imageUri - uri to download the image from Transloadit`
	`mime - image mime type`

* **Header Params**

	`Authorization: Token <Firebase Id token>`

* **Success Response**

  * **Code:** 200
  * **Content:** `{poetry: <poetry content>}`

* **Error Response**
  * **Code:** 400 Bad Request
  * **Code:** 401 Unauthorized    
  * **Code:** 404 Not Found  

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
