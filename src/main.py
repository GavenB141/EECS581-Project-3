'''
Author: Jocelyn Miller, Cooper Fish
KUID: 3090871
Last Modified: 11.10.26
Modification: Add swarm movement and controls to BattleGameScreen
Purpose: Connect swarm movement, combat, and rendering to the game screen
'''
import pyray as rl
from stack_screen import Stack , TitleScreen


def main():
    # Initialize Raylib window
    rl.init_window(800, 600, "Bug Game")
    rl.set_target_fps(60)

    # Instantiate the stack and seed it with the Title Screen
    stack = Stack()
    stack.push(TitleScreen(stack))

    try:
        while not rl.window_should_close() and not stack.is_empty():
            stack.peek().handle_input()
            # A button can change the active screen before this frame is drawn.
            current_screen = stack.peek()
            if current_screen is None:
                break
            current_screen.update()

            rl.begin_drawing()
            rl.clear_background(rl.RAYWHITE)
            current_screen.render()
            rl.end_drawing()
    finally:
        rl.close_window()

if __name__ == "__main__":
    main()
