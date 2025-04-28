import unittest
from unittest.mock import Mock, MagicMock
from typing import Any, Type, List

# Define missing custom exceptions
class ReadOnlyError(Exception):
    """Raised when trying to modify a read-only property."""
    pass

class NotNullableError(Exception):
    """Raised when trying to set None to a non-nullable property."""
    pass

class ColumnProperty:
    """Represents a property (column) in a row with validation and change tracking."""
    def __init__(
        self,
        property_id: str,
        read_only: bool,
        read_only_change_allowed: bool,
        nullable: bool,
        default_value: Any,
        value_type: Type
    ):
        if not property_id:
            raise ValueError("Property ID cannot be None")
        if value_type is None:
            raise ValueError("Type cannot be None")
        
        self._property_id = property_id
        self._read_only = read_only
        self._read_only_change_allowed = read_only_change_allowed
        self._nullable = nullable
        self._value = default_value
        self._type = value_type
        self._modified = False
        self._owner = None

    def get_value(self) -> Any:
        return self._value

    def set_value(self, value: Any) -> None:
        if self._read_only:
            raise ReadOnlyError("Property is read-only")
        if not self._nullable and value is None:
            raise NotNullableError("Property is not nullable")
        if value is not None and not isinstance(value, self._type):
            raise TypeError(f"Value must be of type {self._type.__name__}")
        
        self._value = value
        self._modified = True
        if self._owner:
            self._owner.notify_change()

    def is_modified(self) -> bool:
        """Return whether the value was modified."""
        return self._modified

    def set_owner(self, owner):
        """Assigns an owner (row) to this property."""
        self._owner = owner

class RowItem:
    """Mock row item that owns properties and notifies the container when changed."""
    def __init__(self, container: Any, row_id: Any, properties: List[ColumnProperty]):
        self.container = container
        self.row_id = row_id
        self.properties = properties
        for prop in properties:
            prop.set_owner(self)
    
    def notify_change(self):
        self.container.item_change_notification(self)

class SQLContainer:
    """Mock SQL container for receiving change notifications."""
    def item_change_notification(self, item):
        pass

class TestColumnProperty(unittest.TestCase):
    """Unit tests for ColumnProperty behavior."""

    def setUp(self):
        self.container = MagicMock(spec=SQLContainer)
        self.row_id = Mock()

    def test_set_value_success(self):
        """Test setting a new value on a writable and nullable property."""
        cp = ColumnProperty('NAME', False, True, True, 'Ville', str)
        row_item = RowItem(self.container, self.row_id, [cp])

        cp.set_value('Kalle')

        self.assertEqual('Kalle', cp.get_value())
        self.container.item_change_notification.assert_called_once_with(row_item)

    def test_set_value_read_only_error(self):
        """Test setting a value on a read-only property raises an error."""
        cp = ColumnProperty('NAME', True, True, True, 'Ville', str)
        RowItem(self.container, self.row_id, [cp])

        with self.assertRaises(ReadOnlyError):
            cp.set_value('Kalle')

        self.container.item_change_notification.assert_not_called()

    def test_set_value_not_nullable_error(self):
        """Test setting None on a non-nullable property raises an error."""
        cp = ColumnProperty('NAME', False, True, False, 'Ville', str)
        RowItem(self.container, self.row_id, [cp])

        with self.assertRaises(NotNullableError):
            cp.set_value(None)

        self.container.item_change_notification.assert_not_called()

    def test_modified_flag_tracking(self):
        """Test that setting a value marks the property as modified."""
        cp = ColumnProperty('NAME', False, True, True, 'Ville', str)
        RowItem(self.container, self.row_id, [cp])

        self.assertFalse(cp.is_modified())

        cp.set_value('Kalle')

        self.assertTrue(cp.is_modified())
        self.container.item_change_notification.assert_called_once()

if __name__ == '__main__':
    unittest.main()
