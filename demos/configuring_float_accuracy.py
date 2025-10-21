"""
Demo: Configuring Float Accuracy
=================================

This demo shows how to configure the FLOAT_ACCURACY setting using the
nexpy.default module. This setting controls the tolerance for floating-point
equality comparisons throughout the library.
"""

import nexpy as nx
from nexpy import default

print("Float Accuracy Configuration Demo")
print("=" * 60)

# 1. View the default float accuracy
print(f"\n1. Default FLOAT_ACCURACY: {default.FLOAT_ACCURACY}")
print("   (default is 1e-9)")

# 2. For high-precision scientific applications
print("\n2. Configuring for high-precision scientific work:")
default.FLOAT_ACCURACY = 1e-12
print(f"   FLOAT_ACCURACY set to: {default.FLOAT_ACCURACY}")

# Create observables with high precision
x = nx.XValue(0.123456789012345)
y = nx.XValue(0.123456789012344)  # Differs by 1e-12

x.value_hook.join(y.value_hook)
print(f"   x.value = {x.value}")
print(f"   y.value = {y.value}")
print(f"   Values are now synchronized with high precision")

# 3. For UI applications (more lenient)
print("\n3. Configuring for UI applications:")
default.FLOAT_ACCURACY = 1e-6
print(f"   FLOAT_ACCURACY set to: {default.FLOAT_ACCURACY}")

# Create observables for UI work
ui_x = nx.XValue(0.1234567)
ui_y = nx.XValue(0.1234568)  # Differs by 1e-7, within tolerance

ui_x.value_hook.join(ui_y.value_hook)
print(f"   ui_x.value = {ui_x.value}")
print(f"   ui_y.value = {ui_y.value}")
print(f"   Small differences are ignored for smoother UI")

# 4. Common use cases
print("\n4. Common FLOAT_ACCURACY values by use case:")
print("   - UI applications: 1e-6 to 1e-3")
print("   - General purpose: 1e-9 to 1e-8 (default)")
print("   - Scientific/High precision: 1e-12 to 1e-15")

# 5. Access the NEXUS_MANAGER
print(f"\n5. Default NEXUS_MANAGER: {default.NEXUS_MANAGER}")
print(f"   Type: {type(default.NEXUS_MANAGER).__name__}")

print("\n" + "=" * 60)
print("Key Takeaway:")
print("  Configure FLOAT_ACCURACY before creating observables for")
print("  consistent behavior across your application.")
print("=" * 60)

