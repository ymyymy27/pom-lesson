# 第4课：Mock 与测试隔离

## 1. 为什么要 Mock？

### 一句话解释

**Mock = 用假对象替换外部依赖** —— 单元测试只测「你的逻辑」，不测数据库、网络、第三方 API。

### 测试隔离原则

```
┌─────────────────────────────────────┐
│  被测单元（UserService.create）      │
│         ↓ 调用                      │
│  外部依赖 → Mock 掉                  │
│  • 数据库 UserRepository             │
│  • 邮件服务 EmailSender              │
│  • HTTP 客户端 requests              │
└─────────────────────────────────────┘
```

**Mock 什么：** 慢、不稳定、有副作用的外部系统  
**不 Mock 什么：** 被测对象内部的纯函数逻辑

---

## 2. unittest.mock 基础

```python
from unittest.mock import Mock, MagicMock, patch

def test_send_welcome_email():
    mock_sender = Mock()
    service = UserService(email_sender=mock_sender)

    service.create(name="Alice", email="a@b.com")

    mock_sender.send.assert_called_once()
    args = mock_sender.send.call_args
    assert args[0][0] == "a@b.com"  # 收件人
    assert "Alice" in args[0][1]    # 正文
```

### Mock 常用断言

```python
mock_obj.method.assert_called()
mock_obj.method.assert_called_once()
mock_obj.method.assert_called_with("arg1", keyword="val")
mock_obj.method.assert_not_called()
assert mock_obj.method.call_count == 3
```

### return_value 与 side_effect

```python
mock_repo = Mock()
mock_repo.find_by_id.return_value = User(id=1, name="Alice")

mock_repo.find_by_id.side_effect = UserNotFoundError()
mock_repo.find_by_id.side_effect = [user1, user2, None]  # 连续调用
```

---

## 3. patch 装饰器与上下文

```python
@patch("user_service.send_email")
def test_create_triggers_email(mock_send):
    mock_send.return_value = True
    UserService().create("Bob", "bob@test.com")
    mock_send.assert_called_once()

@patch("requests.get")
def test_fetch_weather(mock_get):
    mock_get.return_value.json.return_value = {"temp": 25}
    result = get_weather("Beijing")
    assert result["temp"] == 25
```

**patch 路径规则：** 在**使用处** patch，而非定义处

```python
# user_service.py
from external import fetch_data

# test_user_service.py
@patch("user_service.fetch_data")  # ✅ 正确
# @patch("external.fetch_data")  # ❌ 若已在 user_service 中 import
```

---

## 4. pytest monkeypatch

pytest 内置 fixture，适合改环境变量、属性、路径：

```python
def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret")
    assert get_api_key() == "test-secret"

def test_disable_cache(monkeypatch):
    monkeypatch.setattr("app.settings.CACHE_ENABLED", False)
    ...

def test_chdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert Path.cwd() == tmp_path
```

测试结束后 **自动恢复**，无需手动 teardown。

---

## 5. pytest-mock（mocker fixture）

```bash
pip install pytest-mock
```

```python
def test_with_mocker(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"ok": True}

    assert fetch_status() == {"ok": True}
    mock_get.assert_called_once_with("https://api.example.com/status")
```

与 `unittest.mock.patch` 等价，写法更简洁，自动清理。

---

## 6. 捕获副作用：capsys / caplog

```python
import logging

def test_logs_error(caplog):
    caplog.set_level(logging.ERROR)
    process_invalid_input(None)
    assert "invalid input" in caplog.text

def test_cli_output(capsys):
    main(["--version"])
    assert "1.0.0" in capsys.readouterr().out
```

---

## 7. 临时文件与目录

```python
def test_export_csv(tmp_path):
    output = tmp_path / "users.csv"
    export_users(output, users=[User("Alice")])
    content = output.read_text()
    assert "Alice" in content
```

---

## 8. Mock 反模式

| 反模式 | 问题 | 改进 |
|--------|------|------|
| Mock 被测对象本身 | 测的是 Mock 不是代码 | 只 Mock 依赖 |
| 过度 Mock | 测试与实现强耦合 | 测行为而非内部调用 |
| 不断言 Mock 调用 | 假绿测试 | assert_called / 返回值 |
| patch 路径错误 | Mock 未生效 | 在使用模块 patch |

```python
# ❌ 没断言，测试无意义
def test_create(mock_repo):
    UserService(mock_repo).create("A", "a@b.com")

# ✅
def test_create(mock_repo):
    user = UserService(mock_repo).create("A", "a@b.com")
    mock_repo.save.assert_called_once()
    assert user.name == "A"
```

---

## 9. 练习

1. 为 `OrderService` 编写测试：Mock 库存服务，验证「库存不足时抛异常」
2. 用 `monkeypatch.setenv` 测试读取配置
3. 用 `mocker.patch` 模拟 HTTP 超时

<details>
<summary>库存不足测试参考</summary>

```python
def test_insufficient_stock(mocker):
    mock_inventory = mocker.Mock()
    mock_inventory.check.return_value = False

    service = OrderService(inventory=mock_inventory)
    with pytest.raises(InsufficientStockError):
        service.place_order(product_id=1, qty=10)

    mock_inventory.check.assert_called_once_with(1, 10)
```

</details>

---

## 10. 自检清单

- [ ] 能区分该 Mock 什么、不该 Mock 什么
- [ ] 会用 `Mock`、`patch`、`monkeypatch`
- [ ] 理解 patch 路径要在「使用模块」
- [ ] 会用 `capsys` / `caplog` 验证输出
- [ ] 每个 Mock 测试都有有意义的断言

👉 下一课：[05_conftest_and_plugins.md](05_conftest_and_plugins.md)
