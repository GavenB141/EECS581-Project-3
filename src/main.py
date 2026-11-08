'''
Author: Jocelyn Miller
KUID: 3090871
Last Modified: 11.7.26
Modification: Created Basic main function to test Screens implimentation
Purpose: Will eventually be where the game is launched from - for now it is here for testing purposes.
'''
from stack_screen import Stack, TitleScreen
import pyray as rl

def main():
    # Initialize Raylib window
    rl.init_window(800, 600, "Project 3 - Screen Stack Test")
    rl.set_target_fps(60)

    # Instantiate the stack and seed it with the Title Screen
    stack = Stack()
    stack.push(TitleScreen(stack))

    while not rl.window_should_close():
        # Get the screen currently at the top of the stack
        current_screen = stack.peek()

        if current_screen:
            current_screen.handle_input()
            current_screen.update()

        # Begin Raylib drawing frame
        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)

        if current_screen:
            current_screen.render()
        else:
            # If stack becomes empty, exit gracefully
            break

        rl.end_drawing()

    rl.close_window()

if __name__ == "__main__":
    main()