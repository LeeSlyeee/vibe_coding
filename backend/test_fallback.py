import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_analysis import ai_analyzer

print("Testing Fallback Logic...")
# Test Happy
res_happy = ai_analyzer.generate_comment("행복해 (99.9%)")
print(f"Input: 행복해 -> Output: {res_happy}")

# Test Sad
res_sad = ai_analyzer.generate_comment("우울해 (99.9%)")
print(f"Input: 우울해 -> Output: {res_sad}")

# Test Randomness
res_sad2 = ai_analyzer.generate_comment("우울해 (99.9%)")
print(f"Input: 우울해 (2nd) -> Output: {res_sad2}")

if res_sad != res_sad2:
    print("SUCCESS: Random logic works (Outputs differ).")
else:
    print("NOTE: Outputs might be same due to chance or fixed logic.")
