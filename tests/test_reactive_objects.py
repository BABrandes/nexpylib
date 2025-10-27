"""
Comprehensive tests for reactive X objects (XValue, XList, XDict, XSet, selection objects).

Based on documentation and API reference.
"""

import pytest
import nexpy as nx
from test_base import ObservableTestCase


class TestXValue(ObservableTestCase):
    """Test XValue reactive wrapper."""
    
    def test_xvalue_creation(self):
        """Test creating XValue with different types."""
        int_val = nx.XValue(42)
        assert int_val.value == 42
        
        float_val = nx.XValue(3.14)
        assert float_val.value == 3.14
        
        str_val = nx.XValue("hello")
        assert str_val.value == "hello"
        
        list_val = nx.XValue([1, 2, 3])
        assert list_val.value == [1, 2, 3]
    
    def test_xvalue_with_validation(self):
        """Test XValue with custom validation."""
        def validate_positive(value: int) -> tuple[bool, str]:
            if value > 0:
                return True, "Valid"
            return False, "Must be positive"
        
        val = nx.XValue(10, validate_value_callback=validate_positive)
        
        val.value = 20  # OK
        assert val.value == 20
        
        with pytest.raises(Exception):
            val.value = -5
    
    def test_xvalue_change_value_method(self):
        """Test change_value method (lambda-friendly)."""
        val = nx.XValue(10)
        
        success, _ = val.change_value(20, raise_submission_error_flag=False)
        assert success
        assert val.value == 20
    
    def test_xvalue_hook_access(self):
        """Test accessing underlying hook."""
        val = nx.XValue(42)
        hook = val.value_hook
        
        assert hook.value == 42
        
        hook.value = 100
        assert val.value == 100
    
    def test_xvalue_comparison_operators(self):
        """Test comparison operator overloading."""
        x = nx.XValue(10)
        y = nx.XValue(20)
        
        assert x < y
        assert not (x > y)
        assert x <= y
        assert y >= x
        assert x != y  # Object identity, not value
    
    def test_xvalue_arithmetic_operators(self):
        """Test arithmetic operator support."""
        x = nx.XValue(10)
        
        assert int(x) == 10
        assert float(x) == 10.0
        assert abs(nx.XValue(-5)) == 5


class TestXList(ObservableTestCase):
    """Test XList reactive list."""
    
    def test_xlist_creation(self):
        """Test creating XList."""
        lst = nx.XList([1, 2, 3])
        assert lst.list == [1, 2, 3]
        assert lst.length == 3
    
    def test_xlist_append(self):
        """Test append operation."""
        lst = nx.XList([1, 2])
        lst.append(3)
        
        assert lst.list == [1, 2, 3]
        assert lst.length == 3
    
    def test_xlist_extend(self):
        """Test extend operation."""
        lst = nx.XList([1, 2])
        lst.extend([3, 4, 5])
        
        assert lst.list == [1, 2, 3, 4, 5]
        assert lst.length == 5
    
    def test_xlist_insert(self):
        """Test insert operation."""
        lst = nx.XList([1, 3])
        lst.insert(1, 2)
        
        assert lst.list == [1, 2, 3]
    
    def test_xlist_remove(self):
        """Test remove operation."""
        lst = nx.XList([1, 2, 3, 2])
        lst.remove(2)  # Removes first occurrence
        
        assert lst.list == [1, 3, 2]
    
    def test_xlist_pop(self):
        """Test pop operation."""
        lst = nx.XList([1, 2, 3])
        val = lst.pop()
        
        assert val == 3
        assert lst.list == [1, 2]
        
        val = lst.pop(0)
        assert val == 1
        assert lst.list == [2]
    
    def test_xlist_clear(self):
        """Test clear operation."""
        lst = nx.XList([1, 2, 3])
        lst.clear()
        
        assert lst.list == []
        assert lst.length == 0
    
    def test_xlist_direct_assignment(self):
        """Test direct list assignment."""
        lst = nx.XList([1, 2, 3])
        lst.list = [10, 20]
        
        assert lst.list == [10, 20]
        assert lst.length == 2
    
    def test_xlist_length_sync(self):
        """Test that length stays synchronized."""
        lst = nx.XList([1, 2, 3])
        
        lst.append(4)
        assert lst.length == 4
        
        lst.pop()
        assert lst.length == 3
        
        lst.list = [1]
        assert lst.length == 1


