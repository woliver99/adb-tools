import os
import platform
from typing import Callable, Any, Optional

# ----------------------------------------------------------
# TerminalMenu by woliver99
# ----------------------------------------------------------


def DEFAULT_EXIT_RUNNABLE(): return exit(0)


class Option:
    title: str
    runnable: Callable[[], Any]

    def __init__(self, title: str, runnable: Callable[[], Any]):
        self.title = title
        self.runnable = runnable


class OptionMenu:
    menu_title: str
    options: list[Option]
    exit_runnable: Callable[[], Any]
    default_index: Optional[int]  # 1-based index

    def __init__(
        self,
        menu_title: str,
        options: list[Option],
        exit_runnable: Callable[[], Any] = DEFAULT_EXIT_RUNNABLE,
        # Optional default option (1-based)
        default_index: Optional[int] = None,
    ):
        self.menu_title = menu_title
        self.options = options
        self.exit_runnable = exit_runnable
        self.default_index = default_index

        if self.default_index is not None:
            if not (1 <= self.default_index <= len(self.options)):
                raise ValueError(
                    f"default_index must be between 1 and {len(self.options)}, got {
                        self.default_index}"
                )

    def prompt(self) -> Callable[[], Any]:
        prompt_options = self.options
        prompt_options.append(Option("Exit", self.exit_runnable))

        print(f"{self.menu_title}:")

        option_dict: dict[int, Callable[[], Any]] = {}
        index = 1

        for option in prompt_options:
            option_dict[index] = option.runnable
            print(f"{index}) {option.title}")
            index += 1

        print()
        prompt_message = "Enter your choice"
        if self.default_index != None:
            prompt_message += f" [{self.default_index}]"
        prompt_message += ": "

        while True:
            try:
                user_input = input(prompt_message).strip()
                if user_input.lower() == "exit":
                    return self.exit_runnable
                elif user_input == "" and self.default_index is not None:
                    return option_dict[self.default_index]
                elif user_input.isdigit():
                    choice = int(user_input)
                    if 1 <= choice <= len(option_dict):
                        return option_dict[choice]
                print(
                    f"'{user_input}' is not a valid option. Please enter a number from 1 to {
                        len(option_dict)}."
                )
            except KeyboardInterrupt:
                print()
                return self.exit_runnable


class NumberInput:
    prompt_message: str
    default_value: Optional[float]
    exit_runnable: Callable[[], Any]
    min_value: Optional[float]
    max_value: Optional[float]

    def __init__(
        self,
        prompt_message: str,
        default_value: Optional[float] = None,
        exit_runnable: Callable[[], Any] = lambda: DEFAULT_EXIT_RUNNABLE,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        self.prompt_message = prompt_message
        self.default_value = default_value
        self.exit_runnable = exit_runnable
        self.min_value = min_value
        self.max_value = max_value

        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError("min_value cannot be greater than max_value")

        if self.default_value is not None:
            if self.min_value is not None and self.default_value < self.min_value:
                raise ValueError(
                    f"default_value {self.default_value} is less than min_value {
                        self.min_value}"
                )
            if self.max_value is not None and self.default_value > self.max_value:
                raise ValueError(
                    f"default_value {self.default_value} is greater than max_value {
                        self.max_value}"
                )

    def prompt(self) -> float | None:
        default_str = f" [default: {
            self.default_value}]" if self.default_value is not None else ""
        range_str = ""
        if self.min_value is not None and self.max_value is not None:
            range_str = f" (between {self.min_value} and {self.max_value})"
        elif self.min_value is not None:
            range_str = f" (min {self.min_value})"
        elif self.max_value is not None:
            range_str = f" (max {self.max_value})"
        full_prompt = f"{self.prompt_message}{range_str}{default_str}: "

        while True:
            try:
                user_input = input(full_prompt).strip()
                if user_input.lower() == "exit":
                    self.exit_runnable()
                elif user_input == "" and self.default_value is not None:
                    return self.default_value
                else:
                    # Attempt to convert input to float
                    value = float(user_input)
                    # Check range if applicable
                    if self.min_value is not None and value < self.min_value:
                        print(f"Value must be at least {
                              self.min_value}. Please try again.")
                        continue
                    if self.max_value is not None and value > self.max_value:
                        print(f"Value must be at most {
                              self.max_value}. Please try again.")
                        continue
                    return value
            except ValueError:
                print(f"'{user_input}' is not a valid float. Please try again.")
            except KeyboardInterrupt:
                print("")
                return self.exit_runnable()


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

    # Set the default option to Option 2 (index=2)
    def exit_runnable():
        print("Better goodbye!")
        exit(0)

    menu = OptionMenu(
        menu_title="Example Menu",
        options=options,
        exit_runnable=exit_runnable,
        default_index=2  # Makes Option 2 the default
    )
    menu.prompt()()


def example_number_input():
    # Define a custom exit runnable
    def exit_runnable():
        print("\nExiting number input. Goodbye!")
        exit(0)

    number_prompt = NumberInput(
        prompt_message="Please enter your height in meters",
        default_value=1.75,
        exit_runnable=exit_runnable,
        min_value=1,        # Minimum acceptable value
        max_value=None      # Maximum acceptable value
    )

    user_number = number_prompt.prompt()
    print(f"You entered: {user_number}")


if __name__ == "__main__":
    # example_menu()
    example_number_input()
