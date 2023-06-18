# OpenAI API 函数调用 DEMO

该项目是一个 Python 程序，在与 OpenAI 的 GPT 模型对话时提供插件支持。

## 功能

- 支持设置代理服务器
- 往消息列表中添加条目
- 与用户进行对话并调用插件函数提供额外功能
- 加载配置文件
- 其他辅助函数

## 用法

1. 在 config.json 中配置项目所需的参数，例如 API 密钥、模型等。

2. 运行 main.py 文件。程序会读取配置文件，并根据配置的参数和提示，生成 OpenAI API 的请求并打印出回应。

## 插件功能

该项目提供了以下插件功能：

1. 获取当前时间
2. 运行系统指令
3. 调用 Wolfram Alpha 的数学计算接口
4. 爬取指定网页的文本内容
5. 读取本地文件内容
6. 将数据写入本地文件中

## 安装

克隆项目到本地：

```bash
git clone https://github.com/PeterBilly/OpenAI-Functions.git
```

进入项目目录：

```bash
cd OpenAI-Functions
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 配置文件

使用 config.json 文件进行配置，模板见 [config_template](config_template.json)

## 许可证

该项目使用 AGPL v3 开源许可证。详情请参阅 [LICENCE](LICENCE) 文件。
