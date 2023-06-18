import datetime
import json
import os
import subprocess

import bs4
import requests

wolfram_api_key = None
always_authenticate = False

def gen_functions(functions_def: list) -> list:
    function_params_list = []
    for user_function in functions_def:
        try:
            function = {
                "name": user_function["name"],
                "description": "\n".join([line.strip() for line in user_function["description"].strip().split("\n")]),
                "parameters": {
                    "type": "object",
                    "properties": user_function["params"]
                },
                "requires": list(user_function["params"].keys())
            }
            function_params_list.append(function)
        except KeyError:
            print(f"函数 {user_function.get('name', '未知')} 无法识别")
    return function_params_list

def get_time(args: dict=None) -> dict:
    if args is None:
        args = {}
    return json.dumps({"time": str(datetime.datetime.now())})

def run_cmd(args: dict=None) -> dict:
    if args is None:
        args = {}
    cmd = args.get("cmd", "")
    print(f"请求执行指令：{cmd}, 你是否授权这一行为? [Y/n/用户反馈] ", end="")
    authorization = "y" if always_authenticate else input("")
    if authorization.lower() == "n":
        return json.dumps({"result": "User rejected the request"})
    elif authorization.lower() == "y" or authorization == "":
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding='gbk')
            return json.dumps(
                {
                    "result": f"成功运行了指令：{cmd} {result.stdout.strip()}"
                    if result.returncode == 0 and result.stdout is not None
                    else f"运行指令时发生了错误：{cmd} {result.stderr.strip()}"
                }
            )
        except Exception as e:
            return json.dumps({"result": str(e)})
    else:
        return json.dumps({"result": f"User rejected the request with a feedback: {authorization}"})

def wolframalpha(args: dict=None) -> dict:
    if args is None:
        args = {}
    query = args.get("query", "")
    full_results = args.get("full_results", False)
    base_url = "http://api.wolframalpha.com/v2/query" if full_results else "http://api.wolframalpha.com/v1/result"
    if query == "":
        return json.dumps({"error": "query is empty"})
    if wolfram_api_key is None:
        return json.dumps({"error": "wolfram_api_key is empty"})

    params = {
        "input": query,
        "format": "plaintext",
        "appid": wolfram_api_key
    }
    if full_results:
        params["output"] = "JSON"

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        result = response.json() if full_results else {"result": response.text}
        return json.dumps(result)
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Request failed: {e}"})

def spider(args: dict=None) -> dict:
    if args is None:
        args = {}
    url = args.get("url", "")
    print(f"尝试爬取内容: {url}")
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    text = ' '.join(soup.stripped_strings)
    return json.dumps({"result": text})

def get_absolute_path(path):
    return path if os.path.isabs(path) else os.path.abspath(path)

def write(args: dict=None) -> dict:
    if args is None:
        args = {}
    result = {'result': ""}
    try:
        path = args['path']
        content = args['content']
        encoding = args.get('encoding', 'utf-8')
        if path == "":
            path = "./"
        path = get_absolute_path(path)
        print(f"请求保存文件到：{path}, 你是否授权这一行为? [Y/n/用户反馈] ", end="")
        authorization = "y" if always_authenticate else input("")
        if authorization.lower() == "n":
            result['result'] = "User rejected the request"
            return json.dumps(result)
        elif authorization.lower() == "y" or authorization == "":
            os.makedirs(os.path.dirname(path), exist_ok=True)
            # file deepcode ignore BinaryWrite: encoding be decided by AI
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            result['result'] = f"File saved successfully at {path}"
        else:
            result['result'] = f"User rejected the request with a feedback: {authorization}"
            return json.dumps(result)
    except Exception as e:
        result['result'] = f"An error occurred while saving the file: {str(e)}"
    return json.dumps(result)

def read(args):
    result = {'success': False, 'content': None, 'error': None}
    try:
        path = args['path']
        encoding = args['encoding'] if 'encoding' in args else 'utf-8'
        print(f"请求读取文件：{path}, 你是否授权这一行为? [Y/n/用户反馈] ", end="")
        authorization = "y" if always_authenticate else input("")
        if authorization.lower() == "n":
            result['error'] = "User rejected the request"
            return json.dumps(result)
        elif authorization.lower() == "y" or authorization == "":
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            result['success'] = True
            result['content'] = content
        else:
            result['error'] = f"User rejected the request with a feedback: {authorization}"
            return json.dumps(result)
    except Exception as e:
        result['error'] = str(e)
    return json.dumps(result)

functions_def = [
    {
        "name": "get_time",
        "user_friendly_name": "获取时间",
        "description": "Get the current date time in YYYY-MM-DD HH:mm:SS.millisecond",
        "params": {},
        "function": get_time
    },
    {
        "name": "run_cmd",
        "user_friendly_name": "运行指令",
        "description": """run a Windows command and get command output
                        Your command will be be running in a safe environment.
                        For file paths that has spaces, use double quotes to wrap the path.""",
        "params": {
            "cmd": {
                "type": "string",
                "description": "The command you would like to execute"
            }
        },
        "function": run_cmd
    },
    {
        "name": "wolframalpha",
        "user_friendly_name": "Wolfram Alpha",
        "description": """to get math answers using natural language
                        If the function fails, notify the user and try solve the problem""",
        "params": {
            "query": {
                "type": "string",
                "description": "describe your math question in natural language, you MUST use english language."
            },
            "full_results": {
                "type": "boolean",
                "description": "set to true will return the answer in full, vice versa."
            }
        },
        "function": wolframalpha
    },
    {
        "name": "spider",
        "user_friendly_name": "爬虫",
        "description": "for getting text from a dedicated url",
        "params": {
            "url": {
                "type": "string",
                "description": "your dedicated url"
            }
        },
        "function": spider
    },
    {
        "name": "read",
        "user_friendly_name": "读取文件",
        "description": "read local file from a given path and encoding",
        "params": {
            "path": {
                "type": "string",
                "description": "Path to the file you would like to read"
            },
            "encoding":{
                "type": "string",
                "description": "The Encoding of the file you would like to read"
            }
        },
        "function": read
    },
    {
        "name": "write",
        "user_friendly_name": "写入文件",
        "description": "write data to local file from a given path and encoding",
        "params": {
            "path": {
                "type": "string",
                "description": "Path to the file you would like to write"
            },
            "encoding":{
                "type": "string",
                "description": "The Encoding of the file you would like to write"
            },
            "content":{
                "type": "string",
                "description": "Content you would like to write to the file"
            }
        },
        "function": write
    }
]