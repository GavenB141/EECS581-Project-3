'''
Author: Jocelyn Miller
KUID: 3090871
Class Name: Stack, Screen, TitleScreen, GameScreen, OptionsScreen, UpgradeScreen, PauseScreen, and Button
Last Modified: 11.7.26
Modification: Began implimentation of other Screeb Classes
Purpose of Class: Basic Screens have been implimented, but buttons might need to be moved
To Do: Upgrades functionality
       Game World rendering and implimentation
       Options implimentation/functionality
       Fix `Return to Menu` buttons (they don't work and I'm not sure why)
'''

import pyray as rl
import sys

class Stack: # Basic stack implementation using a list as the underlying data structure
  def __init__(self): 
    self.stack = []

  def is_empty(self):
      return self.stack == []

  def reset_to(self, screen):
      self.stack = [screen]  # Replaces the whole stack with just this screen

  def __len__(self): 
    return len(self.stack) 

  def push(self,item): 
    self.stack.append(item)

  def peek(self):
        if self.stack:
            return self.stack[-1]
        return None

  def pop(self): 
    if len(self) == 0: 
      raise Exception("pop() called on empty stack.") 
    return self.stack.pop()

  def __str__(self): 
    return str(self.stack) 

class Screen: # Basic screen class to hold basic screen information that can be overwritten by subclasses
  def __init__(self, screen_stack):
    self.screen_stack = screen_stack # Reference to push/pop other screens
    self.buttons = [] # Shared button container

  def handle_input(self):
  # Default input handling for buttons
    for button in self.buttons:
      button.is_clicked()

  def update(self):
  # Overridden by subclasses if they need active logic.
    pass

  def render(self):
  # Render shared UI elements or base background
    for button in self.buttons:
      button.draw()

class Button: # Basic reusable button class
    def __init__(self, text, action, x, y, width, height):
        self.text = text
        self.action = action  # This is the lambda function!
        self.rec = rl.Rectangle(x, y, width, height)
        
    def draw(self):
        # Draw the button rectangle using Raylib
        rl.draw_rectangle_rec(self.rec, rl.LIGHTGRAY)
        rl.draw_rectangle_lines_ex(self.rec, 2, rl.DARKGRAY)
        
        # Draw the text centered on the button
        rl.draw_text(self.text, int(self.rec.x + 20), int(self.rec.y + 15), 20, rl.BLACK)
        
    def is_clicked(self):
        # Check if the mouse is hovering and the left click is pressed
        mouse_pos = rl.get_mouse_position()
        if rl.check_collision_point_rec(mouse_pos, self.rec):
            if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
                self.action()  # Run the lambda action!
                return True
        return False

class TitleScreen(Screen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack) # Enables inheritence from Screen
        start_btn = Button("Start Game", lambda: screen_stack.push(GameScreen(screen_stack)), 300, 200, 200, 50)
        upgrade_btn = Button("Upgrades", lambda: screen_stack.push(UpgradeScreen(screen_stack)), 300, 275, 200, 50)
        options_btn = Button("Options", lambda: screen_stack.push(OptionsScreen(screen_stack)), 300, 350, 200, 50)
        quit_btn = Button("Quit Game", lambda: exit(), 300, 425, 200, 50)
        
        
        self.buttons = [start_btn, quit_btn, upgrade_btn, options_btn]


    def render(self):
        # 1. Draw vertical gradient background from Green to Light Green
        rl.draw_rectangle_gradient_v(
            0, 0, 
            rl.get_screen_width(), rl.get_screen_height(), 
            rl.DARKGREEN, rl.BROWN
        )
        
        # 2. Draw title text on top of the background
        rl.draw_text("Bug Game", 280, 100, 30, rl.GREEN)
        
        # 3. Call super().render() to draw the buttons on top of everything else
        super().render()

class PauseScreen(Screen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack)
        button_width = 220
        button_x = (rl.get_screen_width() - button_width) // 2
        panel_y = (rl.get_screen_height() - 300) // 2
        button_y = panel_y + 85
        resume_btn = Button("Resume Game", screen_stack.pop, button_x, button_y, button_width, 46)
        menu_btn = Button(
            "Main Menu",
            lambda: screen_stack.reset_to(TitleScreen(screen_stack)),
            button_x,
            button_y + 60,
            button_width,
            46,
        )
        upgrade_btn = Button(
            "Upgrades",
            lambda: screen_stack.push(UpgradeScreen(screen_stack)),
            button_x,
            button_y + 120,
            button_width,
            46,
        )

        self.buttons = [resume_btn, menu_btn, upgrade_btn]

    def render(self):
        if len(self.screen_stack) > 1:
            self.screen_stack.stack[-2].render()

        screen_width = rl.get_screen_width()
        screen_height = rl.get_screen_height()
        rl.draw_rectangle(
            0,
            0,
            screen_width,
            screen_height,
            rl.Color(0, 0, 0, 160),
        )

        panel = rl.Rectangle(
            (screen_width - 300) / 2,
            (screen_height - 300) / 2,
            300,
            300,
        )
        rl.draw_rectangle_rec(panel, rl.Color(45, 45, 45, 245))
        rl.draw_rectangle_lines_ex(panel, 2, rl.LIGHTGRAY)

        title = "Paused"
        title_x = (screen_width - rl.measure_text(title, 30)) // 2
        rl.draw_text(title, title_x, int(panel.y + 26), 30, rl.WHITE)
        super().render()

