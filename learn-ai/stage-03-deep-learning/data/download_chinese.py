import urllib.request
import ssl
import os
import json

data_dir = "e:/code/Projects/learn/learn-ai/stage-03-deep-learning/data"
os.makedirs(data_dir, exist_ok=True)

# 创建不验证 SSL 的上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 尝试多个镜像
tang_urls = [
    "https://ghproxy.com/https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master/poetry/tang.0.json",
    "https://raw.gitmirror.com/chinese-poetry/chinese-poetry/master/poetry/tang.0.json",
]
tang_path = os.path.join(data_dir, "tang.json")
for url in tang_urls:
    try:
        print(f"尝试唐诗: {url[:60]}...")
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, context=ssl_context, timeout=30)
        content = response.read()
        with open(tang_path, 'wb') as f:
            f.write(content)
        print(f"成功！文件大小: {len(content):,} bytes")
        break
    except Exception as e:
        print(f"  失败: {e}")

# 宋词
ci_urls = [
    "https://ghproxy.com/https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master/poetry/ci.song.0.json",
    "https://raw.gitmirror.com/chinese-poetry/chinese-poetry/master/poetry/ci.song.0.json",
]
ci_path = os.path.join(data_dir, "ci.json")
for url in ci_urls:
    try:
        print(f"尝试宋词: {url[:60]}...")
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, context=ssl_context, timeout=30)
        content = response.read()
        with open(ci_path, 'wb') as f:
            f.write(content)
        print(f"成功！文件大小: {len(content):,} bytes")
        break
    except Exception as e:
        print(f"  失败: {e}")
