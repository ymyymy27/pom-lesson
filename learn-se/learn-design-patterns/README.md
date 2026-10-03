# 设计模式

GoF 23 种经典设计模式的系统学习，以 Python 为例，强调「何时用、何时不用」。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_pattern_overview.md` | 模式分类、选型决策树 + 深入篇：底层逻辑 |
| 第1课 | `01_creational_patterns.md` | 创建型 5 种 + 深入篇：机关与权衡 |
| 第2课 | `02_structural_patterns.md` | 结构型 7 种 + 深入篇：机关与双胞胎 |
| 第3课 | `03_behavioral_patterns.md` | 行为型 11 种 + 深入篇：机关与对比总表 |
| 第4课 | `04_patterns_in_practice.md` | 模式组合、反模式 + 深化篇：从模式到架构 |
| 复习 | `05_review_creational_structural.md` | 23 模式全景 + 九组亲戚 + 20 道鉴别题 |

## 代码练习

`practice/` 目录包含可运行的 Python 示例，每课对应子目录。

```bash
cd practice
python -m creational.factory_demo
python -m creational.singleton_demo
python -m structural.adapter_demo
python -m behavioral.strategy_demo
python -m behavioral.state_demo
```

完整列表见 `practice/README.md`。

## 学习方式

- 先读 `00_pattern_overview.md` 建立全局地图
- 每学一个模式：看动机 → 看结构图 → 跑示例 → 想自己项目里的场景
- 学完 01~03 后回看各文件末尾的「深入篇」，完成第二次理解
- 最后用 `05_review_creational_structural.md` 的鉴别题做自测
- 避免「模式滥用」：第4课专门讲反模式与过度设计
