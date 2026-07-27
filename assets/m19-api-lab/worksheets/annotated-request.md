# Annotated request worksheet (lesson 2)

Below is one complete raw request to the lab service. Annotate every line:
what it is, who demands it (the protocol, this service, or your choice),
and where the value should live (code, configuration, or secret store).
No line stays unexplained. "It was in the example" is not an explanation;
it is the fog this module exists to burn off.

```
POST /v1/echo HTTP/1.1
Host: 127.0.0.1:8124
Authorization: Bearer mock-key-local-only
Content-Type: application/json
Content-Length: 47

{"model": "mock-1", "input": "What is an API?"}
```

| Line | What it is | Protocol / service-specific / your choice | Lives in code / config / secret store |
| --- | --- | --- | --- |
| `POST` | | | |
| `/v1/echo` | | | |
| `HTTP/1.1` | | | |
| `Host:` | | | |
| `Authorization:` | | | |
| `Content-Type:` | | | |
| `Content-Length:` | | | |
| the body | | | |
| `"model"` field | | | |
| `"input"` field | | | |

## The sorting rule that transfers

Protocol parts (method, Host, Content-Length) look the same on every
service you will ever call. Service-specific parts (the endpoint path, the
auth header NAME, the body field names) are what change when you switch
providers, and they are exactly what Module 21's adapter will normalize.
Your-choice parts (which model, what input) are configuration. When you
can sort any request line into one of those three buckets on sight, copied
examples stop being spells and start being mail.