class TestXSet(ObservableTestCase):
    """Test XSet reactive set."""
    
    def test_xset_creation(self):
        """Test creating XSet."""
        s = nx.XSet({1, 2, 3})
        assert s.set == {1, 2, 3}
    
    def test_xset_add(self):
        """Test add operation."""
        s = nx.XSet({1, 2})
        s.add(3)
        
        assert 3 in s.set
    
    def test_xset_remove(self):
        """Test remove operation."""
        s = nx.XSet({1, 2, 3})
        s.remove(2)
        
        assert 2 not in s.set
        assert s.set == {1, 3}
    
    def test_xset_discard(self):
        """Test discard operation (no error if not present)."""
        s = nx.XSet({1, 2, 3})
        s.discard(2)
        assert 2 not in s.set
        
        s.discard(99)  # Should not raise error
    
    def test_xset_clear(self):
        """Test clear operation."""
        s = nx.XSet({1, 2, 3})
        s.clear()
        
        assert s.set == set()
    
    def test_xset_operations(self):
        """Test set operations."""
        s1 = nx.XSet({1, 2, 3})
        s2 = nx.XSet({2, 3, 4})
        
        # Union
        union = s1.set | s2.set
        assert union == {1, 2, 3, 4}
        
        # Intersection
        intersection = s1.set & s2.set
        assert intersection == {2, 3}


class TestXDict(ObservableTestCase):
    """Test XDict reactive dictionary."""
    
    def test_xdict_creation(self):
        """Test creating XDict."""
        d = nx.XDict({"a": 1, "b": 2})
        assert d.dict == {"a": 1, "b": 2}
    
    def test_xdict_getitem(self):
        """Test dictionary access."""
        d = nx.XDict({"a": 1, "b": 2})
        assert d["a"] == 1
        assert d["b"] == 2
    
    def test_xdict_setitem(self):
        """Test dictionary assignment."""
        d = nx.XDict({"a": 1})
        d["b"] = 2
        
        assert d.dict == {"a": 1, "b": 2}
        
        d["a"] = 10
        assert d.dict == {"a": 10, "b": 2}
    
    def test_xdict_delitem(self):
        """Test dictionary deletion."""
        d = nx.XDict({"a": 1, "b": 2, "c": 3})
        del d["b"]
        
        assert d.dict == {"a": 1, "c": 3}
    
    def test_xdict_get(self):
        """Test get method with default."""
        d = nx.XDict({"a": 1})
        
        # XDict doesn't have .get() - use dict property or [] operator
        assert d.dict.get("a") == 1
        assert d.dict.get("b") is None
        assert d.dict.get("b", 99) == 99
    
    def test_xdict_clear(self):
        """Test clear operation."""
        d = nx.XDict({"a": 1, "b": 2})
        d.clear()
        
        assert d.dict == {}


class TestXDictSelect(ObservableTestCase):
    """Test XDictSelect with internal synchronization."""
    
    def test_xdict_select_creation(self):
        """Test creating XDictSelect."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        assert dict(select.dict_hook.value) == {"a": 1, "b": 2}
        assert select.key == "a"
        assert select.value == 1
    
    def test_xdict_select_key_change(self):
        """Test that changing key updates value."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2, "c": 3},
            key_hook="a",
            value_hook=None
        )
        
        select.change_key("b")
        assert select.value == 2
        
        select.change_key("c")
        assert select.value == 3
    
    def test_xdict_select_value_change(self):
        """Test that changing value updates dict."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        select.change_value(10)
        assert select.dict_hook.value["a"] == 10
    
    def test_xdict_select_dict_change(self):
        """Test that changing dict updates value."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        select.change_dict({"a": 100, "b": 200})
        assert select.value == 100
    
    def test_xdict_select_change_dict_and_key(self):
        """Test atomic dict and key change."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        select.change_dict_and_key({"x": 10, "y": 20}, "x")
        assert dict(select.dict_hook.value) == {"x": 10, "y": 20}
        assert select.key == "x"
        assert select.value == 10
    
    def test_xdict_select_invariant_key_in_dict(self):
        """Test that key must always be in dict."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        with pytest.raises(Exception):  # Could be KeyError or SubmissionError
            select.change_key("z")  # Key not in dict
    
    def test_xdict_select_invariant_value_consistency(self):
        """Test that value always equals dict[key]."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        # After any operation, invariant must hold
        select.change_key("b")
        assert select.value == select.dict_hook.value[select.key]
        
        select.change_value(20)
        assert select.value == select.dict_hook.value[select.key]
    
    def test_xdict_select_multiple_hooks(self):
        """Test that XDictSelect exposes multiple hooks."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        
        # All hooks accessible
        assert hasattr(select, 'dict_hook')
        assert hasattr(select, 'key_hook')
        assert hasattr(select, 'value_hook')


