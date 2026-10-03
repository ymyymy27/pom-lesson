"""迭代器模式示例：文档分块懒加载遍历

迭代器把"怎么遍历"从集合内部抽出来，调用方不需要知道数据是
内存列表、数据库游标还是网络流——统一 for 循环搞定。

Python 里迭代器协议是语言内置的（__iter__ / __next__），
生成器（yield）就是迭代器的语法糖。
"""


class DocumentChunk:
    def __init__(self, index: int, text: str):
        self.index = index
        self.text = text


class ChunkIterator:
    """懒加载迭代器：每次 next() 才"读"一块，不一次性载入内存"""

    def __init__(self, total_chunks: int):
        self._total = total_chunks
        self._current = 0                       # 机关：记住"遍历到哪了"

    def __iter__(self):
        return self                             # for 循环第一步：拿迭代器

    def __next__(self):
        if self._current >= self._total:
            raise StopIteration                 # 遍历结束信号
        chunk = DocumentChunk(self._current, f"chunk-{self._current}-content")
        self._current += 1                      # 位置前移
        return chunk


def chunks_generator(total: int):
    """生成器：yield 自动实现迭代器协议，是 ChunkIterator 的语法糖版本"""
    for i in range(total):
        yield DocumentChunk(i, f"chunk-{i}-content")


def main():
    print("== 手写迭代器（懒加载，一次只读一块）==")
    for chunk in ChunkIterator(5):
        print(f"  块 {chunk.index}: {chunk.text}")

    print("\n== 生成器版本（效果一样，代码更短）==")
    for chunk in chunks_generator(3):
        print(f"  块 {chunk.index}: {chunk.text}")


if __name__ == "__main__":
    main()
