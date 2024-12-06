import pyautogui
import pygetwindow as gw
import time

WINDOW_TITLE = "Monkey CalculatingPK"
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 100
ANSWER_WIDTH = 780
ANSWER_HEIGHT = 610
MAXIMUM_DIGIT = 4
DIGIT_MARGIN = 40

WINDOW_POSITION_OFFSET_X = 10
WINDOW_POSITION_OFFSET_Y = 45

MOVE_DURATION = 0.05
WAIT_DURATION = 1.2

def draw_number(num, x, y):
    digits = []
    for digit in str(num):
        digits.append(int(digit))
    
    w = ANSWER_WIDTH // MAXIMUM_DIGIT - DIGIT_MARGIN
    h = ANSWER_HEIGHT // 3 * 2
    y = y + ANSWER_HEIGHT // 6 + DIGIT_MARGIN // 2
    h = h - DIGIT_MARGIN
    
    for i in range(len(digits)):
        x = x + DIGIT_MARGIN // 2
        segments = [
            [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],                               # 0
            [(x + w // 2, y), (x + w // 2, y + h)],                                                 # 1
            [(x, y), (x + w, y), (x, y + h), (x + w, y + h)],                                       # 2
            [(x, y), (x + w, y + h // 4), (x, y + h // 2),(x + w, y + h // 4 * 3),(x, y + h)],      # 3
            [(x + w, y + h), (x + w, y), (x, y + h // 2), (x + w, y + h // 2)],                     # 4
            [(x + w, y), (x, y), (x, y + h // 2), (x + w, y + h // 2), (x + w, y + h), (x, y + h)], # 5
            [(x + w, y), (x, y + h // 2), (x + w, y + h), (x + w, y + h // 2), (x, y + h // 2)],    # 6
            [(x, y), (x + w, y), (x + w, y + h)],                                                   # 7
            [(x, y), (x + w, y), (x, y + h), (x + w, y + h), (x, y)],                               # 8
            [(x + w, y + h), (x + w, y), (x, y), (x, y + h // 2), (x + w, y + h // 4)],             # 9
        ]
        
        pyautogui.moveTo(segments[digits[i]][0][0], segments[digits[i]][0][1], duration=MOVE_DURATION)
        pyautogui.mouseDown(button='left')
        for segment in segments[digits[i]]:
            pyautogui.moveTo(segment[0], segment[1], duration=MOVE_DURATION)
        pyautogui.mouseUp(button='left')
        x = x + w + DIGIT_MARGIN // 2
    

def main():
    target_window = None
    while target_window == None:
        for window in gw.getAllWindows():
            if WINDOW_TITLE in window.title:
                target_window = window
                break
    
    time.sleep(1)  # waiting to activate
    
    origin_x, origin_y = target_window.left, target_window.top
    width, height = target_window.width, target_window.height
    
    start_button_x = origin_x + width // 2
    start_button_y = origin_y + height * 0.7
    
    canvas_x = origin_x + WINDOW_POSITION_OFFSET_X + 35
    canvas_y = origin_y + WINDOW_POSITION_OFFSET_Y + 635
    
    restart_button_x = origin_x + width // 2
    restart_button_y = origin_y + height * 0.8
    
    pyautogui.moveTo(start_button_x, start_button_y, duration=MOVE_DURATION)
    time.sleep(0.5)
    pyautogui.click()
    
    list = [12,23,34,45,56,67,78,89,90,100]
    for i in list:
        draw_number(i, canvas_x, canvas_y)
        pyautogui.press('enter')
        time.sleep(WAIT_DURATION)
    
    pyautogui.moveTo(start_button_x, start_button_y, duration=MOVE_DURATION)
    time.sleep(1)
    pyautogui.click()

main()