import argparse

def add_task(tasks, title):
    title = title.strip()
    if not title:
        raise ValueError("任务名称不能为空")
    tasks.append({"id": max((t["id"] for t in tasks), default=0) + 1,
                  "title": title, "done": False})

def complete_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            return
    raise ValueError("任务编号不存在")

def show(tasks):
    for task in tasks:
        print(f"{task['id']} [{'完成' if task['done'] else '待办'}] {task['title']}")
    if not tasks:
        print("暂无任务")

def main():
    parser = argparse.ArgumentParser(description="任务只保留在本次运行的内存中")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    tasks = []
    if args.demo:
        add_task(tasks, "阅读课程说明")
        add_task(tasks, "完成第一课")
        complete_task(tasks, 1)
        show(tasks)
        return
    while True:
        command = input("输入 add/list/done/quit：").strip()
        try:
            if command == "add":
                add_task(tasks, input("任务名称："))
            elif command == "list":
                show(tasks)
            elif command == "done":
                complete_task(tasks, int(input("任务编号：")))
            elif command == "quit":
                break
            else:
                print("未知命令")
        except ValueError as error:
            print(f"输入错误：{error}")

if __name__ == "__main__":
    main()
