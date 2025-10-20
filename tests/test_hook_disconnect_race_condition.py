"""
Test for the race condition in hook disconnect.

This test verifies that the fix for the "Hook was not found in its own hook nexus!"
error works correctly when disconnect() and join_by_key() are called concurrently.
"""

import threading
import time

from nexpy import FloatingHook

def test_disconnect_connect_race_condition():
    """
    Test that disconnect and connect operations don't cause race conditions.
    
    The bug was that _replace_nexus() didn't acquire the hook's lock,
    so it could replace self._hook_nexus while disconnect() was checking
    if self was in self._hook_nexus.hooks, causing a ValueError.
    """
    
    # Create three hooks
    hook1 = FloatingHook(1)
    hook2 = FloatingHook(2)
    hook3 = FloatingHook(3)
    
    # Connect hook1 and hook2
    hook1.join(hook2, "use_caller_value")
    
    # Verify they're connected
    assert hook1.is_joined_with(hook2)
    assert hook2.is_joined_with(hook1)
    assert hook1.value == 1
    assert hook2.value == 1
    
    errors: list[tuple[str, Exception]] = []
    
    def disconnect_hook1():
        """Thread 1: Disconnect hook1"""
        try:
            time.sleep(0.001)  # Small delay to increase chance of race
            hook1.isolate()
        except Exception as e:
            errors.append(("disconnect", e))
    
    def connect_hook1_hook3():
        """Thread 2: Connect hook1 to hook3"""
        try:
            # This will call _replace_nexus on hook1 and hook3
            hook1.join(hook3, "use_caller_value")
        except Exception as e:
            errors.append(("connect", e))
    
    # Run both operations concurrently multiple times to catch the race
    for i in range(50):
        # Reset the hooks
        hook1 = FloatingHook(1)
        hook2 = FloatingHook(2)
        hook3 = FloatingHook(3)
        hook1.join(hook2, "use_caller_value")
        
        errors.clear()
        
        # Start both threads
        t1 = threading.Thread(target=disconnect_hook1)
        t2 = threading.Thread(target=connect_hook1_hook3)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Check for errors
        if errors:
            for source, error in errors:
                print(f"Error in {source}: {error}")
            
            # If we got the specific race condition error, the test should fail
            for source, error in errors:
                if "Hook was not found in its own hook nexus" in str(error):
                    raise AssertionError(
                        f"Race condition detected on iteration {i}: {error}"
                    )
    
    print(f"Test passed: No race condition detected in 50 iterations")


def test_disconnect_replace_nexus_concurrent():
    """
    More targeted test: directly test concurrent disconnect and _replace_nexus.
    """
    
    errors: list[Exception] = []
    
    for iteration in range(100):
        hook1 = FloatingHook(1)
        hook2 = FloatingHook(2)
        
        # Connect them
        hook1.join(hook2, "use_caller_value")
        
        def thread_disconnect():
            try:
                hook1.isolate()
            except Exception as e:
                errors.append(e)
        
        def thread_replace():
            try:
                # Simulate what happens during connect_hooks
                from nexpy.core.nexus_system.nexus import Nexus
                new_nexus = Nexus(hook1.value, hooks={hook1})
                hook1._replace_nexus(new_nexus) # type: ignore
            except Exception as e:
                errors.append(e)
        
        t1 = threading.Thread(target=thread_disconnect)
        t2 = threading.Thread(target=thread_replace)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        if errors:
            for error in errors:
                if "Hook was not found in its own hook nexus" in str(error):
                    raise AssertionError(
                        f"Race condition on iteration {iteration}: {error}"
                    )
            errors.clear()
    
    print("Test passed: No race condition in 100 iterations of direct testing")


if __name__ == "__main__":
    test_disconnect_connect_race_condition()
    test_disconnect_replace_nexus_concurrent()
    print("\nAll race condition tests passed!")

