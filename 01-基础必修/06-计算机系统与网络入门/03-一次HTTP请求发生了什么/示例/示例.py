from urllib.parse import urlparse
url = urlparse("http://127.0.0.1:8000/tasks")
print(url.hostname, url.port, url.path)
