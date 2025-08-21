"""
BSD 2-Clause License

Copyright (c) 2025, Social Cognition in Human-Robot Interaction,
                    Istituto Italiano di Tecnologia, Genova


All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import yarp
import sys
import json
import os
import re
from openai import AzureOpenAI
from openai import APIConnectionError, RateLimitError, Timeout, APIError
from pyicub.core.logger import YarpLogger


class GPT(yarp.RFModule):

    def configure(self, rf):
        self.DEFAULT_SESSION = "default"

        self.logs = YarpLogger.getLogger()
        self.logs.info("[GPT] Starting configuration...")

        self.period = 0.1

        #self.sessions_file = "sessions.json"
        
        self.sessions_folder = rf.check("sessions_folder", yarp.Value("")).asString()
        if not self.sessions_folder:
            self.logs.error("[GPT] Missing sessions_folder path")
            return False
        if not (os.path.isdir(self.sessions_folder)):
            os.makedirs(self.sessions_folder)

        self.total_tokens_used = 0

        self._setup_ports()

        self.config_path = rf.check("config", yarp.Value("")).asString()
        if not self.config_path:
            self.logs.error("[GPT] Missing config file path")
            return False

        if not self._load_config():
            return False

        self.prompt_path = rf.check("prompt_file", yarp.Value("")).asString()
        self._load_system_prompt()

        try:
            self.client = AzureOpenAI(
                azure_endpoint=self.config['endpoint'],
                api_key=self.config["AZURE_API_KEY"],
                api_version=self.config['api_version']
            )
        except Exception as e:
            self.logs.error(f"[GPT] AzureOpenAI init failed: {e}")
            return False

        self.sessions = {}
        self.token_usage = {}

        self.active_session = self.DEFAULT_SESSION

        self._create_session(self.active_session)
        if not (self.active_session == self.DEFAULT_SESSION):
            self.save_active_session_to_file()

        #self._load_sessions_from_file()

        self.status = 'idle'
        self.query_via_rpc = False
        self.text_via_rpc = ""

        # make the first API call here is necessary to establish the connection
        self._model_warmup()

        self.logs.info("[GPT] Configuration complete.")
        return True

    def _model_warmup(self):
        warmup_system_prompt = "You are an assistant"
        messages = [{"role": "system", "content": warmup_system_prompt}, {"role": "user", "content": "Hi"}]
        self._query_llm(messages)

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
            self.logs.error(f"[GPT] Failed to load config: {e}")
            return False

    def _load_system_prompt(self):
        if self.prompt_path and os.path.isfile(self.prompt_path):
            try:
                with open(self.prompt_path, 'r') as f:
                    self.system_prompt = f.read().strip()
            except Exception as e:
                self.logs.warning(f"[GPT] Failed to read prompt file: {e}")
                self.system_prompt = "You are a helpful assistant."
        else:
            self.system_prompt = self.config.get('system_prompt', "You are a helpful assistant.")
        self.logs.info(f"[GPT] System prompt: {self.system_prompt}")

    def _create_session(self, session_id):
        self.sessions[session_id] = [{"role": "system", "content": self.system_prompt}]
        self.token_usage[session_id] = 0

    def _reset_session(self, session_id):
        self.sessions[session_id] = [{"role": "system", "content": self.system_prompt}]
        self.token_usage[session_id] = 0

    def reset_active_session(self):
        self._reset_session(self.active_session)


    def save_session_to_file(self, session_id):
        try:
            filename = f"{self.session_id}.json"
            filepath = os.path.join(self.sessions_folder, filename)
            data = {
                "session": self.sessions[session_id], 
                "token_usage": self.token_usage[session_id]
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.logs.error(f"[GPT] Failed to save session {session_id=}: {e}")

    def save_active_session_to_file(self):
        return self.save_session_to_file(self.active_session)
        


    # def _save_sessions_to_file(self):
    #     try:
    #         data = {"sessions": self.sessions, "token_usage": self.token_usage}
    #         with open(self.sessions_file, 'w') as f:
    #             json.dump(data, f, indent=2)
    #     except Exception as e:
    #         self.logs.error(f"[GPT] Failed to save sessions: {e}")

    # def _load_sessions_from_file(self):
    #     if not os.path.isfile(self.sessions_file):
    #         return
    #     try:
    #         with open(self.sessions_file, 'r') as f:
    #             data = json.load(f)
    #             self.sessions = data.get("sessions", {})
    #             self.token_usage = data.get("token_usage", {})
    #         if self.active_session not in self.sessions:
    #             self._create_session(self.active_session)
    #     except Exception as e:
    #         self.logs.warning(f"[GPT] Failed to load sessions file: {e}")


    def _markdown_to_text(self, markdown: str) -> str:
        """
        Convert Markdown text to plain text by stripping common Markdown syntax.
        """

        text = markdown

        # # Remove code blocks (```...```)
        # text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # # Remove inline code (`...`)
        # text = re.sub(r"`([^`]*)`", r"\1", text)

        # # Remove images ![alt](url)
        # text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

        # # Replace links [text](url) with just text
        # text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        # Remove emphasis **bold**, *italic*
        text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

        # # Remove headers #### Header → Header
        # text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # # Remove blockquotes
        # text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)

        # Remove unordered list markers (-, *, +)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

        # Remove ordered list markers (1., 2., etc.)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Remove horizontal rules (---, ***, etc.)
        text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)

        # Collapse multiple newlines
        text = re.sub(r"\n{2,}", "\n\n", text)

        return text.strip()


    def _query_llm(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.deployments[self.current_model],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                messages=messages,
                timeout=30,
                stream=False
            )
            return response
        except (APIConnectionError, Timeout, RateLimitError, APIError) as e:
            self.logs.error(f"[GPT] API request failed: {e}")
            return None

    def answer_ChatGPT(self, text_input):
        if not text_input:
            return "[WARNING] Empty input"

        self.status = 'generating'
        self.logs.info(f"[GPT:{self.active_session}] User: {text_input}")
        self.sessions[self.active_session].append({"role": "user", "content": text_input})
        response = self._query_llm(self.sessions[self.active_session])

        if response is None:
            self.status = 'idle'
            return "[ERROR] Failed to get response."

        raw_reply = response.choices[0].message.content.strip()

        # Replace all whitespace characters (like \n, \t, etc.) with a single space
        full_reply = re.sub(r'\s+', ' ', raw_reply)
        full_reply = self._markdown_to_text(full_reply)
        full_reply = full_reply.replace('"', "") # speech has a bug, it does not work with hi" for instance.
        print(full_reply)

        out_bottle = self.output_port.prepare()
        out_bottle.clear()
        out_bottle.addString(full_reply)
        self.output_port.write()

        self.sessions[self.active_session].append({"role": "assistant", "content": full_reply})
        
        if not (self.active_session == self.DEFAULT_SESSION):
            self.save_active_session_to_file()
            #self._save_sessions_to_file()

        self.status = 'idle'
        return full_reply

    def _set_system_prompt_from_file(self, abs_filepath):
        try:
            if not os.path.isabs(abs_filepath):
                return "[ERROR] filepath is not absolute!"
            
            sys_prompt = None
            with open(abs_filepath, 'r') as f:
                sys_prompt = f.read().strip()
            return self._set_system_prompt(sys_prompt)
        except Exception as e:
            return f"[ERROR] Failed to load system prompt from {abs_filepath} file: {e}"
        
    def _set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset_active_session()
        return 'System prompt updated.'

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
            res = self._set_system_prompt(new_prompt)
            reply.addString(res)
        elif cmd == "set_system_prompt_from_file":
            abs_filepath = command.get(1).asString()
            res = self._set_system_prompt_from_file(abs_filepath)
            reply.addString(res)
        elif cmd == 'create_session':
            session_id = command.get(1).asString()
            self._create_session(session_id)
            self.save_session_to_file(session_id)
            reply.addString(f"Session '{session_id}' created.")
        elif cmd == 'switch_session':
            session_id = command.get(1).asString()
            if session_id in self.sessions:
                self.active_session = session_id
                reply.addString(f"Switched to session '{session_id}'.")
            else:
                reply.addString(f"[ERROR] Session '{session_id}' not found.")
        elif cmd == 'list_sessions':
            reply.addString(", ".join(self.sessions.keys()))
        elif cmd == 'set_model':
            model_name = command.get(1).asString()
            if model_name in self.deployments:
                self.current_model = model_name
                reply.addString(f"Model set to '{model_name}'.")
            else:
                reply.addString(f"[ERROR] Unknown model '{model_name}'.")
        else:
            reply.addString(f"[ERROR] Unknown command '{cmd}'. Type 'help'.")

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
        self.logs.info("[GPT] Closing ports...")
        self.input_port.close()
        self.output_port.close()
        self.rpc_port.close()
        return True

    def interruptModule(self):
        self.logs.info("[GPT] Interrupting module...")
        self.input_port.interrupt()
        self.output_port.interrupt()
        self.rpc_port.interrupt()
        return True


if __name__ == '__main__':
    yarp.Network.init()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(sys.argv)
    mod = GPT()
    mod.runModule(rf)
    yarp.Network.fini()
