def general_http_response_codes(response):
    response_status = str(response.status_code)
    if '200' in response_status:
        print('Website Response = 200: Connected successfully')
    elif '301' in response_status:
        print('Website Response = 301: Redirected to a different endpoint')
    elif '400' in response_status:
        print('Website Response = 400: Bad request, try again')
    elif '401' in response_status:
        print('Website Response = 401: Login required')
    elif '403' in response_status:
        print('Website Response = 403: Forbidden')
    elif '404' in response_status:
        print('Website Response = 404: Cannot access requested site')
    elif '429' in response_status:
        print('Website Response = 429: Too many requests (rate limited)')
    elif '503' in response_status:
        print('Website Response = 503: Server is not ready to handle request')
    else:
        print('N/A')

def iex_http_response_codes(IEXResponse):
    response_status = str(IEXResponse.status_code)
    if '200' in response_status:
        print('IEX Response =', response_status,
              'Connected successfully')
    elif '400' in response_status:
        print('IEX Response =', response_status,
              'Invalid values were supplied for the API request/'
              'No symbol provided/'
              'Batch request \"types\" parameter requires a valid value')
    elif '401' in response_status:
        print('IEX Response =', response_status,
              'Hashed token authorization is restricted/'
              'Hashed token authorization is required/'
              'The requested data is marked restricted and the account does not have access/'
              'An API key is required to access the requested endpoint/'
              'The secret key is required to access to requested endpoint/'
              'The referer in the request header is not allowed due to API token domain restrictions')
    elif '402' in response_status:
        print('IEX Response =', response_status,
              'You have exceeded your allotted credit quota/'
              'The requested endpoint is not available to free accounts/'
              'The requested data is not available to your current tier')
    elif '403' in response_status:
        print('IEX Response =', response_status,
              'Hashed token authorization is invalid/'
              'The provided API token has been disabled/'
              'The provided API token is not valid/'
              'A test token was used for a production endpoint/'
              'A production token was used for a sandbox endpoint/'
              'Your pay-as-you-go circuit breaker has been engaged and further requests are not allowed/'
              'Your account is currently inactive')
    elif '404' in response_status:
        print('IEX Response =', response_status,
              'Unknown symbol provided/'
              'Resource not found')
    elif '413' in response_status:
        print('IEX Response =', response_status,
              'Maximum number of \"types\" values provided in a batch request')
    elif '429' in response_status:
        print('IEX Response =', response_status,
              'Too many requests hit the API too quickly. An exponential backoff of your requests is recommended')
    elif '451' in response_status:
        print('IEX Response =', response_status,
              'The requested data requires additional permission to access')
    elif '500' in response_status:
        print('IEX Response =', response_status,
              'Something went wrong on an IEX Cloud server')
    else:
        print('IEX Response =', response_status,
              'Unknown error')

