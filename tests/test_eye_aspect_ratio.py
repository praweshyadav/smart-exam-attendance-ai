from backend.ai.eye_aspect_ratio import EyeAspectRatio


print("===== EYE ASPECT RATIO TEST =====")


print("1. Testing open eye EAR...")

open_eye = [
    [0.0, 0.0],
    [1.0, 1.0],
    [3.0, 1.0],
    [4.0, 0.0],
    [3.0, -1.0],
    [1.0, -1.0],
]

open_ear = EyeAspectRatio.calculate(open_eye)

print(f"   Open eye EAR: {open_ear:.4f}")

if open_ear <= 0:
    raise RuntimeError(
        "Open eye EAR should be greater than zero."
    )

print("   PASS")


print("2. Testing closed eye EAR...")

closed_eye = [
    [0.0, 0.0],
    [1.0, 0.05],
    [3.0, 0.05],
    [4.0, 0.0],
    [3.0, -0.05],
    [1.0, -0.05],
]

closed_ear = EyeAspectRatio.calculate(closed_eye)

print(f"   Closed eye EAR: {closed_ear:.4f}")

if closed_ear <= 0:
    raise RuntimeError(
        "Closed eye EAR should be greater than zero."
    )

print("   PASS")


print("3. Comparing open and closed eye EAR...")

if open_ear <= closed_ear:
    raise RuntimeError(
        "Open eye EAR should be greater than closed eye EAR."
    )

print(
    f"   Open EAR ({open_ear:.4f}) > "
    f"Closed EAR ({closed_ear:.4f})"
)

print("   PASS")


print("4. Testing invalid landmark count...")

try:
    EyeAspectRatio.calculate(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [2.0, 0.0],
        ]
    )
except ValueError:
    print("   PASS")
else:
    raise RuntimeError(
        "Invalid landmark count was not rejected."
    )


print("5. Testing zero horizontal distance...")

try:
    EyeAspectRatio.calculate(
        [
            [1.0, 0.0],
            [1.0, 0.5],
            [1.0, -0.5],
            [1.0, 0.0],
            [1.0, -0.5],
            [1.0, 0.5],
        ]
    )
except ValueError:
    print("   PASS")
else:
    raise RuntimeError(
        "Zero horizontal distance was not rejected."
    )


print("ALL EYE ASPECT RATIO TESTS PASSED")