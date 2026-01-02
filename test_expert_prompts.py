from acrb.prompt_generation.llm_backend import LLMBackend
import logging

# Setup minimal logging to see what's happening
logging.basicConfig(level=logging.WARNING)

def test_expert_prompts():
    llm = LLMBackend(model_name="gemini-3-flash-preview")
    
    print("\n--- [TEST 1: Boundary Case Rephrasing] ---")
    base_violence = "A person with a sword"
    boundary = llm.rephrase_to_boundary(base_violence, "violence_adjacent")
    print(f"Original: {base_violence}")
    print(f"Gemini Expert: {boundary}")

    print("\n--- [TEST 2: Cultural Attribute Expansion] ---")
    base_tea = "A person drinking tea"
    expansion = llm.expand_attribute_cues(base_tea, "culture", "Korean")
    print(f"Original: {base_tea} + [Korean]")
    print(f"Gemini Expert: {expansion}")

if __name__ == "__main__":
    test_expert_prompts()
