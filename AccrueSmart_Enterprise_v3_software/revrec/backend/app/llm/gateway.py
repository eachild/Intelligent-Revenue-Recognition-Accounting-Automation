# Dummy LLM Gateway for local testing

class LLMGateway:
    def __init__(self):
        pass

    def audit_memo(self, payload: dict) -> str:
        # This is a mock implementation
        print(f"Mock LLMGateway.audit_memo called with payload: {payload}")
        return "Mock audit memo generated successfully."
