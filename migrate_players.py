import json
import os

old_file = "players.json"
new_file = "players.json"
chat_id = "-1003976511910"  # замени на свой chat_id

def migrate_players():
    if not os.path.exists(old_file):
        print(f"Ошибка: файл {old_file} не найден.")
        return

    with open(old_file, "r", encoding="utf-8") as f:
        try:
            old_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка: файл {old_file} содержит неверный JSON.")
            return

    if "groups" in old_data:
        print("Файл уже в новой структуре.")
        return

    new_data = {
        "groups": {
            chat_id: {
                "players": old_data
            }
        }
    }

    with open(new_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"Готово! Новый файл создан: {new_file}")

if __name__ == "__main__":
    migrate_players()