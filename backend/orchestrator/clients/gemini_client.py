# orchestrator/clients/gemini_client.py
"""
Wrapper for the Gemini API client.
This client is responsible for interacting with the Gemini 2.5 Pro API for moderator tasks.
"""

imporclass GeminiAPIClient:
    def __init__(self):
        """
        Initializes the GeminiAPIClient.
        If GEMINI_API_KEY is not set, falls back to a mock mode
        so that local runs and tests don't crash.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.enabled = bool(self.api_key)
        if self.enabled:
            # In a real implementation, you would initialize the Gemini client here.
            print("Initialized Gemini API client.")
        else:
            print("GEMINI_API_KEY not set. Using mock moderator responses.")
ini API client.")    def invoke(self, prompt):
        """
        Invokes the Gemini API with a given prompt.

        Args:
            prompt (str): The prompt to send to the API.

        Returns:
            str: The API's response.
        """
        # Mock behavior when API key is not provided.
        if not getattr(self, "enabled", False):
            return "[Mock Gemini] Final decision synthesized (no API key provided)."
        print(f"Invoking Gemini API with prompt: {prompt}")
        return f"Gemini response for: {prompt}"onse for: {prompt}"
