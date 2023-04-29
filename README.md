## Challenges

- Downloading multiple extensions at same time, Since Microsoft does not provide API to search based on keywords.
- Microsoft also limit number of requests for any particular IP address and extension ID.
- How to get the port number from the `package.json`, `package.nls.json` files.
- How to get the port number, which is currently used by the extension. (Most extensions allocate port numbers randomly)
- Checking for path traversal in the extension using variants of URI's, headers like `User-Agents` and other parameters.
- Automating the whole process using python coroutines made it much faster which was a challenge in itself.
