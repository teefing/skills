import os
import requests
import json
import sys

retryable_rate_limit_codes = {"1254290", "1255040", "1254607", "1254608"}


def is_retryable_rate_limit_text(text):
    if not text:
        return False
    lower_text = text.lower()
    if "frequency limit" in lower_text:
        return True
    for code in retryable_rate_limit_codes:
        if code in text:
            return True
    return False


class LarkBitableClient:
    def __init__(self):
        self.iris_agent_base_url = os.getenv("IRIS_AGENT_BASE_URL", "")
        if not self.iris_agent_base_url:
            self._handle_error("ENV_MISSING", "Environment variable IRIS_AGENT_BASE_URL not set.", "Please communicate with the developer to fix this issue")
        
        if self.iris_agent_base_url.endswith("/"):
            self.iris_agent_base_url = self.iris_agent_base_url[:-1]
            
        self.api_url = f"{self.iris_agent_base_url}/internal/call_tool"

    def call(self, method, args):
        payload = {
            "tool_name": f"lark_bitable_{method}",
            "toolset": "lark_bitable",
            "parameters": args,
            "internal_options":{"agent_step_id":os.getenv("IRIS_CURRENT_AGENT_STEP_ID", ""),"display_to_user":True} # 用来把工具事件展示给用户
        }
        # 禁用代理，直接连接（适用于内网 IPv6 地址）
        proxies = {
            'http': None,
            'https': None
        }
        header = {"Content-Type": "application/json", "X-JWT-Token": os.getenv("AIME_USER_CLOUD_JWT", "")}
        try:
            response = requests.post(self.api_url, headers=header, json=payload, proxies=proxies, timeout=1800)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            msg = str(e)
            details = ""
            if hasattr(e, 'response') and e.response is not None:
                # Try to parse server error message
                try:
                    # Agent server often returns raw text or specific JSON for errors.
                    # We try to read the text.
                    details = e.response.text
                except:
                    pass
            text_to_check = details if details else msg
            error_code = "RATE_LIMIT_RETRYABLE" if is_retryable_rate_limit_text(text_to_check) else "RPC_ERROR"
            self._handle_error(error_code, f"Failed to call Lark Bitable RPC: {msg}", details)

    def _handle_error(self, code, message, suggestion=""):
        error_output = {
            "error": {
                "error_code": code,
                "message": message,
                "suggestion": suggestion
            }
        }
        if code == "RATE_LIMIT_RETRYABLE":
            raise RetryableRateLimitError(error_output)
        raise LarkBitableError(error_output)

class LarkBitableError(Exception):
    def __init__(self, json_payload):
        super().__init__(json_payload)
        self.json_payload = json_payload


class RetryableRateLimitError(LarkBitableError):
    pass

def print_json(data):
    json_str = json.dumps(data, ensure_ascii=False)
    if len(json_str) > 30000:
        import uuid
        import time
        workspace_path = os.environ.get('AIME_WORKSPACE_PATH', '/tmp')
        output_dir = os.path.join(workspace_path, 'lark_bitable_large_output')
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            output_dir = '/tmp'
        file_name = f"lark_bitable_resp_{int(time.time())}_{uuid.uuid4().hex[:8]}.json"
        file_path = os.path.join(output_dir, file_name)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            summary = {"_note": f"Response too large ({len(json_str)} chars). Saved to {file_path}", "structure_summary": {}}
            
            def summarize_item(obj, depth=0):
                if depth > 2: # Limit recursion depth to top 2 levels
                     return "..."
                if isinstance(obj, list):
                    return f"list[{len(obj)}]"
                if isinstance(obj, dict):
                    # Show structure for keys, but stop if too deep
                    return {k: summarize_item(v, depth + 1) for k, v in obj.items() if k not in ["code", "msg"]}
                return type(obj).__name__

            if isinstance(data, dict):
                summary["structure_summary"] = summarize_item(data, depth=0)
            elif isinstance(data, list):
                summary["structure_summary"] = f"list[{len(data)}]"
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"NOTICE: Failed to save large response to file: {e}", file=sys.stderr)
            chunk_size = 4000
            for i in range(0, min(len(json_str), 12000), chunk_size): # Cap at 12k chars fallback
                 print(json_str[i : i + chunk_size])
    else:
        # Normal output for small responses
        chunk_size = 4000
        if len(json_str) > chunk_size:
            print("NOTICE: Output is wrapped into multiple lines to avoid truncation.", file=sys.stderr)
        for i in range(0, len(json_str), chunk_size):
            print(json_str[i : i + chunk_size])

def run_script(func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        if result is not None:
            print_json(result)
    except LarkBitableError as e:
        print_json(e.json_payload)
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
