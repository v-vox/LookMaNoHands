import re
import speech_recognition as sr
import pyautogui
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading


def create_green_icon():
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 64, 64), fill=(0, 255, 0))
    return image

# Function to generate a red square icon
def create_red_icon():
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 64, 64), fill="red")
    return image


def handleText(text):
    text = text.lower()
    if "banana" in text or "cabana" in text or "bandana" in text or "montana" in text:
        if "backspace" in text or "back space" in text:
            num = extract_last_number(text)
            for i in range(num):
                pyautogui.press('backspace')
        elif "space" in text:
            num = extract_last_number(text)
            for i in range(num):
                pyautogui.press('space')
        elif "enter" in text:
            pyautogui.press('enter')
        elif "escape" in text:
            pyautogui.press('esc')
        elif "page up" in text:
            pyautogui.press('pageup')
        elif "page down" in text:
            pyautogui.press('pagedown')
        elif "tab" in text:
            pyautogui.press('tab')
        elif "comma" in text:
            pyautogui.press(',')
        elif "period" in text:
            pyautogui.press('.')
        elif "exclamation mark" in text:
            pyautogui.press('!')
        elif "question mark" in text:
            pyautogui.press('?')
        elif "quote" in text:
            pyautogui.press('"')
        elif "colon" in text:
            pyautogui.press(':')
    else:
        pyautogui.typewrite(text)

def extract_last_number(text):
    # Find all sequences of digits in the string
    numbers = re.findall(r'\d+', text)
    if numbers:
        # Return the last number found
        return int(numbers[-1])
    return 1  # Return None if no number is found

speechToggle = False

def recognize_speech(icon):
    global speechToggle

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something...")
        icon.icon = create_green_icon()
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        icon.icon = create_red_icon()
    try:
        text = recognizer.recognize_google(audio)
        print("You said: " + text)
        print(speechToggle)
        if "orange" in text.lower():
            speechToggle = not speechToggle
        elif speechToggle:
            handleText(text)
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio.")
    except sr.RequestError:
        print("Could not request results, check your internet connection.")

def run_speech_recognition(icon):
    while True:
        recognize_speech(icon)


def on_quit(icon, item):
    icon.stop()


def setup_tray():
    icon_image = create_green_icon()  # Start with a green square icon
    icon_menu = Menu(MenuItem('Quit', on_quit))
    
    # Create the icon and add the menu
    icon = Icon("Speech Recognition", icon_image, menu=icon_menu)
    
    # Run the speech recognition in a background thread
    threading.Thread(target=run_speech_recognition, args=(icon,), daemon=True).start()
    
    # Run the icon in the background
    icon.run()

# Main function
if __name__ == "__main__":
    setup_tray()