class TestXSetSingleSelect(ObservableTestCase):
    """Test XSetSingleSelect selection from set."""
    
    def test_xset_select_creation(self):
        """Test creating XSetSingleSelect."""
        select = nx.XSetSingleSelect(
            selected_option=3,
            available_options={1, 2, 3, 4, 5}
        )
        
        assert select.available_options == {1, 2, 3, 4, 5}
        assert select.selected_option == 3
    
    def test_xset_select_change_selection(self):
        """Test changing selection."""
        select = nx.XSetSingleSelect(
            selected_option=1,
            available_options={1, 2, 3}
        )
        
        select.change_selected_option(2)
        assert select.selected_option == 2
        
        select.change_selected_option(3)
        assert select.selected_option == 3
    
    def test_xset_select_invariant(self):
        """Test that selection must be in set."""
        select = nx.XSetSingleSelect(
            selected_option=1,
            available_options={1, 2, 3}
        )
        
        with pytest.raises(Exception):  # Could be ValueError or SubmissionError
            select.change_selected_option(99)  # Not in set


class TestXSetMultiSelect(ObservableTestCase):
    """Test XSetMultiSelect for multiple selection."""
    
    def test_xset_multi_select_creation(self):
        """Test creating XSetMultiSelect."""
        select = nx.XSetMultiSelect(
            selected_options={"a", "c"},
            available_options={"a", "b", "c", "d"}
        )
        
        assert select.available_options == {"a", "b", "c", "d"}
        assert select.selected_options == {"a", "c"}
    
    def test_xset_multi_select_add(self):
        """Test adding to selection."""
        select = nx.XSetMultiSelect(
            selected_options={"a"},
            available_options={"a", "b", "c"}
        )
        
        select.add_selected_option("b")
        assert "b" in select.selected_options
    
    def test_xset_multi_select_remove(self):
        """Test removing from selection."""
        select = nx.XSetMultiSelect(
            selected_options={"a", "b"},
            available_options={"a", "b", "c"}
        )
        
        select.remove_selected_option("a")
        assert "a" not in select.selected_options
        assert select.selected_options == {"b"}
    
    def test_xset_multi_select_invariant(self):
        """Test that selection must be subset of universe."""
        select = nx.XSetMultiSelect(
            selected_options={"a"},
            available_options={"a", "b", "c"}
        )
        
        with pytest.raises(Exception):  # ValueError or SubmissionError
            select.change_selected_options({"a", "z"})  # "z" not in available options


class TestValidationIntegration(ObservableTestCase):
    """Test validation across different X objects."""
    
    def test_validation_in_xvalue(self):
        """Test XValue validation."""
        def validate_even(value: int) -> tuple[bool, str]:
            if value % 2 == 0:
                return True, "Valid"
            return False, "Must be even"
        
        val = nx.XValue(2, validate_value_callback=validate_even)
        
        val.value = 4  # OK
        assert val.value == 4
        
        with pytest.raises(Exception):
            val.value = 3  # Odd
    
    def test_validation_with_joined_xvalues(self):
        """Test validation when XValues are joined."""
        def validate_positive(value: int) -> tuple[bool, str]:
            if value > 0:
                return True, "Valid"
            return False, "Must be positive"
        
        val1 = nx.XValue(10, validate_value_callback=validate_positive)
        val2 = nx.XValue(20)
        
        val1.value_hook.join(val2.value_hook, "use_caller_value")
        
        # Both must pass validation
        val2.value = 30  # OK
        assert val1.value == 30
        
        with pytest.raises(Exception):
            val2.value = -5  # Fails val1's validation

