import argparse
import csv
from pathlib import Path

def summarize(path):
    groups={}
    with Path(path).open(encoding="utf-8-sig",newline="") as source:
        reader=csv.DictReader(source)
        if reader.fieldnames != ["课程","学习分钟","完成"]:
            raise ValueError("CSV列必须为：课程、学习分钟、完成")
        for number,row in enumerate(reader,2):
            try:
                minutes=int(row["学习分钟"])
                done=int(row["完成"])
            except (ValueError,TypeError) as error:
                raise ValueError(f"第{number}行数字无效") from error
            title=row["课程"].strip()
            if not title or minutes<0 or done not in (0,1):
                raise ValueError(f"第{number}行内容无效")
            group=groups.setdefault(title,{"count":0,"minutes":0,"done":0})
            group["count"]+=1;group["minutes"]+=minutes;group["done"]+=done
    return groups

def report(groups):
    lines=["# 校园学习记录分析","","数据为教学合成样例，不能推断真实学生表现。","","| 课程 | 记录数 | 总分钟 | 完成率 |","|---|---:|---:|---:|"]
    for name,item in sorted(groups.items()):
        lines.append(f"| {name} | {item['count']} | {item['minutes']} | {item['done']/item['count']:.1%} |")
    if not groups:lines.append("没有可分析的记录。")
    return "\n".join(lines)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default=str(Path(__file__).with_name("学习记录.csv")))
    parser.add_argument("--output")
    args=parser.parse_args()
    try:
        result=report(summarize(args.input))
        if args.output:Path(args.output).write_text(result,encoding="utf-8")
        else:print(result)
    except (ValueError,OSError) as error:parser.exit(1,f"分析失败：{error}\n")
