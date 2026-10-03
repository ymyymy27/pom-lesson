from urllib.parse import urlparse
u = urlparse("http://localhost:8080/health")
print(u.hostname)
print(u.port)
print(u.path)
