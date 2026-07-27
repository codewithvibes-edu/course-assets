# Flow diagram worksheet (lesson 1)

Fill in every bracket, then narrate the whole round trip out loud without
using the word "API". If you can only explain it with the word you are
defining, you have not finished the lesson.

```
[YOUR MACHINE]                                [THE SERVER]

 client: ______________                        service: ______________
 (the program that sends:                      (the program that answers:
  curl, your script,                            here, mock_service.py;
  an SDK under the hood)                        in production, the
        |                                       provider's fleet)
        |
        |  base URL: _______________________
        |  (which SERVER to talk to)
        |
        |  endpoint: _______________________
        |  (which CAPABILITY on that server)
        |
        |------------- REQUEST ------------->
        |   method: ______
        |   headers: ______________________
        |   body: _________________________
        |
        |<------------ RESPONSE -------------
        |   status: ______
        |   headers: ______________________
        |   body: _________________________
```

## The words, kept apart

| Word | What it means here | The thing it is NOT |
| --- | --- | --- |
| provider | the organization operating the service | the server machine itself |
| server | the machine/program answering on a base URL | the whole provider |
| base URL | `http://127.0.0.1:8124` | an endpoint |
| endpoint | `/v1/echo` | the whole address |
| client | whatever sends the request | "the terminal" |
| SDK | a library that builds these requests for you | a different protocol |

Module 0's first_call.py sent exactly one of these round trips. The SDK
recipes hid the request behind a function call. Same wire, same anatomy,
nothing new under there.
