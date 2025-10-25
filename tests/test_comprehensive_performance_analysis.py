"""
Comprehensive performance analysis based on both hook count AND nexus count.

This test analyzes performance across different combinations of:
- Hook count (number of hooks)
- Nexus count (number of separate nexuses)
- Total operations (hooks × nexuses)

This will help determine optimal thresholds for adaptive submission.
"""

from typing import Any
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nexpy import FloatingHook
from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.internal_submit_methods.internal_submit_1 import internal_submit_values as internal_submit_1
from nexpy.core.nexus_system.internal_submit_methods.internal_submit_2 import internal_submit_values as internal_submit_2
from nexpy.core.nexus_system.internal_submit_methods.internal_submit_3 import internal_submit_values as internal_submit_3
from test_base import ObservableTestCase
from nexpy.core.nexus_system.nexus import Nexus


class TestComprehensivePerformanceAnalysis(ObservableTestCase):
    """Comprehensive performance analysis across hook and nexus dimensions."""
    
    def setup_method(self):
        super().setup_method()
        self.manager = NexusManager()
    
    def create_test_scenario(self, nexus_count: int, hooks_per_nexus: int) -> tuple[list[Nexus[Any]], list[FloatingHook[Any]]]:
        """Create a test scenario with specified nexus and hook counts."""
        nexuses: list[Nexus[Any]] = []
        all_hooks: list[FloatingHook[Any]] = []
        
        for nexus_idx in range(nexus_count):
            # Create hooks for this nexus
            nexus_hooks = [FloatingHook[int](nexus_idx * 100 + i) for i in range(hooks_per_nexus)]
            
            # Connect all hooks in this nexus together
            for i in range(1, len(nexus_hooks)):
                nexus_hooks[0].join(nexus_hooks[i], "use_caller_value")
            
            nexuses.append(nexus_hooks[0]._get_nexus()) # type: ignore
            all_hooks.extend(nexus_hooks)
        
        return nexuses, all_hooks
    
    def test_performance_matrix(self):
        """Test performance across a matrix of hook and nexus counts."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE PERFORMANCE MATRIX ANALYSIS")
        print("=" * 80)
        
        # Test scenarios: (nexus_count, hooks_per_nexus, description)
        test_scenarios = [
            # Small scenarios
            (1, 5, "1 nexus, 5 hooks"),
            (1, 10, "1 nexus, 10 hooks"),
            (1, 20, "1 nexus, 20 hooks"),
            (1, 50, "1 nexus, 50 hooks"),
            
            # Multiple nexuses, few hooks each
            (2, 5, "2 nexuses, 5 hooks each"),
            (5, 5, "5 nexuses, 5 hooks each"),
            (10, 5, "10 nexuses, 5 hooks each"),
            (20, 5, "20 nexuses, 5 hooks each"),
            
            # Medium scenarios
            (1, 100, "1 nexus, 100 hooks"),
            (2, 50, "2 nexuses, 50 hooks each"),
            (5, 20, "5 nexuses, 20 hooks each"),
            (10, 10, "10 nexuses, 10 hooks each"),
            
            # Large scenarios
            (1, 200, "1 nexus, 200 hooks"),
            (1, 500, "1 nexus, 500 hooks"),
            (2, 100, "2 nexuses, 100 hooks each"),
            (5, 50, "5 nexuses, 50 hooks each"),
            (10, 20, "10 nexuses, 20 hooks each"),
            
            # Very large scenarios
            (1, 1000, "1 nexus, 1000 hooks"),
            (2, 500, "2 nexuses, 500 hooks each"),
            (5, 200, "5 nexuses, 200 hooks each"),
            (10, 100, "10 nexuses, 100 hooks each"),
        ]
        
        results: list[dict[str, Any]] = []
        
        for nexus_count, hooks_per_nexus, description in test_scenarios:
            print(f"\nTesting: {description}")
            
            # Create test scenario
            nexuses, _ = self.create_test_scenario(nexus_count, hooks_per_nexus)
            
            # Calculate metrics
            total_hooks = nexus_count * hooks_per_nexus
            total_nexuses = nexus_count
            
            # Prepare submission data
            nexus_and_values_1 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            nexus_and_values_2 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            nexus_and_values_3 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            
            # Test Internal Submit 1
            start_time = time.perf_counter()
            success_1, _ = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
            time_1 = time.perf_counter() - start_time
            
            # Test Internal Submit 2
            start_time = time.perf_counter()
            success_2, _ = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
            time_2 = time.perf_counter() - start_time
            
            # Test Internal Submit 3
            start_time = time.perf_counter()
            success_3, _ = internal_submit_3(self.manager, nexus_and_values_3, "Normal submission")
            time_3 = time.perf_counter() - start_time
            
            # Calculate performance metrics
            speedup_2 = time_1 / time_2 if time_2 > 0 else float('inf')
            speedup_3 = time_1 / time_3 if time_3 > 0 else float('inf')
            speedup_3_vs_2 = time_2 / time_3 if time_3 > 0 else float('inf')
            
            # Determine winner
            fastest_time = min(time_1, time_2, time_3)
            if fastest_time == time_1:
                winner = "Submit 1"
            elif fastest_time == time_2:
                winner = "Submit 2"
            else:
                winner = "Submit 3"
            
            # Store results
            result: dict[str, Any] = {
                'nexus_count': nexus_count,
                'hooks_per_nexus': hooks_per_nexus,
                'total_hooks': total_hooks,
                'total_nexuses': total_nexuses,
                'description': description,
                'time_1': time_1,
                'time_2': time_2,
                'time_3': time_3,
                'speedup_2': speedup_2,
                'speedup_3': speedup_3,
                'speedup_3_vs_2': speedup_3_vs_2,
                'winner': winner,
                'success_1': success_1,
                'success_2': success_2,
                'success_3': success_3
            }
            results.append(result)
            
            print(f"  Total hooks: {total_hooks}, Total nexuses: {total_nexuses}")
            print(f"  Submit 1: {time_1:.6f}s")
            print(f"  Submit 2: {time_2:.6f}s")
            print(f"  Submit 3: {time_3:.6f}s")
            print(f"  Winner: {winner}")
            print(f"  Speedup (2 vs 1): {speedup_2:.2f}x")
            print(f"  Speedup (3 vs 1): {speedup_3:.2f}x")
            print(f"  Speedup (3 vs 2): {speedup_3_vs_2:.2f}x")
            
            assert success_1 and success_2 and success_3
        
        # Analyze results
        self.analyze_performance_patterns(results)
    
    def analyze_performance_patterns(self, results: list[dict[str, Any]]):
        """Analyze performance patterns from the test results."""
        print("\n" + "=" * 80)
        print("PERFORMANCE PATTERN ANALYSIS")
        print("=" * 80)
        
        # Group by total hooks
        print("\n=== Performance by Total Hook Count ===")
        hook_groups: dict[int, list[dict[str, Any]]] = {}
        for result in results:
            total_hooks = result['total_hooks']
            if total_hooks not in hook_groups:
                hook_groups[total_hooks] = []
            hook_groups[total_hooks].append(result)
        
        for total_hooks in sorted(hook_groups.keys()):
            group_results = hook_groups[total_hooks]
            submit_1_wins = sum(1 for r in group_results if r['winner'] == 'Submit 1')
            submit_2_wins = sum(1 for r in group_results if r['winner'] == 'Submit 2')
            submit_3_wins = sum(1 for r in group_results if r['winner'] == 'Submit 3')
            avg_speedup_2 = sum(r['speedup_2'] for r in group_results) / len(group_results)
            avg_speedup_3 = sum(r['speedup_3'] for r in group_results) / len(group_results)
            avg_speedup_3_vs_2 = sum(r['speedup_3_vs_2'] for r in group_results) / len(group_results)
            
            print(f"  {total_hooks:4d} hooks: S1: {submit_1_wins}, S2: {submit_2_wins}, S3: {submit_3_wins} | Avg speedup 2: {avg_speedup_2:.2f}x, 3: {avg_speedup_3:.2f}x, 3vs2: {avg_speedup_3_vs_2:.2f}x")
        
        # Group by nexus count
        print("\n=== Performance by Nexus Count ===")
        nexus_groups: dict[int, list[dict[str, Any]]] = {}
        for result in results:
            nexus_count = result['nexus_count']
            if nexus_count not in nexus_groups:
                nexus_groups[nexus_count] = []
            nexus_groups[nexus_count].append(result)
        
        for nexus_count in sorted(nexus_groups.keys()):
            group_results = nexus_groups[nexus_count]
            submit_1_wins = sum(1 for r in group_results if r['winner'] == 'Submit 1')
            submit_2_wins = sum(1 for r in group_results if r['winner'] == 'Submit 2')
            submit_3_wins = sum(1 for r in group_results if r['winner'] == 'Submit 3')
            avg_speedup_2 = sum(r['speedup_2'] for r in group_results) / len(group_results)
            avg_speedup_3 = sum(r['speedup_3'] for r in group_results) / len(group_results)
            avg_speedup_3_vs_2 = sum(r['speedup_3_vs_2'] for r in group_results) / len(group_results)
            
            print(f"  {nexus_count:2d} nexuses: S1: {submit_1_wins}, S2: {submit_2_wins}, S3: {submit_3_wins} | Avg speedup 2: {avg_speedup_2:.2f}x, 3: {avg_speedup_3:.2f}x, 3vs2: {avg_speedup_3_vs_2:.2f}x")
        
        # Group by hooks per nexus
        print("\n=== Performance by Hooks per Nexus ===")
        hooks_per_nexus_groups: dict[int, list[dict[str, Any]]] = {}
        for result in results:
            hooks_per_nexus = result['hooks_per_nexus']
            if hooks_per_nexus not in hooks_per_nexus_groups:
                hooks_per_nexus_groups[hooks_per_nexus] = []
            hooks_per_nexus_groups[hooks_per_nexus].append(result)
        
        for hooks_per_nexus in sorted(hooks_per_nexus_groups.keys()):
            group_results = hooks_per_nexus_groups[hooks_per_nexus]
            submit_1_wins = sum(1 for r in group_results if r['winner'] == 'Submit 1')
            submit_2_wins = sum(1 for r in group_results if r['winner'] == 'Submit 2')
            submit_3_wins = sum(1 for r in group_results if r['winner'] == 'Submit 3')
            avg_speedup_2 = sum(r['speedup_2'] for r in group_results) / len(group_results)
            avg_speedup_3 = sum(r['speedup_3'] for r in group_results) / len(group_results)
            avg_speedup_3_vs_2 = sum(r['speedup_3_vs_2'] for r in group_results) / len(group_results)
            
            print(f"  {hooks_per_nexus:3d} hooks/nexus: S1: {submit_1_wins}, S2: {submit_2_wins}, S3: {submit_3_wins} | Avg speedup 2: {avg_speedup_2:.2f}x, 3: {avg_speedup_3:.2f}x, 3vs2: {avg_speedup_3_vs_2:.2f}x")
        
        # Find optimal thresholds
        self.find_optimal_thresholds(results)
    
    def find_optimal_thresholds(self, results: list[dict[str, Any]]):
        """Find optimal thresholds for adaptive selection."""
        print("\n=== Optimal Threshold Analysis ===")
        
        # Analyze by total hooks
        print("\nBy Total Hook Count:")
        for result in results:
            total_hooks = result['total_hooks']
            winner = result['winner']
            speedup_2 = result['speedup_2']
            speedup_3 = result['speedup_3']
            speedup_3_vs_2 = result['speedup_3_vs_2']
            print(f"  {total_hooks:4d} hooks: {winner} | 2: {speedup_2:.0f}x, 3: {speedup_3:.0f}x, 3vs2: {speedup_3_vs_2:.2f}x")
        
        # Analyze by nexus count
        print("\nBy Nexus Count:")
        for result in results:
            nexus_count = result['nexus_count']
            winner = result['winner']
            speedup_3_vs_2 = result['speedup_3_vs_2']
            print(f"  {nexus_count:2d} nexuses: {winner} (3vs2: {speedup_3_vs_2:.2f}x)")
        
        # Analyze by hooks per nexus
        print("\nBy Hooks per Nexus:")
        for result in results:
            hooks_per_nexus = result['hooks_per_nexus']
            winner = result['winner']
            speedup_3_vs_2 = result['speedup_3_vs_2']
            print(f"  {hooks_per_nexus:3d} hooks/nexus: {winner} (3vs2: {speedup_3_vs_2:.2f}x)")
        
        # Find crossover points
        print("\n=== Crossover Point Analysis ===")
        
        # Find where Submit 2 starts winning consistently
        submit_2_wins_by_hooks: dict[int, list[bool]] = {}
        for result in results:
            total_hooks = result['total_hooks']
            if total_hooks not in submit_2_wins_by_hooks:
                submit_2_wins_by_hooks[total_hooks] = []
            submit_2_wins_by_hooks[total_hooks].append(result['winner'] == 'Submit 2')
        
        print("Submit 2 win rate by total hooks:")
        for total_hooks in sorted(submit_2_wins_by_hooks.keys()):
            wins = submit_2_wins_by_hooks[total_hooks]
            win_rate = sum(wins) / len(wins)
            print(f"  {total_hooks:4d} hooks: {win_rate:.2f} win rate")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        print("\n" + "=" * 80)
        print("EDGE CASE ANALYSIS")
        print("=" * 80)
        
        edge_cases: list[tuple[int, int, str]] = [
            (1, 1, "Single hook, single nexus"),
            (1, 2, "Two hooks, single nexus"),
            (2, 1, "Two nexuses, single hook each"),
            (100, 1, "100 nexuses, single hook each"),
            (1, 1000, "Single nexus, 1000 hooks"),
        ]
        
        for nexus_count, hooks_per_nexus, description in edge_cases:
            print(f"\nTesting edge case: {description}")
            
            nexuses, _ = self.create_test_scenario(nexus_count, hooks_per_nexus)
            total_hooks = nexus_count * hooks_per_nexus
            
            nexus_and_values_1 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            nexus_and_values_2 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            
            # Test both implementations
            start_time = time.perf_counter()
            success_1, _ = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
            time_1 = time.perf_counter() - start_time
            
            start_time = time.perf_counter()
            success_2, _ = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
            time_2 = time.perf_counter() - start_time
            
            speedup = time_1 / time_2 if time_2 > 0 else float('inf')
            winner = "Submit 1" if time_1 < time_2 else "Submit 2"
            
            print(f"  Total hooks: {total_hooks}, Total nexuses: {nexus_count}")
            print(f"  Submit 1: {time_1:.6f}s")
            print(f"  Submit 2: {time_2:.6f}s")
            print(f"  Winner: {winner} ({speedup:.2f}x speedup)")
            
            assert success_1 and success_2
    
    def test_memory_usage_analysis(self):
        """Analyze memory usage patterns."""
        print("\n" + "=" * 80)
        print("MEMORY USAGE ANALYSIS")
        print("=" * 80)
        
        import tracemalloc
        
        test_cases: list[tuple[int, int, str]] = [
            (1, 50, "1 nexus, 50 hooks"),
            (10, 5, "10 nexuses, 5 hooks each"),
            (1, 500, "1 nexus, 500 hooks"),
        ]
        
        for nexus_count, hooks_per_nexus, description in test_cases:
            print(f"\nMemory analysis: {description}")
            
            nexuses, _ = self.create_test_scenario(nexus_count, hooks_per_nexus)
            total_hooks = nexus_count * hooks_per_nexus
            
            nexus_and_values_1 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            nexus_and_values_2 = {nexus: nexus.stored_value + 1000 for nexus in nexuses}
            
            # Test Submit 1 memory usage
            tracemalloc.start()
            success_1, _ = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
            _, peak_1 = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Test Submit 2 memory usage
            tracemalloc.start()
            success_2, _ = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
            _, peak_2 = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            print(f"  Total hooks: {total_hooks}, Total nexuses: {nexus_count}")
            print(f"  Submit 1 - Peak memory: {peak_1 / 1024:.2f} KB")
            print(f"  Submit 2 - Peak memory: {peak_2 / 1024:.2f} KB")
            print(f"  Memory ratio: {peak_1/peak_2:.2f}x")
            
            assert success_1 and success_2


if __name__ == "__main__":
    # Run the comprehensive performance analysis
    test_instance = TestComprehensivePerformanceAnalysis()
    test_instance.setup_method()
    
    print("=" * 80)
    print("COMPREHENSIVE PERFORMANCE ANALYSIS")
    print("Hook Count × Nexus Count Performance Matrix")
    print("=" * 80)
    
    _ = test_instance.test_performance_matrix()
    test_instance.test_edge_cases()
    test_instance.test_memory_usage_analysis()
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ANALYSIS COMPLETE")
    print("=" * 80)
