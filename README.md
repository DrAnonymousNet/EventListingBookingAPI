# EventListingBookingAPI

Just A simple API to publish Event where people can RSVP.

Once you have cloned Repository, and Install packages,Create a postgres Database and add the configuration in the .env file.

Create a SuperUser as no form of Authentication is configured.

You can use the superuser as Event Owner.

Register an application in the [Google Console](https://console.cloud.google.com/apis/credentials/consent) to get a ClientID and Client Secret

Add the Client Credentials in the .env file:

```
GOOGLE_OUTH_CLIENT_ID=
GOOGLE_OUTH_CLIENT_SECRET=
```

Obtain a Google API Secret Key from the [Google Dashboard](https://console.cloud.google.com/apis/dashboard) and Enable the GeoEncoding and GeoLocation API and optionally the GeoDirection API from the [Google Map Console](https://console.cloud.google.com/google/maps-apis/api-list)

Add the Secret keys in the .env file:

```
GOOGLE_DIRECTION_SECRET_KEY=
```



