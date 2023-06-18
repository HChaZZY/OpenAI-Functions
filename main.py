import json
import os
import sys

import openai
import socks

import function_generator as fun

SUPPORTED_MODELS = ["gpt-3.5-turbo-0613", "gpt-4-0613"]

def set_proxy(HTTP_PROXY = None, SOCKS_PROXY = None):
    """
    设置代理服务器

    Args:
        HTTP_PROXY: HTTP代理服务器地址和端口号
        SOCKS_PROXY: SOCKS代理服务器地址和端口号
    """
    os.environ["http_proxy"] = f"http://{HTTP_PROXY[0]}:{HTTP_PROXY[1]}"
    os.environ["https_proxy"] = f"http://{HTTP_PROXY[0]}:{HTTP_PROXY[1]}"
    socks.set_default_proxy(socks.SOCKS5, SOCKS_PROXY[0], SOCKS_PROXY[1])

def add_msg(messages, role, msg, name = None):
    """
    往消息列表中添加条目

    Args:
        messages: 消息列表
        role: 发送者角色 (user/assistant/system/function)
        msg: 消息内容
        name: 插件名称
    """
    if not name:
        messages.append({"role": role, "content": msg})
    else:
        messages.append({"role": role, "name": name, "content": msg})

def chat(messages, api_key, model, functions, base):
    """
    发起对话

    Args:
        messages: 消息列表
        api_key: OpenAI API密钥
        model: 使用的模型
        functions: 定义的插件函数
        base: API基础路径
    """
    while True:
        openai.api_key = api_key
        openai.api_base = base
        try:
            function_call = {
                "name": "",
                "arguments": "",
            }
            use_function = False
            answer = ""
            response = openai.ChatCompletion.create(
                model = model,
                messages = messages,
                functions = functions,
                function_call = "auto",
                temperature = 1,
                stream = True
            )
            for chunk in response:
                message = chunk["choices"][0]
                if not message.get("finish_reason", None):
                    if message["delta"].get("function_call"):
                        use_function = True
                        function_call["name"] += message["delta"]["function_call"].get("name", "")
                        function_call["arguments"] += message["delta"]["function_call"].get("arguments", "")
                    if not use_function:
                        answer += message["delta"].get("content", "")
                        print(message["delta"].get("content", ""), end="")
                elif not use_function:
                    return answer
            try:
                function_call["arguments"] = json.loads(function_call["arguments"])
            except json.JSONDecodeError:
                function_call["arguments"] = {}
            if use_function:
                if function_call["name"] != "exit":
                    print(f"\n正在调用插件：{function_call['name']}")
                function_response = eval(f"fun.{function_call['name']}({function_call['arguments']})")
                add_msg(messages, "function", function_response, function_call["name"])
        except Exception as e:
            print(f"调用OpenAI API时发生了错误: {str(e)}")
            break

def load_config(config_file):
    """
    加载配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        config: 配置文件的字典
    """
    try:
        with open(config_file, 'r', encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"无法加载配置文件 {config_file}: {str(e)}")
        config = {}
    return config

def main():
    config = load_config("config.json")
    if config.get("PROXY", False):
        HTTP_PROXY = config.get("HTTP_PROXY", None)
        SOCKS_PROXY = config.get("SOCKS_PROXY", None)
        if HTTP_PROXY is not None and SOCKS_PROXY is not None:
            set_proxy(HTTP_PROXY, SOCKS_PROXY)
        else:
            print("HTTP_PROXY 或 SOCKS_PROXY 在 config.json 中为空, 将不会设置代理")

    api_key = config.get("api_key", None)
    model = config.get("model", "gpt-3.5-turbo-0613")
    base = config.get("base", "https://api.openai.com/v1")
    system_prompt = config.get("system_prompt", None)
    fun.wolfram_api_key = config.get("wolfram_api_key", None)
    fun.always_authenticate = config.get("always_authenticate", False)

    messages = []
    functions = fun.gen_functions(fun.functions_def)

    if model not in SUPPORTED_MODELS:
        print(f"你所使用的模型: {model} 当前无法使用函数功能 \
                \n请使用以下模型中的一个: {SUPPORTED_MODELS}")
        sys.exit(1)

    if not api_key:
        api_key = input("请输入你的api key: ")

    if not api_key.startswith("sk-"):
        print("API key 无效, 正在退出...")
        sys.exit(1)

    if system_prompt is not None:
        add_msg(messages, "system", system_prompt)

    if fun.wolfram_api_key is None:
        print("wolfram_api_key 并未在配置文件中给出, Wolfram Alpha将不可用.")

    if fun.always_authenticate:
        print("**警告**: always_authenticate 已启用, 任何AI尝试执行的指令将不会征得你的同意")
        print("你依然想要开启 always_authenticate 吗? [y/N] ", end="")
        if input().lower() != "y":
            fun.always_authenticate = False
            print("always_authenticate 已关闭.")
    while True:
        prompt = input("\n>")
        if prompt.startswith("/"):
            if prompt == "/clear":
                messages.clear()
                os.system("cls")
                print("消息已被清空")
            else:
                print(f"无法识别命令: {prompt}.")
            continue
        add_msg(messages, "user", prompt)
        response = chat(messages, api_key, model, functions, base)
        add_msg(messages, "assistant", response)

if __name__ == "__main__":
    main()