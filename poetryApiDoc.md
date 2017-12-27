**Documentation**
---

* **URL**

	`/poetry`

  Takes an image as input and returns poetry generated from the image. Currently it only supports images.

* **Method**

	`GET`

* **URL Params**

	`imageUri - uri to download the image from s3`
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
       .query({ imageUri: 'https://xxx.s3.amazonaws.com/...', mine: 'image/png' })
       .end(function(err, res){
       		...
       });
```




* **URL**

	`/caption`

  Takes a video as input and returns captions generated from video, one line every 2 seconds.

* **Method**

	`GET`

* **URL Params**

	`videoUri - uri to download the image from s3`
	`mime - video mime type`
	`duration - video duration in seconds`

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

request.get('/caption')
       .set('Authorization': 'Token ' + verySecretIdToken)
       .query({ video: 'https://xxx.s3.amazonaws.com/...', mime: 'video/mp4', duration: '7.44'})
       .end(function(err, res){
       		...
       });
```
