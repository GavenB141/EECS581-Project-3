'''
Author: Jocelyn Miller
KUID: 3090871
Class Name: Stack
Last Modified: 11.5.26
Modification: Began implimentation of Stack Class
Purpose of Class: To implement a stack data structure with push, pop, and peek operations
'''


class Stack: 
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

