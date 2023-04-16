import base64

zip_file_path = 'example.zip'
output_file_path = 'base64_encoded_zip.txt'

# Read the ZIP file as binary data
with open(zip_file_path, 'rb') as zip_file:
    zip_data = zip_file.read()

# Encode the binary data to a base64 string
base64_encoded_zip = base64.b64encode(zip_data).decode('utf-8')

# Write the base64-encoded string to a new text file
with open(output_file_path, 'w') as output_file:
    output_file.write(base64_encoded_zip)

print(f"Base64-encoded string of {zip_file_path} saved to {output_file_path}.")

