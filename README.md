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


    ## CLEAN VSCODE (If installing extension gives JSON error) `MACOS`
    
    - rm -fr ~/Library/Preferences/com.microsoft.VSCode.helper.plist 
    - rm -fr ~/Library/Preferences/com.microsoft.VSCode.plist 
    - rm -fr ~/Library/Caches/com.microsoft.VSCode 
    - rm -fr ~/Library/Caches/com.microsoft.VSCode.ShipIt/ 
    - rm -fr ~/Library/Application\ Support/Code/ 
    - rm -fr ~/Library/Saved\ Application\ State/com.microsoft.VSCode.savedState/ 
    - rm -fr ~/.vscode/

    `RETRY...`


        # url252f = "..%252fcookiehere.html"
        # url253266 = "..%25%32%66cookiehere.html"
        # local_host_url = "..%2fcookiehere.html"  # %252f is / and %2f is / and %25%32%66 is /
        # local_host_url252f = "..%252fcookiehere.html"
        # local_host_url253266 = "..%25%32%66cookiehere.html"
        # local_host_urlslash = "../cookiehere.html"
        # local_host_urldslash = "..//cookiehere.html"
        # local_host_url2slash = "%2e%2e/cookiehere.html"
        # local_host_url2dslash = "%2e%2e%2fcookiehere.html"
        # local_host_url2slash2slash = "..%2fcookiehere.html"
        # local_host_url2slash2dslash = "%2e%2e%2fcookiehere.html"
        # local_host_url2slash2slash2slash = "%252e%252e%252fcookiehere.html"


        # jobs.append((host_ip, port, url252f, extension))
        # jobs.append((host_ip, port, url253266, extension))
        # jobs.append((host_ip, port, local_host_urlslash, extension))
        # jobs.append((host_ip, port, local_host_urldslash, extension))
        # jobs.append((host_ip, port, local_host_url2slash, extension))
        # jobs.append((host_ip, port, local_host_url2dslash, extension))
        # jobs.append((host_ip, port, local_host_url2slash2slash, extension))
        # jobs.append((host_ip, port, local_host_url2slash2dslash, extension))
        # jobs.append((host_ip, port, local_host_url2slash2slash2slash, extension))
        # jobs.append((local_host_ip, port, url, extension))
        # jobs.append((local_host_ip, port, local_host_url, extension))
        # jobs.append((local_host_ip, port, local_host_url252f, extension))
        # jobs.append((local_host_ip, port, local_host_url253266, extension))
        # jobs.append((local_host_ip, port, local_host_urlslash, extension))
        # jobs.append((local_host_ip, port, local_host_urldslash, extension))
        # jobs.append((local_host_ip, port, local_host_url2slash, extension))
        # jobs.append((local_host_ip, port, local_host_url2dslash, extension))
        # jobs.append((local_host_ip, port, local_host_url2slash2slash, extension))
        # jobs.append((local_host_ip, port, local_host_url2slash2dslash, extension))
        # jobs.append((local_host_ip, port, local_host_url2slash2slash2slash, extension))
