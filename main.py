import os
import json
import datetime
import urllib.request


REPO = os.environ["REPO"]
ISSUE = int(os.environ["ISSUE"])
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
XAI_TOKEN = os.environ["XAI_TOKEN"]
DEFAULT_SYSTEM_MESSAGE = """
你是一个极客、技术爱好者、计算机专家、软件工程师，具备备丰富的计算机基础知识，熟练掌握当前主流编程语言各种框架的设计原则、特点、缺陷等方面的内容，同时精通前端、后端、运维、大数据、人工智能等多维度的专业知识。

您将帮助我解决任何与计算机技术、信息技术、信息安全以及数码产品相关的疑惑，提供相应的知识和解决方案。

请使用 Markdown 语法回答问题，以便于用户阅读。在回答问题时，您需要：
 1. 理解问题的本质并给予解答，
 2. 在回答问题时要有耐心，能够从多个维度分析问题。
 3. 回答问题的方式需要结构化。
 4. 尽可能详细阐述相关信息。
 5. 遵循用户语言的半角与全角标点规则。
 6. 持续学习并运用最佳文档写作实践，来提高回答的质量。
"""


def make_request(request: urllib.request.Request) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(request) as response:
            data = response.read()
            return response.status, data
    except urllib.error.HTTPError as e:
        print(f"\033[31mHTTP Error: {e}: {e.read()}\033[0m")
        raise e


def get_issue() -> dict:
    request = urllib.request.Request(
        method="GET", url=f"https://api.github.com/repos/{REPO}/issues/{ISSUE}")
    _, data = make_request(request)
    return json.loads(data)


def rename_issue(title: str) -> None:
    request = urllib.request.Request(
        method="PATCH", url=f"https://api.github.com/repos/{REPO}/issues/{ISSUE}",
        data=json.dumps({"title": title}).encode("utf-8"),
        headers={ "Content-Type": "application/json", "Authorization": f"Bearer {GITHUB_TOKEN}", },
    )
    make_request(request)


def reply_issue(comment: str) -> None:
    request = urllib.request.Request(
        method="POST", url=f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
        data=json.dumps({"body": comment}).encode("utf-8"),
        headers={ "Content-Type": "application/json", "Authorization": f"Bearer {GITHUB_TOKEN}", },
    )
    make_request(request)


def label_issue(labels: list[str]) -> None:
    request = urllib.request.Request(
        method="PATCH", url=f"https://api.github.com/repos/{REPO}/issues/{ISSUE}",
        data=json.dumps({"labels": labels}).encode("utf-8"),
        headers={ "Content-Type": "application/json", "Authorization": f"Bearer {GITHUB_TOKEN}", },
    )
    make_request(request)


def close_issue() -> None:
    request = urllib.request.Request(
        method="PATCH", url=f"https://api.github.com/repos/{REPO}/issues/{ISSUE}",
        data=json.dumps({"state": "closed"}).encode("utf-8"),
        headers={ "Content-Type": "application/json", "Authorization": f"Bearer {GITHUB_TOKEN}", },
    )
    make_request(request)


def request_ai(message: str, system_message: str = DEFAULT_SYSTEM_MESSAGE) -> str:
    payload = {
        "model": "grok-beta",
        "stream": False,
        "messages": [
            { "role": "user", "content": message },
            { "role": "system", "content": system_message },
        ]
    }
    request = urllib.request.Request(
        method="POST", url="https://api.x.ai/v1/chat/completions", 
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {XAI_TOKEN}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"
        },
    )
    _, data = make_request(request)
    return json.loads(data)["choices"][0]["message"]["content"]


def get_ai_reply(message: str, system_message: str = DEFAULT_SYSTEM_MESSAGE) -> str:
    return request_ai(message, system_message)["choices"][0]["message"]["content"]


