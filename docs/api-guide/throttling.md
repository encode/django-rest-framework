<a class="github" href="throttling.py"></a>

# Throttling

> HTTP/1.1 420 Enhance Your Calm
>
> [Twitter API rate limiting response][cite]

[cite]: https://dev.twitter.com/docs/error-codes-responses

Throttling is similar to [permissions], in that it determines if a request should be authorized.  Throttles indicate a temporary state, and are used to control the rate of requests that clients can make to an API.

As with permissions, multiple throttles may be used.  Your API might have a restrictive throttle for unauthenticated requests, and a less restrictive throttle for authenticated requests.

Another scenario where you might want to use multiple throttles would be if you need to impose different constraints on different parts of the API, due ato some services being particularly resource-intensive.

Throttles do not necessarily only refer to rate-limiting requests.  For example a storage service might also need to throttle against bandwidth.

## How throttling is determined

As with permissions and authentication, throttling in REST framework is always defined as a list of classes.

Before running the main body of the view each throttle in the list is checked.
If any throttle check fails an `exceptions.Throttled` exception will be raised, and the main body of the view will not run.

## Setting the throttling policy

The default throttling policy may be set globally, using the `DEFAULT_THROTTLES` setting.  For example.

    API_SETTINGS = {
        'DEFAULT_THROTTLES': (
            'djangorestframework.throttles.AnonThrottle',
            'djangorestframework.throttles.UserThrottle',
        )
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/day',
            'user': '1000/day'
        }        
    }

You can also set the throttling policy on a per-view basis, using the `APIView` class based views.

    class ExampleView(APIView):
        throttle_classes = (UserThrottle,)

        def get(self, request, format=None):
            content = {
                'status': 'request was permitted'
            }
            return Response(content)

Or, if you're using the `@api_view` decorator with function based views.

    @api_view('GET')
    @throttle_classes(UserThrottle)
    def example_view(request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)

## AnonThrottle

The `AnonThrottle` will only ever throttle unauthenticated users.  The IP address of the incoming request is used to identify 

`AnonThrottle` is suitable if you want to restrict the rate of requests from unknown sources.

## UserThrottle

`UserThrottle` is suitable if you want a simple restriction

## ScopedThrottle

## Custom throttles

[permissions]: permissions.md