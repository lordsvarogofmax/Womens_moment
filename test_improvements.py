#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест улучшений бота-бати
"""

import re

def extract_name_from_text(text):
    """Извлекает имя из развернутого сообщения"""
    # Убираем лишние пробелы и приводим к нижнему регистру для анализа
    text_clean = re.sub(r'\s+', ' ', text.strip())
    
    # Паттерны для поиска имени
    patterns = [
        r'меня зовут\s+(\w+)',
        r'я\s+(\w+)',
        r'зовите меня\s+(\w+)',
        r'мое имя\s+(\w+)',
        r'имя\s+(\w+)',
        r'^(\w+)\s',  # Первое слово
        r'(\w+)$'     # Последнее слово
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Проверяем, что это не служебное слово
            if len(name) >= 2 and name.lower() not in ['меня', 'зовут', 'мое', 'имя', 'это', 'вот', 'так', 'да', 'нет']:
                return name.capitalize()
    
    # Если ничего не найдено, берем первое слово длиннее 2 символов
    words = text_clean.split()
    for word in words:
        if len(word) >= 2 and word.isalpha():
            return word.capitalize()
    
    return None

def test_name_extraction():
    """Тестирует извлечение имени из различных сообщений"""
    test_cases = [
        ("Меня зовут Анна", "Анна"),
        ("Я Мария", "Мария"),
        ("Зовите меня Петр", "Петр"),
        ("Мое имя Екатерина", "Екатерина"),
        ("Имя Дмитрий", "Дмитрий"),
        ("Анна", "Анна"),
        ("Привет, меня зовут Ольга, рада познакомиться", "Ольга"),
        ("Я студент, меня зовут Иван", "Иван"),
        ("Меня зовут Александра, а тебя как?", "Александра"),
        ("Да, я согласен, меня зовут Михаил", "Михаил"),
        ("Нет, я не хочу", None),  # Должно вернуть None
        ("Да", None),  # Должно вернуть None
        ("", None),  # Должно вернуть None
    ]
    
    print("🧪 Тестирование извлечения имени:")
    print("=" * 50)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_name_from_text(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{i:2d}. {status} '{input_text}' -> '{result}' (ожидалось: '{expected}')")
    
    print()

def test_dialogue_patterns():
    """Тестирует паттерны диалога"""
    test_cases = [
        ("как готовить", True, "вопрос о готовке"),
        ("что делать", True, "вопрос о готовке"),
        ("помоги", True, "просьба о помощи"),
        ("не понимаю", True, "просьба о помощи"),
        ("спасибо", True, "благодарность"),
        ("отлично", True, "благодарность"),
        ("не работает", True, "жалоба"),
        ("кто ты", True, "вопрос о бате"),
        ("привет", False, "обычное сообщение"),
        ("как дела", True, "вопрос о бате"),
    ]
    
    print("🧪 Тестирование паттернов диалога:")
    print("=" * 50)
    
    for i, (text, should_match, description) in enumerate(test_cases, 1):
        # Проверяем различные паттерны
        patterns = [
            ['как готовить', 'как приготовить', 'что делать', 'помоги', 'объясни'],
            ['помоги', 'не понимаю', 'не знаю', 'что делать', 'как'],
            ['спасибо', 'благодарю', 'отлично', 'круто', 'классно', 'супер'],
            ['не работает', 'ошибка', 'проблема', 'не получается', 'сломалось'],
            ['кто ты', 'что ты', 'как дела', 'как поживаешь']
        ]
        
        matched = False
        for pattern_list in patterns:
            if any(word in text.lower() for word in pattern_list):
                matched = True
                break
        
        status = "✅" if matched == should_match else "❌"
        print(f"{i:2d}. {status} '{text}' -> {matched} ({description})")
    
    print()

if __name__ == "__main__":
    print("🚀 Тестирование улучшений бота-бати")
    print("=" * 60)
    print()
    
    test_name_extraction()
    test_dialogue_patterns()
    
    print("✅ Тестирование завершено!")
    print()
    print("📋 Что улучшено:")
    print("• Извлечение имени из развернутых сообщений")
    print("• Умная обработка любых сообщений пользователя")
    print("• Контекстные ответы в зависимости от этапа диалога")
    print("• Поддержка вопросов, благодарностей, жалоб")
    print("• Персонализированные ответы с учетом имени и пола")
