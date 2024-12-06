import inspect
import os
import time
import tkinter as tk
from ctypes import windll
from random import randint, choice
import cv2
import numpy as np
import tensorflow as tf
from PIL import Image, ImageDraw, ImageTk, ImageOps
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist

DEBUG_FLAG = True  # Debug flag

script_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
MODEL_PATH = os.path.join(script_directory, "model.h5")
MODEL_EPOCHS = 10
WINDOW_WIDTH = 850
WINDOW_HEIGHT = 1400
ANSWER_WIDTH = 780
ANSWER_HEIGHT = 610
QUESTION_COUNT = 10
TIMEOUT_SECONDS = 10
WAIT_DURATION = 1000
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 100
PEN_WIDTH = 16
ICON_SIZE = 480


class DigitRecognizer:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = tf.keras.models.load_model(MODEL_PATH)
            print("Model loaded successfully!")
        else:
            print("No saved model found. Training a new model...")
            self.train_model()

    def train_model(self):
        (x_train, y_train), (x_test, y_test) = mnist.load_data()

        x_train = x_train.astype("float32") / 255.0
        x_test = x_test.astype("float32") / 255.0
        x_train = np.expand_dims(x_train, -1)  # (60000, 28, 28, 1)
        x_test = np.expand_dims(x_test, -1)  # (10000, 28, 28, 1)

        y_train = tf.keras.utils.to_categorical(y_train, 10)
        y_test = tf.keras.utils.to_categorical(y_test, 10)

        self.model = models.Sequential([
            layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.Flatten(),
            layers.Dense(64, activation='relu'),
            layers.Dense(10, activation='softmax')
        ])

        self.model.summary()

        self.model.compile(optimizer='adam',
                           loss='categorical_crossentropy',
                           metrics=['accuracy'])

        self.model.fit(x_train, y_train, epochs=MODEL_EPOCHS, batch_size=64, validation_split=0.1)

        self.model.save(MODEL_PATH)
        print(f"Model saved successfully! Path: {MODEL_PATH}")

        test_loss, test_acc = self.model.evaluate(x_test, y_test, verbose=2)
        print(f"Test accuracy: {test_acc:.4f}")

    def recognize_digits(self, image):
        image = ImageOps.invert(image).convert("L")
        image = image.point(lambda p: p > 128 and 255)

        image_array = np.array(image)

        contours, _ = cv2.findContours(image_array, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 512]
        bounding_boxes = sorted(bounding_boxes, key=lambda x: x[0])

        predictions = []
        idx = 0
        for x, y, w, h in bounding_boxes:
            digit_image = image.crop((x, y, x + w, y + h))

            size = max(digit_image.size[0], digit_image.size[1])
            square_digit = Image.new("L", (size, size), "black")
            square_digit.paste(digit_image,
                               (int((size - digit_image.size[0]) / 2), int((size - digit_image.size[1]) / 2)))

            margin = 4
            square_digit = square_digit.resize((28 - margin * 2, 28 - margin * 2))
            square_digit = ImageOps.expand(square_digit, border=margin, fill="black")

            if DEBUG_FLAG:
                square_digit.save(script_directory + f"\\digit_{idx}.png")
                idx += 1

            digit_array = np.array(square_digit).astype('float32') / 255.0
            digit_array = digit_array.reshape(1, 28, 28, 1)

            prediction = self.model.predict(digit_array)
            predictions.append(np.argmax(prediction))

        print(f"Predicted Labels: {predictions}")
        return predictions


def load_background_image(path):
    background_image = Image.open(path)
    background_height = background_image.size[1]
    background_width = int(background_height * (WINDOW_WIDTH / WINDOW_HEIGHT))
    margin_left = background_image.size[0] // 2 - background_width // 2
    margin_right = margin_left + background_width
    background_image = background_image.crop((margin_left, 0, margin_right, background_height)).resize(
        (WINDOW_WIDTH, WINDOW_HEIGHT))
    return ImageTk.PhotoImage(background_image)