class GameOverScreen(Screen):
    def __init__(
        self, screen_stack, message, on_restart, rounds_survived, food_collected
    ):
        super().__init__(screen_stack)
        self.message = message
        self.rounds_survived = rounds_survived
        self.food_collected = food_collected

        def play_again():
            screen_stack.pop()   # remove this screen, revealing the game
            on_restart()         # then reset the round

        self.buttons = [
            Button("Play Again", play_again, 300, 250, 200, 50),
            Button(" Return to Menu",
                   lambda: screen_stack.reset_to(TitleScreen(screen_stack)),
                   300, 325, 200, 50),
        ]

    def render(self):
        rl.draw_rectangle_gradient_v(
            0, 0, rl.get_screen_width(), rl.get_screen_height(),
            rl.DARKGREEN, rl.BROWN,
        )
        width = rl.measure_text(self.message, 40)
        rl.draw_text(self.message, 400 - width // 2, 140, 40, rl.WHITE)
        rounds_text = f"Rounds survived: {self.rounds_survived}"
        rounds_width = rl.measure_text(rounds_text, 24)
        rl.draw_text(rounds_text, 400 - rounds_width // 2, 190, 24, rl.WHITE)
        food_text = f"Food collected: {self.food_collected}"
        food_width = rl.measure_text(food_text, 24)
        rl.draw_text(food_text, 400 - food_width // 2, 220, 24, rl.YELLOW)
        super().render()

class OptionsScreen(Screen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack) # Enables inheritence from Screen
        start_btn = Button("Start Game", lambda: screen_stack.push(GameScreen(screen_stack)), 300, 200, 200, 50)
        menu_btn = Button("Return to Menu", lambda: screen_stack.reset_to(TitleScreen(screen_stack)), 300, 275, 200, 50)
        # will need to improve functionality to return to PauseScreen if selected from there, but this is fine for now.
        upgrade_btn = Button("Upgrades", lambda: screen_stack.push(UpgradeScreen(screen_stack)), 300, 350, 200, 50)
        
        self.buttons = [start_btn, menu_btn]


    def render(self):
        # 1. Draw vertical gradient background from Green to Light Green
        rl.draw_rectangle_gradient_v(
            0, 0, 
            rl.get_screen_width(), rl.get_screen_height(), 
            rl.DARKGREEN, rl.BROWN
        )
        
        # 2. Draw title text on top of the background
        rl.draw_text("Options Menu", 280, 100, 30, rl.GREEN)
        
        # 3. Call super().render() to draw the buttons on top of everything else
        super().render()
    # Add function(s) for options and retaining their changes here

class GameScreen(Screen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack) # Enables inheritence from Screen
        pause_btn = Button("||", lambda: screen_stack.push(PauseScreen(screen_stack)), 10, 540, 50, 40)
        
        self.buttons = [pause_btn]


    def render(self):
        # 1. Draw vertical gradient background from Green to Light Green
        rl.draw_rectangle_gradient_v(
            0, 0, 
            rl.get_screen_width(), rl.get_screen_height(), 
            rl.DARKGREEN, rl.BROWN
        )
        
        # 2. Draw title text on top of the background
        rl.draw_text("Game Screen", 280, 100, 30, rl.GREEN)
        
        # 3. Call super().render() to draw the buttons on top of everything else
        super().render()

    # I'm not sure if it would be a seperate function or in the render function, but we can connect Gavin's world logic (from world.py) here.

class UpgradeScreen(Screen):
    def __init__(self, screen_stack):
        super().__init__(screen_stack) # Enables inheritence from Screen
        start_btn = Button("Start Game", lambda: screen_stack.push(GameScreen(screen_stack)), 300, 200, 200, 50)
        upgrade_btn = Button("Upgrades", lambda: screen_stack.push(UpgradeScreen(screen_stack)), 300, 275, 200, 50)
        options_btn = Button("Options", lambda: screen_stack.push(OptionsScreen(screen_stack)), 300, 350, 200, 50)
        menu_btn = Button("Return to Menu", lambda: screen_stack.reset_to(TitleScreen(screen_stack)), 300, 425, 200, 50)
         
        self.buttons = [start_btn, menu_btn, upgrade_btn, options_btn]


    def render(self):
        # 1. Draw vertical gradient background from Green to Light Green
        rl.draw_rectangle_gradient_v(
            0, 0, 
            rl.get_screen_width(), rl.get_screen_height(), 
            rl.DARKGREEN, rl.BROWN
        )
        
        # 2. Draw title text on top of the background
        rl.draw_text("Upgrades", 280, 100, 30, rl.GREEN)
        
        # 3. Call super().render() to draw the buttons on top of everything else
        super().render()

    # Add method for implimenting upgrade tree and buttons here
