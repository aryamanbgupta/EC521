## Pending Tasks

- ~~Figure out how to get the port number from the package.json file~~
- ~~Write 2 implementations one to figure out with regex and another to figure out with a `for` loop as fallback~~
- ~~Create a new html file with some specified content which will be used to check path traversal~~
- ~~Use the curl command or its variants to check for path traversal~~
- ~~Create a new output json which will hold all extensions with this vulnerability~~


## Extended Tasks

- Include package.nls.json files in the search


## Challenges

- Downloading multiple extensions at same time, Since Microsoft does not provide API to search based on keywords.
- Microsoft also limit number of requests for any particular IP address and extension ID.
- How to get the port number from the `package.json`, `package.nls.json` files.
- How to get the port number, which is currently used by the extension. (Most extensions allocate port numbers randomly)
- Checking for path traversal in the extension using variants of URI's, headers like `User-Agents` and other parameters.
- Automating the whole process using python coroutines made it much faster which was a challenge in itself.
