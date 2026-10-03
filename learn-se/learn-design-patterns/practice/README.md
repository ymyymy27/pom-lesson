# 设计模式代码练习

可运行的 Python 示例，配合 `learn-design-patterns/` 课程使用。

## 运行方式

在 `practice/` 目录下：

```bash
# 创建型
python -m creational.factory_demo
python -m creational.abstract_factory_demo
python -m creational.singleton_demo
python -m creational.builder_demo
python -m creational.prototype_demo

# 结构型
python -m structural.decorator_demo
python -m structural.adapter_demo
python -m structural.bridge_demo
python -m structural.composite_demo
python -m structural.facade_demo
python -m structural.flyweight_demo
python -m structural.proxy_demo
python -m structural.skeleton_review

# 行为型
python -m behavioral.strategy_demo
python -m behavioral.observer_demo
python -m behavioral.command_demo
python -m behavioral.state_demo
python -m behavioral.chain_demo
python -m behavioral.template_demo
python -m behavioral.iterator_demo
python -m behavioral.mediator_demo
python -m behavioral.memento_demo
python -m behavioral.visitor_demo
python -m behavioral.interpreter_demo
```

## 目录与课程对应

| 目录 | 模式 | 对应课程 |
|------|------|---------|
| `creational/` | 工厂、抽象工厂、单例、建造者、原型 | 第1课 |
| `structural/` | 装饰器、适配器、桥接、组合、外观、享元、代理 | 第2课 |
| `behavioral/` | 策略、观察者、命令、状态、责任链、模板方法、迭代器、中介者、备忘录、访问者、解释器 | 第3课 |

## 学习建议

1. 先读课程文档中的概念和 UML
2. 运行示例，观察输出
3. 修改示例：加一个新产品类型、新通知渠道、新任务状态
4. 在自己项目中找对应场景
