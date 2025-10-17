#!/usr/bin/env python3
"""
Простой тест для проверки основных функций бота
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    detect_gender_by_name,
    detect_gender_correction,
    parse_ingredients,
    find_matching_recipes,
    get_gender_pronoun
)

def test_gender_detection():
    """Тестируем определение пола по имени"""
    print("🧪 Тестируем определение пола по имени...")
    
    test_cases = [
        ("Анна", "female"),
        ("Александр", "male"),
        ("Мария", "female"),
        ("Дмитрий", "male"),
        ("НеизвестноеИмя", "unknown")
    ]
    
    for name, expected in test_cases:
        result = detect_gender_by_name(name)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {name} -> {result} (ожидалось {expected})")

def test_gender_correction():
    """Тестируем поправку пола"""
    print("\n🧪 Тестируем поправку пола...")
    
    test_cases = [
        ("я мальчик", "male"),
        ("я девочка", "female"),
        ("я мужчина", "male"),
        ("я женщина", "female"),
        ("обычное сообщение", None)
    ]
    
    for text, expected in test_cases:
        result = detect_gender_correction(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text}' -> {result} (ожидалось {expected})")

def test_ingredient_parsing():
    """Тестируем парсинг ингредиентов"""
    print("\n🧪 Тестируем парсинг ингредиентов...")
    
    test_cases = [
        ("макароны, яйца, бекон", ["макароны", "яйца", "бекон"]),
        ("картофель; лук; морковь", ["картофель", "лук", "морковь"]),
        ("мясо\nрис\nовощи", ["мясо", "рис", "овощи"]),
        ("просто слова", ["просто", "слова"])
    ]
    
    for text, expected in test_cases:
        result = parse_ingredients(text)
        # Сравниваем без учета порядка
        status = "✅" if set(result) == set(expected) else "❌"
        print(f"  {status} '{text}' -> {result}")

def test_recipe_matching():
    """Тестируем подбор рецептов"""
    print("\n🧪 Тестируем подбор рецептов...")
    
    test_cases = [
        (["макароны", "яйца", "бекон", "сыр"], 1),  # Должен найти пасту карбонара
        (["говядина", "свекла", "капуста"], 1),     # Должен найти борщ
        (["хлеб", "молоко"], 0),                    # Не должно найти рецептов
    ]
    
    for ingredients, expected_min in test_cases:
        result = find_matching_recipes(ingredients)
        status = "✅" if len(result) >= expected_min else "❌"
        print(f"  {status} {ingredients} -> {len(result)} рецептов (минимум {expected_min})")
        for match in result:
            print(f"    - {match['name']} (не хватает: {match['missing_required']})")

def test_pronouns():
    """Тестируем местоимения"""
    print("\n🧪 Тестируем местоимения...")
    
    test_cases = [
        ("male", {"you": "сынок", "address": "сынок"}),
        ("female", {"you": "дочка", "address": "дочка"}),
        ("unknown", {"you": "детка", "address": "детка"})
    ]
    
    for gender, expected in test_cases:
        result = get_gender_pronoun(gender)
        status = "✅" if result["you"] == expected["you"] and result["address"] == expected["address"] else "❌"
        print(f"  {status} {gender} -> {result['you']}, {result['address']}")

if __name__ == "__main__":
    print("🚀 Запуск тестов кулинарного бота...")
    print("=" * 50)
    
    test_gender_detection()
    test_gender_correction()
    test_ingredient_parsing()
    test_recipe_matching()
    test_pronouns()
    
    print("\n" + "=" * 50)
    print("✅ Тесты завершены!")
