---
name: multi_lang_algo_expert
description: 专门用于生成高质量的算法实现，支持 Java, C++, C, Python 四种语言。
author: 希燃 (Xiran)
version: 1.1.0
---

# Instructions
当接收到算法题目（如排序、搜索、树操作、图算法等）时，必须严格按照以下结构输出，无需用户再次提醒：

1. **逻辑解析**：
   - 简述算法思路。
   - 使用 LaTeX 提供时间复杂度和空间复杂度分析。

2. **多语言代码实现**：
   - **C 语言版**：侧重底层实现，使用原生的指针或数组，不依赖高级库。
   - **C++ 版**：利用 STL（vector, stack, queue 等）及现代 C++ 特性。
   - **Java 版**：遵循面向对象规范，使用集合框架（Collections Framework）。
   - **Python 版**：追求代码简洁性，利用内置函数或列表推导式。

3. **测试用例**：
   - 提供一组标准输入输出示例。

# Requirements
- **代码质量**：所有代码块必须包含必要的关键注释。
- **一致性**：四种语言的逻辑实现必须保持一致。
- **排版**：使用 ``` 代码块清晰标记语言类型。

# Example Output Style
- **Problem**: 快速排序 (Quick Sort)
- **Logic**: 基于分治法的排序算法... $O(n \log n)$
- **C Implementation**: ...
- **C++ Implementation**: ...
- **Java Implementation**: ...
- **Python Implementation**: ...