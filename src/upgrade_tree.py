'''
Name: upgrade_tree.py
Description: Upgrade Tree
Author: Ashton Spencer
Last Modified: 11.15.2026
'''

class upgrade:
    def __init__(self, name, max_level, base_cost, cost_multiplier, parent):
        self.name = name
        self.max_level = max_level
        self.base_cost = base_cost
        self.cost_multiplier = cost_multiplier
        self.parent = parent
        self.children = []
        self.level = 0

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def is_maxed(self):
        return self.level >= self.max_level

    def is_unlocked(self):
        return self.parent is None or self.parent.level > 0

    def get_cost(self):
        return int(round(self.base_cost * self.cost_multiplier ** self.level))

    def can_purchase(self, currency):
        return(self.is_unlocked and not self.is_maxed() and currency >= self.get_cost())

    def purchase(self, currency):
        if not self.can_purchase(currency):
            return False, currency
        cost = self.get_cost()
        self.level += 1
        return True, currency - cost

    
class upgrade_tree:
    def __init__(self):
        self.root = None

    def build_tree(self):
        root = upgrade("Attack Speed", 3, 10, 1.2, None)
        self.root = root
        damage = root.add_child(upgrade("Damage", 5, 15, 1.3, root))
        damage.add_child(upgrade("Attack Range", 3, 20, 1.3, damage))
        root.add_child(upgrade("Swarm Speed", 3, 15, 1.2, root))
        root.add_child(upgrade("Max Health", 5, 12, 1.25, root))