def is_on_topic(message: str) -> bool:
    reply = request_ai(
        "请判断下面的问题是否与计算机技术、信息技术、信息安全以及数码产品相关，且符合论坛规则；如果相关请回答 YES，否则回答 NO。\n\n" + message,
        system_message="""
            你是一个技术论坛的运营人员，论坛的主要讨论主题是计算机技术、信息技术、电子数码、硬件设备、软件应用等方面的内容。
            同时，论坛禁止讨论政治、色情、暴力等内容，也不允许各种广告、推销、宣传等行为，不得包含人身攻击、侮辱或挑衅性言论，不得泄露他人个人信息，不得未经授权分享个人联系方式、地址等敏感信息。
            你需要判断用户提出的问题是否与论坛的主要讨论主题相关且符合论坛规则，如果相关则回答 YES，否则回答 NO。
            你的回答只能是 YES 或者 NO。
        """
    )
    if "YES" in reply.upper():
        return True
    return False


def generate_tags(message: str) -> list[str]:
    tags = request_ai(
        "请为下面的文本选取几个 Tag。\n\n" + message,
        system_message="""
            你是一个计算机技术杂志的编辑人员，主要任务是为投稿的文章起一个合适且方便索引的 Tag。
            合适的标题应该在 10 到 40 个字以内，可以使用中文和英文，但不要使用特殊符号，不要加空格。清正确使用各种技术名词的大小写。
            您只需要回答我你选取的 Tag 即可，不要附带任何解释说明。
            多个 Tag 请用空格隔开。
        """
    )
    tags = [i.strip() for i in tags.split(" ")]
    return tags


def generate_new_title(message: str) -> bool:
    return request_ai(
        "请为下面的文本起一个像技术博客文章的标题。\n\n" + message,
        system_message="""
            你是一个计算机技术杂志的编辑人员，主要任务是为投稿的文章起一个合适且有吸引力的标题。
            合适的标题应该在 10 到 40 个字以内，正确使用各种技术名词的大小写，不要使用特殊符号。
            您只需要回答我标题即可，不要附带任何解释说明。
            你的回答只能包含标题本身。
        """
    )


def write_article(title: str, tags: list[str], content: str):
    yaml_tags = ", ".join([f'"{tag}"' for tag in tags])
    markdown_lines = [
        "---",
        f'title: "{title}"',
        f'date: {datetime.datetime.now().isoformat()}',
        f"tags: [{yaml_tags}]",
        "---",
        content,
    ]
    with open(f"source/_posts/issue-{ISSUE}.md", "w+", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))


def main() -> None:
    print(f"Getting issue for: {REPO} issue #{ISSUE}")
    issue = get_issue()
    issue_title = issue["title"] or "无标题"
    issue_body = issue["body"] or ""
    print(f"Issue title: {issue_title}")
    print(f"Issue body: ------------------------------")
    print(f"{issue_body}")
    print(f"------------------------------------------")
    on_topic = is_on_topic(issue_title + "\n\n" + issue_body)
    print(f"AI assessment of issue on-topic: {on_topic}")
    if not on_topic:
        print("Issue is off-topic. Closing issue.")
        label_issue(["off-topic"])
        close_issue()
        return
    print("Issue is on-topic. Proceeding with AI reply.")
    ai_reply = request_ai("问题标题：" + issue_title + "\n\n问题内容：\n\n" + issue_body)
    print(f"AI Reply ------------------------------")
    print(f"{ai_reply}")
    print(f"------------------------------------------")
    print("Replying to issue with AI reply.")
    reply_issue(ai_reply)
    print("Renaming issue with AI title.")
    ai_title = generate_new_title(ai_reply)
    print(f"AI Title: {ai_title}")
    rename_issue(ai_title)
    ai_tags = generate_tags(ai_reply)
    print(f"AI Tags: {ai_tags}")
    print("Setting issue label to 'answered' and closing issue.")
    label_issue(["answered"])
    close_issue()
    print("Writing article to disk.")
    write_article(ai_title, ai_tags, ai_reply)


if __name__ == '__main__':
    main()
