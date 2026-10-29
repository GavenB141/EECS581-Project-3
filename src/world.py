'''
Name: world.py
Description: Implementation of the Entity-Component-System (ECS) pattern.
Author: Gaven Behrends
Created: 10.27.2026
Revised: 10.29.2026 - typing considerations and documentation before push
'''

from abc import ABC, abstractmethod


class Entity(int):
    """
    An alias for the int type representing an entity ID.
    May be held as a reference to a specific entity, with the caveat
    that entities may be deleted and have their ID reused by a new one.
    If this becomes a problem a generation field may be added.
    """
    pass


class World:
    """
    Holds a table of components belonging to entities and a schedule
    of systems to run for processing entity behaviors.
    """

    def __init__(self):
        self._component_table: dict[type, list[object | None]] = {}
        self._table_width: int = 0
        self._unused_entities: list[Entity] = []
        self._systems: list[System] = []

    def register_system(self, system: System):
        """Add a system to the world.

        Args:
            system: The system to register.
        """
        self._systems.append(system)

    def update(self, dt: float):
        """Run all systems in registration order.
        
        Args:
            dt: The time in seconds systems should simulate for.
        """
        for system in self._systems:
            system.run(self, dt)

    def create_entity(self) -> Entity:
        """Add a blank entity to the world.

        Returns:
            Entity: The integer ID representing the new entity.
        """
        if len(self._unused_entities) > 0:
            return self._unused_entities.pop()
        else:
            id = self._table_width
            self._table_width += 1
            for _, row in self._component_table.items():
                row.append(None)
            return Entity(id)

    def delete_entity(self, entity: Entity):
        """Delete an entity from the world.

        Args:
            entity: The entity to delete.
        """
        if entity > self._table_width or entity in self._unused_entities:
            return
        for _, row in self._component_table.items():
            if entity < len(row):
                row[entity] = None
        self._unused_entities.append(entity)

    def add(self, entity: Entity, component: object):
        """Add a component to an entity.

        Args:
            entity: The ID of the entity to receive the component.
            component: The initialized component object to add.
                An entity may only have one component of any specific type.
                If the entity already has one, it will be replaced.
        """
        if entity >= self._table_width or entity in self._unused_entities:
            raise Exception("Invalid entity ID " + str(entity))

        if type(component) not in self._component_table:
            self._component_table[type(component)] = [None] * self._table_width

        self._component_table[type(component)][entity] = component

    def get(self, entity: Entity, component_type: type) -> object | None:
        """Retrieve a component from an entity.
        
        Args:
            entity: The ID of the entity to read.
            component_type: The type of component to retrieve.

        Returns:
            The requested component object, or None if the entity doesn't
            have the component.
        """
        if entity >= self._table_width or entity in self._unused_entities:
            raise Exception("Invalid entity ID " + str(entity))

        if component_type not in self._component_table:
            return None

        return self._component_table[component_type][entity]

    def query(self, *args: type):
        """A generator function to find entities possessing certain components.

        Args:
            *args: Any number of component types to query for.
                The Entity type may also be passed to get the IDs of matches.

        Yields:
            A tuple containing the requested components for each match.

        Example:
            for e, foo, bar, baz in world.query(Entity, Foo, Bar, Baz):
                # do something with the components
                ... 
        """
        for i in range(0, self._table_width):
            if i in self._unused_entities:
                continue
            output_tuple = ()
            for component_type in args:
                # Allow the Entity type to be used as a component to retrieve entity ID
                if component_type == Entity:
                    output_tuple += (i,)
                    continue
                if component_type not in self._component_table:
                    return None
                component = self._component_table[component_type][i]
                if component is None:
                    break
                output_tuple += (component,)
            if len(output_tuple) == len(args):
                yield output_tuple


class System(ABC):
    """
    Abstract base class to extend when authoring systems.
    The run method defines the behavior of the system, and should use the
    world.query method to find the entities the system concerns.
    """

    @abstractmethod
    def run(self, world: World, dt: float):
        pass
