from __future__ import annotations
import os
import ssl
import socket
import time
import json
import re
from typing import Iterable, Optional, Dict, Any, List
import requests


class TwitchClient:
    """
    Minimal Helix client for Clips + a simple Twitch IRC listener.

    Authentication:
      - For *creating clips*: you MUST use a *User Access Token* with the `clips:edit` scope.
        Docs: https://dev.twitch.tv/docs/api/clips/  (see "Creating Clips")
      - For *getting clips*: any valid OAuth token works (app or user).
      - For IRC chat read: a *User Access Token* with `user:read:chat` (to read).
        Docs: https://dev.twitch.tv/docs/chat/irc/ (see "Authenticating ...", "Receiving Messages")
    """

    def __init__(self, client_id: str, access_token: str, base_url: str = "https://api.twitch.tv/helix"):
        self.client_id = client_id
        self.access_token = access_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # -----------------------
    # IRC (CHAT) — READ MESSAGES
    # -----------------------
    def listen_to_channel_messages(
        self,
        channel_login: str,
        bot_login: str,
        request_tags_and_membership: bool = True,
        ssl_port: int = 6697,
        host: str = "irc.chat.twitch.tv",
    ) -> None:
        """
        Connects to Twitch IRC and prints formatted chat messages.
        """
        self._listen_to_twitch_chat(
            channel_login=channel_login,
            bot_login=bot_login,
            request_tags_and_membership=request_tags_and_membership,
            ssl_port=ssl_port,
            host=host
        )

    def _listen_to_twitch_chat(
        self,
        channel_login: str,
        bot_login: str,
        request_tags_and_membership: bool = True,
        ssl_port: int = 6697,
        host: str = "irc.chat.twitch.tv",
    ) -> None:
        """
        Internal method to connect to Twitch IRC and handle chat messages.
        """
        import ssl
        import socket
        import re
        from datetime import datetime

        # Build TLS socket
        context = ssl.create_default_context()
        with socket.create_connection((host, ssl_port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                def send(line: str) -> None:
                    ssock.sendall((line + "\r\n").encode("utf-8"))

                # Request capabilities (optional but helpful for tags like display-name, message id, etc.)
                if request_tags_and_membership:
                    send("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")

                # Authenticate
                if len(self.access_token) < 20:
                    print("[ERROR] Token seems too short - might be invalid")
                if self.access_token == "your_user_or_app_token":
                    print("[ERROR] Using placeholder token - need real credentials")
                
                send(f"PASS oauth:{self.access_token}")
                send(f"NICK {bot_login}")

                # Join channel
                send(f"JOIN #{channel_login}")
                buffer = b""
                
                # Simple loop: print PRIVMSG; reply to PING.
                while True:
                    data = ssock.recv(4096)
                    if not data:
                        print("[Twitch IRC] Connection closed by server.")
                        break
                    buffer += data

                    # Split on CRLF per spec
                    while b"\r\n" in buffer:
                        line, buffer = buffer.split(b"\r\n", 1)
                        raw = line.decode("utf-8", errors="ignore")

                        # Check for authentication errors
                        if "NOTICE" in raw and "Login unsuccessful" in raw:
                            print(f"[ERROR] Authentication failed - Login unsuccessful: {raw}")
                        elif "NOTICE" in raw and "authentication failed" in raw.lower():
                            print(f"[ERROR] Authentication error: {raw}")
                            break
                        elif "ERROR" in raw:
                            print(f"[ERROR] IRC Error: {raw}")
                            break

                        # Keepalive
                        if raw.startswith("PING"):
                            # Echo the payload back after PONG
                            payload = raw.split("PING", 1)[1].strip()
                            send(f"PONG{payload and ' ' + payload}")
                            continue

                        # Handle PRIVMSG with enhanced formatting
                        if " PRIVMSG " in raw:
                            self._format_and_print_message(raw)

    def _format_and_print_message(self, raw_message: str) -> None:
        """
        Parse and format a PRIVMSG in simple format: Time, Username, Message
        """
        import re
        from datetime import datetime
        
        try:
            # Extract message text (after " :")
            msg_match = re.search(r"PRIVMSG\s+#\S+\s+:(.*)", raw_message)
            message_text = msg_match.group(1) if msg_match else ""

            # Parse tags if present
            tags = {}
            tags_match = re.match(r"^@([^ ]+)\s", raw_message)
            if tags_match:
                tags_str = tags_match.group(1)
                tags = dict(
                    kv.split("=", 1) if "=" in kv else (kv, "")
                    for kv in tags_str.split(";")
                )

            # Extract user info
            display_name = tags.get("display-name", "")
            login = tags.get("login", "")
            
            # Extract timestamp
            timestamp = tags.get("tmi-sent-ts", "")
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(int(timestamp) / 1000)
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = datetime.now().strftime("%H:%M:%S")
            else:
                time_str = datetime.now().strftime("%H:%M:%S")

            # Get username (display name or login)
            username = display_name or login or "unknown"
            
            # Simple format: Time, Username, Message
            print(f"Time: {time_str}\nUsername: {username}\nMessage: {message_text}\n")
            
        except Exception as e:
            print(f"[ERROR] Message parsing failed: {e}")

    # -----------------------
    # Helpers
    # -----------------------
    @staticmethod
    def _raise_for_status(r: requests.Response) -> None:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            # Make errors easier to debug
            detail = None
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise requests.HTTPError(f"{e} | Detail: {detail}") from None
