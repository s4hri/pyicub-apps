
# GPT YARP Module

A YARP module to interface with Azure OpenAI LLMs via Azure GPT deployments, with support for:

- Multiple sessions
- Session persistence
- Streaming responses
- Dynamic model switching
- System prompt configuration
- Full YARP integration

---

## Features

- Built for Azure OpenAI (`AzureOpenAI` client)
- Supports `gpt-4.5-preview` and `gpt-4o-audio-preview` (fully configurable)
- YARP RPC interface for full control
- Streaming enabled by default
- Session management: create, reset, delete, switch
- System prompt can be set via file or runtime

---

### `requirements.txt`

```txt
openai>=1.10.0
```
---

## Configuration

### Create your `config.json`

```json
{
  "endpoint": "https://<your-resource-name>.openai.azure.com/",
  "api_version": "2025-02-27",
  "deployments": {
    "gpt-4.5-preview": "mydeploy_gpt45preview",
    "gpt-4o-audio-preview": "mydeploy_gpt4oaudiopreview"
  },
  "default_model": "gpt-4.5-preview",
  "temperature": 0.7,
  "top_p": 1.0,
  "max_length": 1024
}
```

### Create your system prompt file

Example `prompt.txt`:

```txt
You are a helpful robot assistant for the iCub robot. Answer concisely and politely.
```

---

## Azure API Key

Export your Azure OpenAI key:

```bash
export AZURE_API_KEY="your-azure-api-key"
```

---

## Running the module

```bash
python3 app.py --config config/config.json --prompt_file config/prompt.txt
```

---

## Testing

In another terminal:

```bash
yarp rpc /GPT/rpc:i
```

Then test step-by-step:

```bash
status
query Hello GPT
create_session test
switch_session test
query How are you?
list_sessions
set_model gpt-4o-audio-preview
query Are you running 4o?
```

You can also write via input port:

```bash
yarp write ... /GPT/text:i
Hello via YARP text port!
```

And read answers via:

```bash
yarp read /GPT/text:o
```

---

## Sessions

Sessions are saved automatically in `sessions.json`.

You can:

- `create_session <name>`
- `switch_session <name>`
- `reset_session <name>`
- `list_sessions`
- `delete_session <name>`

---

## Supported RPC Commands

| Command | Description |
|---------|-------------|
| `status` | Return module status |
| `query <text>` | Send a query |
| `set_system_prompt <prompt>` | Change system prompt |
| `create_session <id>` | Create a new session |
| `switch_session <id>` | Switch active session |
| `reset_session <id>` | Reset session history |
| `list_sessions` | List all sessions |
| `delete_session <id>` | Delete a session |
| `set_model <model>` | Change model (must exist in config) |
| `quit` | Stop module |

---

## Input/Output Ports

| Port            | Type          | Description                                  |
|------------------|---------------|----------------------------------------------|
| `/GPT/text:i`    | `yarp.Bottle` | Input text queries to GPT (plain text).      |
| `/GPT/text:o`    | `yarp.Bottle` | Output GPT responses (plain text).           |
| `/GPT/rpc:i`     | `yarp.Port`   | RPC port to send control commands.           |

---

## Future Extensions

- Whisper (speech-to-text) module
- TTS (text-to-speech) module
- Full iCub cognitive loop integration

---

## License

MIT License — free to use & extend.

---