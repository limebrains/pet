__all__ = [
    'PetException', 'NameNotFound', 'NameAlreadyTaken', 'ProjectActivated'
]


class PetException(Exception):
    """
    Base class for exceptions raised by PET
    """


class NameNotFound(PetException):
    """
    Error raised when given name wasn't recognized
    """


class NameAlreadyTaken(PetException):
    """
    Error raised when name is already occupied by something
    """


class ProjectActivated(PetException):
    """
    Error raised when _lock file exists in project directory
    - meaning project is active
    """
