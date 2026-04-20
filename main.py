while True: 
    try:
        from services.logging_config import setup_logging
        import logging

        setup_logging()

        import threading
        import time
        import json
        from datetime import datetime, timedelta

        from services.parser import run_parser
        from services.config_vk import send_message
        from services.Datbase import DataBase
        import asyncio
        import random
        import re

        logger = logging.getLogger("main")
        data = DataBase()

        def format_schedule(schedule):
            # Заголовок (можно добавить дату)
            last_date = data.get_last_schedule_date()
            now = datetime.strptime(last_date, "%Y-%m-%d")
            days = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
            date = f"{days[now.weekday()]} ({now.strftime("%d.%m")})"
            lines = [f"Расписание на {date}", "---------------------"]
            ln = []
            
            for lesson, subject, room in schedule:
                l = re.sub(r'\D', '', lesson)
                ln.append(l)
                s = subject.capitalize()
                r = "".join(c for c in room if c.isdigit()) if any(c.isdigit() for c in room) else room
                lines.append(f"({l})  {s}  [{r}]")

            lines.append("---------------------")

            if min(ln) > "1":
                lines.append(f"*@all ВНИМАНИЕ! Завтра к {min(ln)} паре")
                
            # Объединяем все строки с переносом
            return "\n".join(lines).strip()

        def parser_pool():
            try:
                result = run_parser()
                if result:
                    groups = data.get_group_names()
                    for name in groups:
                        date = data.get_last_schedule_date()
                        schedule = data.get_schedule(group_name=name, date=date)
                        vk_id = data.get_vk_id(group_name=name)
                        text = format_schedule(schedule=schedule)
                        
                        asyncio.run(send_message(peer_id=vk_id,text=text))
                        time.sleep(600)
            except Exception:
                logger.exception("Exception")

        thread_bot = threading.Thread(target=parser_pool, daemon=True)

        thread_bot.start()

        thread_bot.join()

        
    except Exception:
        logger.exception("Exception:")
