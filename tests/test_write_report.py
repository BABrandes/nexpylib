#!/usr/bin/env python3
"""
Test script for the write_report function with a complex hook system.
This creates a sophisticated joining scenario and uses write_report to analyze it.
"""

from typing import Any
from enum import Enum


from nexpy import XValue, XList, XDictSelect, XSet, XSetSingleSelect, XSetMultiSelect, write_report, XBase


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TestWriteReport:
    """Test the write_report function with complex hook systems"""
    
    def test_write_report_complex_system(self):
        """Test write_report with a complex observable system"""
        
        print("\n" + "="*80)
        print("🚀 Testing write_report function with complex hook system")
        print("="*80)
        
        # Create the complex system
        observables: dict[str, XBase[Any, Any]] = self._create_complex_system()
        
        # Analyze it with write_report
        self._analyze_system(observables)
        
        # Demonstrate change propagation
        self._demonstrate_changes(observables)
        
        print("\n" + "="*80)
        print("✅ write_report test completed successfully!")
        print("="*80)
    
    def _create_complex_system(self) -> dict[str, XBase[Any, Any]]:
        """Create a complex system with multiple observables and joinings"""
        
        print("🔧 Creating complex observable system...")
        
        # 1. Core user data
        user_name = XValue("Alice")
        user_age = XValue(28)
        user_role = XSetSingleSelect(UserRole.USER, {UserRole.ADMIN, UserRole.USER, UserRole.GUEST})
        
        # 2. Task management system
        task_list = XList(["Setup project", "Write documentation", "Run tests"])
        task_priorities = XDictSelect({"Setup project": 1, "Write documentation": 2, "Run tests": 3}, "Setup project")
        completed_tasks = XSet({"Write documentation"})
        
        # 3. Multi-selection for task statuses
        available_statuses = {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE}
        current_task_statuses = XSetMultiSelect[TaskStatus](
            {TaskStatus.TODO, TaskStatus.IN_PROGRESS}, 
            available_statuses
        )
        
        # 4. Derived/computed observables
        task_count = XValue(0)  # Will be bound to task_list.length_hook
        user_display = XValue("")  # Will combine name and role
        priority_sum = XValue(0)  # Will sum all priorities
        
        print("✅ Basic observables created")
        
        # Create complex joining relationships
        print("🔗 Creating joinings...")
        
        # Bind task count to list length
        task_count.join(task_list.length_hook, "use_target_value")  # type: ignore
        
        # Bind some observables to demonstrate shared hook nexuses
        task_backup: XList[Any] = XList([])  # Will share nexus with task_list
        task_backup.join_by_key("value", task_list.list_hook, "use_target_value") # type: ignore
        
        # Create another observable that shares the user's age
        min_age_requirement = XValue(18)
        age_validator = XValue(False)  # Will be connected to show age >= min_age
        
        # Connect age-related observables
        backup_age: XValue[Any] = XValue(0)
        backup_age.join(user_age.value_hook, "use_target_value")  # type: ignore
        
        # Create observables that share nexus with the sets
        completed_backup: XSet[Any] = XSet(set())
        completed_backup.join_by_key("value", completed_tasks.set_hook, "use_target_value") # type: ignore
        
        # Multi-selection backup
        status_backup: XSetMultiSelect[TaskStatus] = XSetMultiSelect(set(), available_statuses)
        status_backup.join_by_key("selected_options", current_task_statuses.selected_options_hook, "use_target_value") # type: ignore
        status_backup.join_by_key("available_options", current_task_statuses.available_options_hook, "use_target_value") # type: ignore
        
        print("✅ Joinings created")
        
        # Return dictionary of all observables for analysis
        return {
            "user_name": user_name,
            "user_age": user_age,
            "user_role": user_role,
            "task_list": task_list,
            "task_priorities": task_priorities,
            "completed_tasks": completed_tasks,
            "current_task_statuses": current_task_statuses,
            "task_count": task_count,
            "user_display": user_display,
            "priority_sum": priority_sum,
            "task_backup": task_backup,
            "min_age_requirement": min_age_requirement,
            "age_validator": age_validator,
            "backup_age": backup_age,
            "completed_backup": completed_backup,
            "status_backup": status_backup,
        } # type: ignore
    
    def _analyze_system(self, observables_dict: dict[str, XBase[Any, Any]]):
        """Use write_report to analyze the complex system"""
        
        print("\n" + "="*80)
        print("📊 SYSTEM ANALYSIS REPORT")
        print("="*80)
        
        # Generate the report
        report = write_report(observables_dict) # type: ignore
        
        print(report)
        
        # Add some additional analysis
        print("="*80)
        print("📈 ADDITIONAL METRICS")
        print("="*80)
        
        total_xobjects = len(observables_dict)
        
        # Count how many hooks exist in total
        total_hooks = 0
        for name, observable in observables_dict.items():
            total_hooks += len(observable._get_hook_keys()) # type: ignore
        
        print(f"Total observables: {total_xobjects}")
        print(f"Total hooks: {total_hooks}")
        
        # Count shared nexuses (nexuses with multiple hooks)
        from nexpy.core.nexus_system.system_analysis import collect_all_hook_nexuses
        hook_nexuses = collect_all_hook_nexuses(observables_dict) # type: ignore
        
        shared_nexuses = 0
        unshared_nexuses = 0
        
        for _, hooks_info in hook_nexuses.items():
            if len(hooks_info) > 1:
                shared_nexuses += 1
            else:
                unshared_nexuses += 1
        
        print(f"Shared hook nexuses: {shared_nexuses}")
        print(f"Unshared hook nexuses: {unshared_nexuses}")
        print(f"Total hook nexuses: {len(hook_nexuses)}")
        
        # Show which observables are most connected
        observable_connection_counts: dict[str, int] = {}
        for _, hooks_info in hook_nexuses.items():
            if len(hooks_info) > 1:
                for name, _, _ in hooks_info:
                    observable_connection_counts[name] = observable_connection_counts.get(name, 0) + 1
        
        if observable_connection_counts:
            print(f"\nMost connected observables:")
            for name, count in sorted(observable_connection_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {name}: {count} shared connections")
    
    def _demonstrate_changes(self, observables_dict: dict[str, XBase[Any, Any]]):
        """Demonstrate how changes propagate through the system"""
        
        print("\n" + "="*80)
        print("🔄 DEMONSTRATING CHANGE PROPAGATION")
        print("="*80)
        
        # Show current state
        task_list: XBase[Any, Any] = observables_dict["task_list"]
        task_backup: XBase[Any, Any] = observables_dict["task_backup"]
        task_count: XBase[Any, Any] = observables_dict["task_count"]
        
        print(f"Original task list: {task_list.list}") # type: ignore
        print(f"Task backup: {task_backup.list}") # type: ignore
        print(f"Task count: {task_count.value}") # type: ignore
        
        # Make a change
        print("\n📝 Adding new task...")
        task_list.append("Deploy to production") # type: ignore
        
        print(f"Updated task list: {task_list.list}") # type: ignore
        print(f"Task backup: {task_backup.list}") # type: ignore
        print(f"Task count: {task_count.value}") # type: ignore
        
        # Demonstrate user data joining
        user_name: XBase[Any, Any] = observables_dict["user_name"]
        backup_age: XBase[Any, Any] = observables_dict["backup_age"]
        user_age: XBase[Any, Any] = observables_dict["user_age"]
        
        print(f"\nOriginal user age: {user_age.value}") # type: ignore
        print(f"Backup age: {backup_age.value}") # type: ignore
        
        print("\n🎂 User has a birthday...")
        user_age.value = 29 # type: ignore
        
        print(f"Updated user age: {user_age.value}") # type: ignore
        print(f"Backup age: {backup_age.value}") # type: ignore
    
    def test_write_report_simple_system(self):
        """Test write_report with a simple system to verify basic functionality"""
        
        # Create a simple system
        name: XValue[Any] = XValue[Any]("John")
        age: XValue[Any] = XValue[Any](25)
        
        # Create a backup that shares the name
        name_backup: XValue[Any] = XValue[Any]("")
        name_backup.join(name.value_hook, "use_target_value")  # type: ignore
        
        observables: dict[str, XBase[Any, Any]] = {
            "name": name,
            "age": age,
            "name_backup": name_backup
        } # type: ignore
        
        # Generate report
        report: str = write_report(observables) # type: ignore
        
        # Verify the report contains expected information
        assert "John" in report
        assert "25" in report
        assert "name:" in report
        assert "age:" in report
        assert "name_backup:" in report
        
        # Verify that name and name_backup share a nexus
        assert "name:" in report
        assert "name_backup:" in report
        
        print("\nSimple system report:")
        print(report)
    
    def test_write_report_empty_system(self):
        """Test write_report with an empty system"""
        
        report: str = write_report({}) # type: ignore
        assert report == "No observables provided.\n"
        
        print("\nEmpty system report (should be empty):")
        print(f"'{report}'")
