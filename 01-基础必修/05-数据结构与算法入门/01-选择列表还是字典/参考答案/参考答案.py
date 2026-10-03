courses = [{"id": 10, "name": "数学"}, {"id": 20, "name": "程序设计"}]
by_id = {}
for course in courses:
    by_id[course["id"]] = course
print(by_id[20]["name"])
print(by_id.get(30))
