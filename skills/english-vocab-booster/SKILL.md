---
name: english-vocab-booster
description: 内置四级高频词库（示例）
---

import sys
import json
from datetime import datetime, timedelta

# 内置四级高频词库（示例）
CET4_WORDS = {
    "abandon": {"meaning": "放弃；抛弃", "example": "He abandoned his family."},
    "ability": {"meaning": "能力；才能", "example": "She has the ability to solve the problem."},
    "absent": {"meaning": "缺席的；不在的", "example": "He was absent from school yesterday."},
    "access": {"meaning": "访问；使用权", "example": "Students have free access to the library."},
    "account": {"meaning": "账户；解释", "example": "I have an account with this bank."}
}

def show_word(word: str):
    """查询单词释义和例句"""
    word = word.lower().strip()
    if word in CET4_WORDS:
        info = CET4_WORDS[word]
        print(f"📖 单词：{word}")
        print(f"   释义：{info['meaning']}")
        print(f"   例句：{info['example']}")
    else:
        print(f"❌ 未找到单词 '{word}'，请检查拼写或使用内置词库中的单词")

def daily_review(days: int = 5):
    """生成每日复习计划（艾宾浩斯记忆曲线简易版）"""
    today = datetime.now()
    print(f"📅 接下来{days}天的单词复习计划：")
    for i in range(days):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        words = list(CET4_WORDS.keys())[i::days]
        print(f"  {date_str} 复习：{', '.join(words[:3])}...")

def save_progress(username: str, learned_words: list):
    """保存学习进度到本地文件"""
    progress = {
        "username": username,
        "last_learned": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "learned_words": learned_words
    }
    with open("progress.txt", "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    print("✅ 学习进度已保存到 progress.txt")

def main():
    print("=" * 40)
    print("📚 English Vocab Booster - 英语词汇提升助手")
    print("=" * 40)
    print("1. 查询单词释义和例句")
    print("2. 生成每日复习计划")
    print("3. 保存学习进度")
    print("0. 退出程序")
    print("-" * 40)

    while True:
        choice = input("请输入功能编号：").strip()
        if choice == "0":
            print("👋 再见，祝你学习进步！")
            break
        elif choice == "1":
            word = input("请输入要查询的单词：")
            show_word(word)
        elif choice == "2":
            try:
                days = int(input("请输入计划天数（默认5天）：") or 5)
                daily_review(days)
            except ValueError:
                print("⚠️ 请输入有效的数字")
        elif choice == "3":
            username = input("请输入你的用户名：")
            learned = input("请输入今天学过的单词（用空格分隔）：").split()
            save_progress(username, learned)
        else:
            print("⚠️ 无效的选项，请重新输入")

if __name__ == "__main__":
    main()