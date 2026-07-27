# Error decision tree (lesson 5)

Fill this in from the seven exhibits (live endpoints or
fixtures/responses/). The finished tree is your artifact: symptom on the
left, evidence you read in the middle, YOUR next action on the right.
Keep it to one page. You are building a reflex, not documentation.

| Status | Error type you saw | The evidence worth reading (body fields, headers) | Whose problem | Next action |
| --- | --- | --- | --- | --- |
| 2xx | | | | |
| 400 | | | | fix ______ before retrying |
| 401 | | | | |
| 403 | | | | (how is this different from 401?) |
| 404 | | | | |
| 429 | | which header tells you HOW LONG to wait? | | |
| 5xx | | which value do you quote when you report it? | | |

## Three rules to hold while you fill it in

1. Status class first (4xx: your side; 5xx: their side), THEN the error
   body for the specifics. The class decides who acts; the body decides
   what the action is.
2. Not every service uses these exact fields or even these exact codes.
   The reflex that transfers is "read status, read body, read headers,
   then decide," not a memorized table of one provider's spellings.
3. Retrying a 400 with the same input is asking the same wrong question
   louder. Match the action to the evidence: fix input, refresh access,
   wait the stated time, retry, or report with the request ID.
