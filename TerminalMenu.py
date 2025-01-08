import os
import platform
from typing import Callable, Any

# ----------------------------------------------------------
# TerminalMenu by woliver99 - v1.0
# ----------------------------------------------------------


class Option:
    title: str
    runnable: Callable[[], Any]

    def __init__(self, title: str, runnable: Callable[[], Any]):
        self.title = title
        self.runnable = runnable


class TerminalMenu:
    menu_title: str
    options: list[Option]
    exit_runnable: Callable[[], Any]

    def __init__(self, menu_title: str, options: list[Option], exit_runnable: Callable[[], Any] = lambda: print("Goodbye!") and exit(0)):
        self.menu_title = menu_title
        self.options = options
        self.exit_runnable = exit_runnable

    def prompt(self) -> Callable[[], Any]:
        print(f"{self.menu_title}:")
        option_dict: dict[int, Callable[[], Any]] = {}

        index = 1
        for option in self.options:
            option_dict[index] = option.runnable
            print(f"{index}) {option.title}")
            index += 1

        option_dict[index] = self.exit_runnable
        print(f"{index}) Exit")

        print()
        while True:
            user_input = input("Enter your choice: ")
            if user_input == "exit":
                return self.exit_runnable
            elif user_input.isdigit() and (int(user_input) > 0 and int(user_input) <= len(option_dict)):
                return option_dict[int(user_input)]
            else:
                print(
                    f"'{user_input}' is not a valid option. Please enter a number from 1 to {len(option_dict)}."
                )


def clear_terminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def example_menu():
    options = [
        Option("Option 1", lambda: print("Option 1 selected.")),
        Option("Option 2", lambda: print("Option 2 selected.")),
        Option("Option 3", lambda: print("Option 3 selected.")),
    ]
    def exit_runnable(): return print("Better goodbye!") and exit(0)
    menu = TerminalMenu("Example Menu", options, exit_runnable)
    menu.prompt()()


if __name__ == "__main__":
    example_menu()
