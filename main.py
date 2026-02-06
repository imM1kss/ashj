while True: 
    try:
        import threading
        import time
        import json
        from datetime import datetime, timedelta

        from parser import run_parser
        from vkbot import run_bot, send_message, get_cab, get_hw

        def parser_pool():
            while True:
                res = run_parser()
                today = datetime.today()

                if today.weekday() == 5:  
                    next_day = today + timedelta(days=2)
                elif today.weekday() == 6:
                    next_day = today + timedelta(days=1)
                else:
                    next_day = today + timedelta(days=1)

                ndd = next_day.strftime("%d.%m")

                if res:
                    with open('data.json', 'r', encoding='utf-8') as file:
                        data = json.load(file)

                    text = f"Расписание({ndd}):\n"
                    line = "-" *30
                    text += "".join(line)
                    for row in data['last_schedule']:
                        cab = get_cab(row[2])
                        text += f"\n({row[0][:1]}) {row[1]} [{cab}]"
                    text += f"\n{line}"

                    hw_text, att = get_hw()
                    if hw_text == "":
                        if att:
                            hw_text = "\nТекст не добавили, но есть вложение."
                        else:
                            hw_text = "\nНе задано"
                    
                    text += hw_text
                    
                    send_message(msg = text)

                    #высылаем вложения
                    if att:
                        send_message(msg = "Вложение к дз", attachment=att)

                time.sleep(600)


        bot_thread = threading.Thread(target=run_bot, daemon=True)
        parser_thread = threading.Thread(target=parser_pool, daemon=True)

        bot_thread.start()
        parser_thread.start()

        bot_thread.join()
        parser_thread.join()
    except Exception as e:
        print(e)