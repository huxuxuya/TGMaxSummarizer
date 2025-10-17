#!/usr/bin/env python3
"""
Тест для проверки фильтрации сообщений по классификации
"""

def test_message_filtering():
    """Тест фильтрации сообщений"""
    
    # Тестовые сообщения
    test_messages = [
        {
            'message_id': '1',
            'sender_id': 44502596,
            'text': 'Важное объявление о мероприятии',
            'time': '10:30'
        },
        {
            'message_id': '2', 
            'sender_id': 12345,
            'text': '👍',
            'time': '10:31'
        },
        {
            'message_id': '3',
            'sender_id': 67890,
            'text': 'Можно забрать Машу в 15:00?',
            'time': '10:32'
        },
        {
            'message_id': '4',
            'sender_id': 44502596,
            'text': 'Изменение расписания на завтра',
            'time': '10:33'
        },
        {
            'message_id': '5',
            'sender_id': 11111,
            'text': 'Спасибо за информацию',
            'time': '10:34'
        }
    ]
    
    # Результаты классификации
    test_classification = [
        {'message_id': '1', 'class': 'announcement'},
        {'message_id': '2', 'class': 'irrelevant'},
        {'message_id': '3', 'class': 'release_pickup'},
        {'message_id': '4', 'class': 'schedule_change'},
        {'message_id': '5', 'class': 'irrelevant'}
    ]
    
    # Импортируем ChatAnalyzer
    from chat_analyzer import ChatAnalyzer
    
    # Создаем экземпляр
    analyzer = ChatAnalyzer()
    
    # Тестируем фильтрацию
    filtered_messages = analyzer._filter_by_classification(test_messages, test_classification)
    
    print("=== Тест фильтрации сообщений ===")
    print(f"Исходные сообщения: {len(test_messages)}")
    print(f"Отфильтрованные сообщения: {len(filtered_messages)}")
    print()
    
    print("Исходные сообщения:")
    for i, msg in enumerate(test_messages):
        msg_class = next((c['class'] for c in test_classification if c['message_id'] == msg['message_id']), 'unknown')
        print(f"  {i+1}. [{msg_class}] {msg['text'][:50]}...")
    
    print("\nОтфильтрованные сообщения:")
    for i, msg in enumerate(filtered_messages):
        msg_class = next((c['class'] for c in test_classification if c['message_id'] == msg['message_id']), 'unknown')
        print(f"  {i+1}. [{msg_class}] {msg['text'][:50]}...")
    
    # Проверяем результат
    expected_filtered_ids = {'1', '4'}  # announcement и schedule_change
    actual_filtered_ids = {msg['message_id'] for msg in filtered_messages}
    
    print(f"\nОжидаемые ID: {expected_filtered_ids}")
    print(f"Фактические ID: {actual_filtered_ids}")
    
    if expected_filtered_ids == actual_filtered_ids:
        print("✅ Тест пройден успешно!")
        print("✅ Исключены irrelevant и release_pickup сообщения")
        return True
    else:
        print("❌ Тест не пройден!")
        return False

if __name__ == "__main__":
    test_message_filtering()
