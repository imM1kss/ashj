#imports
import json
from typing import Optional,List,Tuple, Dict

#class of keyboard
class VkKeyboard:
    #create new keyboard
    def __init__(self, inline: bool = True):
        self.keyboard = {
                    "inline": inline,
                    "buttons": []
                }
    # add new callback button to current line func -> None
    def add_callback_button(self,
                   label:Optional[str] = None,
                   color:Optional[str] = None,
                   payload:Optional[Dict] = None) -> None:
        
        #get buttons from keyboard
        self.buttons = self.keyboard["buttons"]

        #add new line if it was empty
        if len(self.buttons) == 0:
            self.buttons.append([])
        
        #transforms from None -> Value or don't change it
        label = label or "Укажите текст"
        color = color or "primary"
        payload = payload or {}

        #add new button to current line
        self.buttons[-1].append({
                                "action": {"type": "callback", "label": label, "payload": payload},
                                "color": color
                            })
    # add line t okeyboard func -> None
    def add_line(self) -> None:
        self.buttons.append([])
    
    # converting dict keyboard to json
    def get_keyboard(self) -> str:
        return json.dumps(self.keyboard, ensure_ascii=False)
        