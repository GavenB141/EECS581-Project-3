'''
Author: Jocelyn Miller, Cooper Fish
KUID: 3090871
Last Modified: 11.10.26
Modification: Implement BattleGameScreen for battle functionality
Purpose: connects BattleSystem to the game screen
'''
import pyray as rl
import stack_screen
from stack_screen import Stack, TitleScreen, GameScreen
from world import World
from battle import BattleSystem

class BattleGameScreen(GameScreen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack)
        self.world = World()
        self.world.register_system(BattleSystem())

    def update(self):
        self.world.update(rl.get_frame_time())

stack_screen.GameScreen = BattleGameScreen

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
