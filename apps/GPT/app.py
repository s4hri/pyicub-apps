
import yarp
import sys
import json
import os
from openai import AzureOpenAI
from openai import APIConnectionError, RateLimitError, Timeout, APIError


class GPT(yarp.RFModule):

    def configure(self, rf):
        self.period = 0.1
        self.sessions_file = "sessions.json"
        self.total_tokens_used = 0

        self._setup_ports()

        self.config_path = rf.check("config", yarp.Value("")).asString()
        if not self.config_path:
            print("[ERROR] Missing config file path")
            return False

        if not self._load_config():
            return False

        self.prompt_path = rf.check("prompt_file", yarp.Value("")).asString()
        self._load_system_prompt()

        try:
            self.client = AzureOpenAI(
                azure_endpoint=self.config['endpoint'],
                api_key=os.getenv("AZURE_API_KEY"),
                api_version=self.config['api_version']
            )
        except Exception as e:
            print(f"[ERROR] AzureOpenAI init failed: {e}")
            return False

        self.sessions = {}
        self.token_usage = {}
        self.active_session = "default"
        self._create_session(self.active_session)

        self._load_sessions_from_file()

        self.status = 'idle'
        self.query_via_rpc = False
        self.text_via_rpc = ""

        return True

    def _setup_ports(self):
        self.input_port = yarp.BufferedPortBottle()
        self.input_port.open("/GPT/text:i")

        self.output_port = yarp.BufferedPortBottle()
        self.output_port.open("/GPT/text:o")

        self.rpc_port = yarp.Port()
        self.rpc_port.open("/GPT/rpc:i")
        self.attach(self.rpc_port)

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            self.deployments = self.config['deployments']
            self.current_model = self.config['default_model']
            self.temperature = self.config.get('temperature', 0.7)
            self.top_p = self.config.get('top_p', 1.0)
            self.max_tokens = self.config.get('max_length', 1024)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            return False

    def _load_system_prompt(self):
        if self.prompt_path and os.path.isfile(self.prompt_path):
            try:
                with open(self.prompt_path, 'r') as f:
                    self.system_prompt = f.read().strip()
            except Exception as e:
                print(f"[ERROR] Failed to read prompt file: {e}")
                self.system_prompt = "You are a helpful assistant."
        else:
            self.system_prompt = self.config.get('system_prompt', "You are a helpful assistant.")
        print(f"[INFO] System prompt loaded:\n{self.system_prompt}")

    def _create_session(self, session_id):
        self.sessions[session_id] = [{"role": "system", "content": self.system_prompt}]
        self.token_usage[session_id] = 0

    def _reset_session(self, session_id):
        self.sessions[session_id] = [{"role": "system", "content": self.system_prompt}]
        self.token_usage[session_id] = 0

    def reset_active_session(self):
        self._reset_session(self.active_session)

    def _save_sessions_to_file(self):
        try:
            data = {
                "sessions": self.sessions,
                "token_usage": self.token_usage
            }
            with open(self.sessions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save sessions: {e}")

    def _load_sessions_from_file(self):
        if not os.path.isfile(self.sessions_file):
            return
        try:
            with open(self.sessions_file, 'r') as f:
                data = json.load(f)
                self.sessions = data.get("sessions", {})
                self.token_usage = data.get("token_usage", {})
            if self.active_session not in self.sessions:
                self._create_session(self.active_session)
        except Exception as e:
            print(f"[ERROR] Failed to load sessions: {e}")

    def _query_llm(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.deployments[self.current_model],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                messages=messages,
                timeout=30,
                stream=True
            )
            return response
        except (APIConnectionError, Timeout, RateLimitError, APIError) as e:
            print(f"[ERROR] API request failed: {e}")
            return None

    def answer_ChatGPT(self, text_input):
        if not text_input:
            return "[WARNING] Empty input"

        self.status = 'generating'
        print(f" ({self.active_session}) Human: {text_input}")

        self.sessions[self.active_session].append({"role": "user", "content": text_input})
        response = self._query_llm(self.sessions[self.active_session])

        if response is None:
            self.status = 'idle'
            return "[ERROR] Failed to get response."

        full_reply = ""
        try:
            for chunk in response:
                choices = chunk.choices
                if not choices or len(choices) == 0:
                    continue
                delta = choices[0].delta
                delta_content = getattr(delta, "content", None)
                if delta_content:
                    print(delta_content, end="", flush=True)
                    full_reply += delta_content

            print("\n")
        except Exception as e:
            print(f"[ERROR] Streaming failed: {e}")
            self.status = 'idle'
            return "[ERROR] Streaming failed."

        self.sessions[self.active_session].append({"role": "assistant", "content": full_reply})
        self._save_sessions_to_file()
        self.status = 'idle'
        return full_reply

    def respond(self, command, reply):
        cmd = command.get(0).asString()

        if cmd == 'status':
            reply.addString(self.status)

        elif cmd == 'reset':
            self.reset_active_session()
            reply.addString('Session reset.')

        elif cmd == 'quit':
            self.close()
            reply.addString('Quit command sent.')

        elif cmd == 'query':
            self.query_via_rpc = True
            text_input = " ".join(command.get(i).asString() for i in range(1, command.size())).strip()
            self.text_via_rpc = text_input
            answer = self.answer_ChatGPT(text_input)
            reply.addString(answer)
            self.query_via_rpc = False

        elif cmd == 'set_system_prompt':
            new_prompt = " ".join(command.get(i).asString() for i in range(1, command.size())).strip()
            self.system_prompt = new_prompt
            self.reset_active_session()
            reply.addString('System prompt updated.')

        elif cmd == 'create_session':
            session_id = command.get(1).asString()
            self._create_session(session_id)
            self._save_sessions_to_file()
            reply.addString(f"Session '{session_id}' created.")

        elif cmd == 'switch_session':
            session_id = command.get(1).asString()
            if session_id in self.sessions:
                self.active_session = session_id
                reply.addString(f"Switched to session '{session_id}'.")
            else:
                reply.addString(f"Session '{session_id}' not found.")

        elif cmd == 'list_sessions':
            reply.addString(", ".join(self.sessions.keys()))

        elif cmd == 'set_model':
            model_name = command.get(1).asString()
            if model_name in self.deployments:
                self.current_model = model_name
                reply.addString(f"Model set to '{model_name}'.")
            else:
                reply.addString(f"Unknown model '{model_name}'.")

        else:
            reply.addString('Unknown command.')

        return True

    def updateModule(self):
        if not self.query_via_rpc:
            bottle = self.input_port.read(False)
            if bottle is not None:
                text_input = " ".join(bottle.get(i).asString() for i in range(bottle.size())).strip()
                answer = self.answer_ChatGPT(text_input)
                bot = self.output_port.prepare()
                bot.clear()
                bot.addString(answer)
                self.output_port.write()
        return True

    def getPeriod(self):
        return self.period

    def close(self):
        self.input_port.close()
        self.output_port.close()
        self.rpc_port.close()
        return True

    def interruptModule(self):
        self.input_port.interrupt()
        self.output_port.interrupt()
        self.rpc_port.interrupt()
        return True


if __name__ == '__main__':
    yarp.Network.init()
    mod = GPT()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(sys.argv)
    mod.runModule(rf)
    yarp.Network.fini()