class CalculatingPKGui:
    def __init__(self, window, recognizer):
        self.recognizer = recognizer

        self.window = window
        self.window.title("Monkey CalculatingPK")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.resizable(False, False)

        self.question = ""
        self.answer = None
        self.remaining_time = 0
        self.current_question_index = 0
        self.timer_id = None

        self.background_menu = load_background_image(script_directory + "\\res\\menuBackground.jpg")
        self.background_game = load_background_image(script_directory + "\\res\\gameBackground.png")

        self.correct_icon = ImageTk.PhotoImage(
            Image.open(script_directory + "\\res\\correct.png").resize((ICON_SIZE, ICON_SIZE)))
        self.wrong_icon = ImageTk.PhotoImage(
            Image.open(script_directory + "\\res\\wrong.png").resize((ICON_SIZE, ICON_SIZE)))

        self.canvas = None
        self.question_count = None
        self.question_text = None
        self.timer_text = None
        self.ans_canvas = None
        self.ans_image = None
        self.draw_tool = None
        self.submit_button = None
        self.clear_button = None
        self.points = []
        self.last_x = None
        self.last_y = None
        self.accept_submissions = False
        self.current_question_index = 0
        self.correct_answers = 0
        self.timeout_questions = 0
        self.wrong_answers = 0
        self.welcome_frame = None
        self.game_frame = None
        self.result_frame = None

    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()

    def welcome_ui(self):
        self.clear_window()
        self.welcome_frame = tk.Frame(self.window)
        self.welcome_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(self.welcome_frame, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=self.background_menu)
        canvas.create_text(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4, text="Monkey Calculating PK",
                           font=("Consolas", 32, "bold"), fill="#f0f0f0")

        start_button = tk.Button(self.welcome_frame,
                                 text="Start Game",
                                 font=("Consolas", 16),
                                 activebackground="#cfdcf0",
                                 relief="flat",
                                 bg="#135bc8",
                                 fg="white",
                                 cursor="hand2",
                                 command=self.start_game)

        start_button.place(relx=0.5, rely=0.7, anchor=tk.CENTER, width=BUTTON_WIDTH, height=BUTTON_HEIGHT)

    def generate_question(self):
        operation = choice(["+", "-", "*", "/"])
        if operation == "*":
            num1, num2 = randint(1, 10), randint(1, 10)
            answer = eval(f"{num1} {operation} {num2}")
            question = f"{num1} {operation} {num2} = ?"
            self.answer = answer
            self.question = question
        elif operation == "/":
            num1, num2 = randint(5, 35), randint(1, 9)
            answer = num1 // num2
            if num1 % num2 == 0:
                question = f"{num1} {operation} {num2} = ?"
            else:
                question = f"{num1} {operation} {num2} = ? ... {num1 % num2}"
        else:
            num1, num2 = randint(1, 20), randint(1, 20)
            num1, num2 = max(num1, num2), min(num1, num2)
            answer = eval(f"{num1} {operation} {num2}")
            question = f"{num1} {operation} {num2} = ?"

        self.answer = answer
        self.question = question

    def start_game(self):
        self.current_question_index = 0
        self.correct_answers = 0
        self.timeout_questions = 0
        self.wrong_answers = 0
        self.game_ui()

    def game_ui(self):
        self.clear_window()
        self.game_frame = tk.Frame(self.window)
        self.game_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.game_frame, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, anchor="nw", image=self.background_game)

        self.generate_question()
        self.question_count = self.canvas.create_text(
            WINDOW_WIDTH // 2, 120,
            text=f"Question {self.current_question_index + 1} / {QUESTION_COUNT}",
            font=("Cambria", 24),
            fill="black")

        self.question_text = self.canvas.create_text(
            WINDOW_WIDTH // 2, 300,
            text=self.question,
            font=("Cambria", 36),
            fill="black")

        self.timer_text = self.canvas.create_text(
            WINDOW_WIDTH // 2, 615,
            text="00 : {:02d}".format(TIMEOUT_SECONDS),
            font=("Arial", 12),
            fill="#88f66f")

        self.ans_canvas = tk.Canvas(self.game_frame, bg="#dceeff", width=ANSWER_WIDTH, height=ANSWER_HEIGHT)
        self.ans_canvas.place(x=35, y=635, anchor="nw")
        self.ans_canvas.bind("<B1-Motion>", self.draw)
        self.ans_canvas.bind("<Button-1>", self.mouse_press)
        self.ans_canvas.bind("<ButtonRelease-1>", self.mouse_release)
        self.last_x = None
        self.last_y = None

        self.ans_image = Image.new("L", (ANSWER_WIDTH, ANSWER_HEIGHT), "white")
        self.draw_tool = ImageDraw.Draw(self.ans_image)

        self.submit_button = tk.Button(self.game_frame,
                                       text="Submit",
                                       font=("Consolas", 16, "bold"),
                                       activebackground="#cfdcf0",
                                       relief="flat",
                                       bg="#24a978",
                                       fg="#f0f0f0",
                                       cursor="hand2",
                                       command=self.submit_answer)
        self.submit_button.place(relx=0.25, rely=0.95, anchor=tk.CENTER, width=BUTTON_WIDTH, height=BUTTON_HEIGHT)

        self.clear_button = tk.Button(self.game_frame,
                                      text="Clear",
                                      font=("Consolas", 16, "bold"),
                                      bg="#fc5143",
                                      fg="#f0f0f0",
                                      activebackground="#ffccce",
                                      relief="flat",
                                      cursor="hand2",
                                      command=self.clear_canvas)
        self.clear_button.place(relx=0.75, rely=0.95, anchor=tk.CENTER, width=BUTTON_WIDTH, height=BUTTON_HEIGHT)

        self.window.bind("<Return>", lambda event: self.submit_answer())

        self.accept_submissions = True
        self.remaining_time = TIMEOUT_SECONDS
        self.update_timer()

    def mouse_press(self, event):
        self.last_x = event.x
        self.last_y = event.y
        self.points = [(event.x, event.y)]

    def draw(self, event):
        if self.last_x is None or self.last_y is None:
            return

        self.ans_canvas.create_line(self.last_x, self.last_y, event.x, event.y, width=PEN_WIDTH, capstyle=tk.ROUND,
                                    joinstyle=tk.BEVEL, fill="black")
        self.points.append((event.x, event.y))
        self.last_x = event.x
        self.last_y = event.y

    def mouse_release(self, event):
        self.points.append((event.x, event.y))
        self.draw_tool.line(self.points, joint="curve", fill="black", width=PEN_WIDTH)
        self.points.clear()
        self.last_x = None
        self.last_y = None

    def clear_canvas(self):
        self.ans_canvas.delete("all")
        self.ans_image = Image.new("L", (ANSWER_WIDTH, ANSWER_HEIGHT), "white")
        self.draw_tool = ImageDraw.Draw(self.ans_image)
        self.points.clear()
        self.last_x = None
        self.last_y = None

    def next_question(self):
        if self.current_question_index == QUESTION_COUNT - 1:
            self.show_result()
            return

        self.current_question_index += 1
        self.remaining_time = TIMEOUT_SECONDS
        self.clear_canvas()
        self.generate_question()

        self.canvas.itemconfigure(self.question_count,
                                  text=f"Question {self.current_question_index + 1} / {QUESTION_COUNT}")
        self.canvas.itemconfigure(self.question_text, text=self.question)
        self.canvas.itemconfigure(self.timer_text, text="00 : {:02d}".format(TIMEOUT_SECONDS))
        self.update_timer()
        
        self.accept_submissions = True

    def submit_answer(self):
        if not self.accept_submissions:
            return
        
        self.accept_submissions = False
        
        if self.timer_id is not None:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None

        if DEBUG_FLAG:
            self.ans_image.save(script_directory + f"\\ans_{self.current_question_index}.png")

        digits = self.recognizer.recognize_digits(self.ans_image)
        ans = 0
        for digit in digits:
            ans = ans * 10 + digit

        if ans == self.answer and len(digits) != 0:
            self.correct_answers += 1
            self.ans_canvas.create_image(ANSWER_WIDTH // 2, ANSWER_HEIGHT // 2, image=self.correct_icon)
        else:
            self.wrong_answers += 1
            self.ans_canvas.create_image(ANSWER_WIDTH // 2, ANSWER_HEIGHT // 2, image=self.wrong_icon)
            self.ans_canvas.create_text(ANSWER_WIDTH // 2, ANSWER_HEIGHT // 2 - 240,
                                        text=f"Correct Answer: {self.answer}",
                                        font=("Cambria", 36),
                                        fill="#fc5143")

        self.window.after(WAIT_DURATION, self.next_question)
        
    def update_timer(self):
        if self.timer_id is not None:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None

        if self.remaining_time > 0:
            self.canvas.itemconfigure(self.timer_text, text="00 : {:02d}".format(self.remaining_time))
            self.remaining_time -= 1
            self.timer_id = self.window.after(1000, self.update_timer)
        else:
            if self.remaining_time == 0:
                self.timeout_questions += 1
            self.next_question()

    def show_result(self):
        self.clear_window()
        self.result_frame = tk.Frame(self.window)
        self.result_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(self.result_frame, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=self.background_menu)

        canvas.create_text(WINDOW_WIDTH // 2, 160,
                           text=f"Game Over!",
                           font=("Cambria", 48),
                           fill="#f0f0f0")

        canvas.create_text(WINDOW_WIDTH // 2, 300,
                           text=f"Correct Answers: {self.correct_answers}",
                           font=("Cambria", 36),
                           fill="#31e6a3")

        canvas.create_text(WINDOW_WIDTH // 2, 400,
                           text=f"Wrong Answers: {self.wrong_answers}",
                           font=("Cambria", 36),
                           fill="#fc5143")

        canvas.create_text(WINDOW_WIDTH // 2, 500,
                           text=f"Timeout Questions: {self.timeout_questions}",
                           font=("Cambria", 36),
                           fill="orange")

        restart_button = tk.Button(self.result_frame,
                                   text="Try again",
                                   font=("Consolas", 18),
                                   activebackground="#cfdcf0",
                                   relief="flat",
                                   bg="#135bc8",
                                   fg="white",
                                   cursor="hand2",
                                   command=self.welcome_ui)
        restart_button.place(relx=0.5, rely=0.8, anchor=tk.CENTER, width=BUTTON_WIDTH, height=BUTTON_HEIGHT)


def main():
    recognizer = DigitRecognizer()
    windll.shcore.SetProcessDpiAwareness(1)  # High DPI awareness for Windows
    window = tk.Tk()
    app = CalculatingPKGui(window, recognizer)
    app.welcome_ui()
    window.mainloop()


main()
