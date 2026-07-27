# The final body to build (lesson 3)

Write a file named repaired.json containing one request body with:

1. a "model" string,
2. a "messages" ARRAY of two OBJECTS, each with "role" and "content"
   strings (one user, one assistant),
3. an "options" object holding a "max_tokens" number and a "stream"
   boolean (JSON spelling, not Python spelling),
4. a "tags" array of at least two strings, no trailing comma.

Validate it with the parser one-liner from the README, then keep it: it is
the request body you send in lesson 4.
