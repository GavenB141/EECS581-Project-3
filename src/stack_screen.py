'''
Author: Jocelyn Miller
KUID: 3090871
Class Name: Stack
Last Modified: 11.5.26
Modification: Began implimentation of Stack Class
Purpose of Class: To implement a stack data structure with push, pop, and peek operations
'''


class Stack: # Basic stack implementation using a list as the underlying data structure
  def __init__(self): 
    self.__index = []

    def is_empty(self):
        return self.__index == [] 

  def __len__(self): 
    return len(self.__index) 

  def push(self,item): 
    self.__index.insert(0,item) 

  def peek(self): 
    if len(self) == 0: 
      raise Exception("peek() called on empty stack.") 
    return self.__index[0] 

  def pop(self): 
    if len(self) == 0: 
      raise Exception("pop() called on empty stack.") 
    return self.__index.pop(0) 

  def __str__(self): 
    return str(self.__index) 

class Screen: # Basic screen class to hold basic screen information that can be overwritten by subclasses
  def _init__(self, screen_stack):
    self.screen_stack = screen_stack # Reference to push/pop other screens
    self.buttons = [] # Shared button container

  def handle_input(self, input):
  # Default input handling for buttons
    for button in self.buttons:
      if button.is_clicked(input):
        button.action()

  def update(self):
  # Overridden by subclasses if they need active logic.
    pass

  def render(self, canvas):
  # Render shared UI elements or base background
    for buttons in self.buttons:
      buttons.draw(canvas)

  
    

    