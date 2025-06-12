import os
from openai import AzureOpenAI
 
# Set your variables here:
AZURE_API_KEY = "yourkey"
AZURE_ENDPOINT = "https://<your-resource-name>.openai.azure.com/"
AZURE_API_VERSION = "2024-12-01-preview"
DEPLOYMENT_NAME = "mydeploy_gpt45preview"
 
# Initialize client
client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION
)
 
# Perform test call
response = client.chat.completions.create(
    model=DEPLOYMENT_NAME,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello world!"}
    ],
    temperature=0.7,
    top_p=1.0,
    max_tokens=512
)
 
# Print result
print("Response:\n", response.choices[0].message.content)