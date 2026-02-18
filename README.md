# CivitAI scanner

It asks the Civit API for all content of the given Username and creates a nice CSV with all the Infos 
the API is providing. 

## Authentication

Set your CivitAI API token as an environment variable (recommended):

```bash
export CIVITAI_API_TOKEN=your_token_here
```

If the variable is not set, you will be prompted to enter it at startup (input is hidden). The token is sent via `Authorization: Bearer` header — never appended to URLs.

Example
This is the first line of the CSV with the user psoft of what you will find in username_output.csv.

Item Name
```
Shimakaze (kancolle) - Character
```
Model Version Name
```
v1.0, v2.0, etc...
```
Item Type
```
LORA
```
Base Model
```
SD15, Pony, Flux, etc...
```
File Name
```
shimakaze_v1.33.safetensors
```
Download URL
```
https://civitai.com/api/download/models/40743
```
Model Image
```
https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f691d97f-fac1-490f-1f4c-fc5de9132c00/width=450/557426.jpeg
```
Model Version URL
```
https://civitai.com/models/13157?modelVersionId=40743
```
