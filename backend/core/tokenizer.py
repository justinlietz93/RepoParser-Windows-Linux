from typing import Tuple, List, Dict, Optional, Any
import tiktoken
import logging

class TokenCalculator:
    """Handles token calculation and cost estimation for different models."""
    
    # Token cost per 1K tokens (as of 2024)
    MODEL_COSTS = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-32k': {'input': 0.06, 'output': 0.12},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.02},
        'gpt-3.5-turbo': {'input': 0.0010, 'output': 0.0020},
        'gpt-3.5-turbo-16k': {'input': 0.0030, 'output': 0.0040},
        'deepseek-chat': {'input': 0.002, 'output': 0.002},  # DeepSeek pricing
        'gemini-1.5-pro-latest': {
            'standard': {'input': 0.00125, 'output': 0.005, 'context': 0.0003125},  # Up to 128k tokens
            'long': {'input': 0.0025, 'output': 0.01, 'context': 0.000625}  # Beyond 128k tokens
        }
    }

    # Model context limits
    MODEL_LIMITS = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 16384,
        "gpt-3.5-turbo-16k": 16384,
        "claude-2.1": 200000,
        "claude-instant": 100000,
        "deepseek-chat": 32768,
        "gemini-1.5-pro-latest": 1000000
    }

    def __init__(self):
        """Initialize the token calculator."""
        self.logger = logging.getLogger(__name__)
        try:
            import tiktoken
            self.tiktoken = tiktoken
        except ImportError:
            self.logger.warning("tiktoken not available, falling back to approximate counting")
            self.tiktoken = None

    @classmethod
    def get_model_limit(cls, model: str) -> int:
        """Get the context limit for a specific model.
        
        Args:
            model: The model name
            
        Returns:
            int: The model's context limit in tokens
        """
        return cls.MODEL_LIMITS.get(model, 8192)  # Default to gpt-4 limit if model not found

    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of all available models with defined limits."""
        return list(cls.MODEL_LIMITS.keys())

    def count_tokens(self, text: str, model: str = None) -> tuple[int, str]:
        """
        Count tokens in text for a specific model.
        Returns (token_count, method_used)
        """
        if not text:
            return 0, "empty"

        try:
            # For Gemini models, use their token counter
            if model and model.startswith('gemini'):
                try:
                    import google.generativeai as genai
                    count = genai.count_tokens(text)
                    return count, "gemini_counter"
                except Exception as e:
                    self.logger.warning(f"Error using Gemini token counter: {e}")
                    return self._approximate_token_count(text), "approximate"

            # Special handling for DeepSeek models
            if model == "deepseek-chat":
                # Use DeepSeek's approximate token ratios
                english_chars = sum(1 for c in text if ord(c) < 128)  # ASCII characters
                chinese_chars = sum(1 for c in text if ord(c) >= 128)  # Non-ASCII (approximate for Chinese)
                
                # Apply DeepSeek's conversion ratios
                token_count = int((english_chars * 0.3) + (chinese_chars * 0.6))
                return token_count, "deepseek_estimate"

            # For OpenAI/compatible models, use tiktoken
            if self.tiktoken and model:
                try:
                    encoding = self.tiktoken.encoding_for_model(model)
                    tokens = encoding.encode(text)
                    return len(tokens), "tiktoken"
                except Exception as e:
                    self.logger.warning(f"Error using tiktoken for {model}: {e}")

            # Fallback to approximate counting
            return self._approximate_token_count(text), "approximate"

        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return self._approximate_token_count(text), "approximate"

    def _approximate_token_count(self, text: str) -> int:
        """Approximate token count based on word count."""
        # Average ratio of tokens to words is about 1.3
        words = len(text.split())
        return int(words * 1.3)

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for given token counts and model."""
        try:
            costs = self.MODEL_COSTS.get(model, {'input': 0.002, 'output': 0.002})
            input_cost = (input_tokens / 1000) * costs['input']
            output_cost = (output_tokens / 1000) * costs['output']
            return input_cost + output_cost
        except Exception as e:
            self.logger.error(f"Error estimating cost: {e}")
            return 0.0

    def calculate_cost(
        self, 
        token_count: int, 
        model: str = "gpt-4", 
        is_output: bool = False,
        is_context: bool = False
    ) -> float:
        """
        Calculate cost for token count.
        
        Args:
            token_count: Number of tokens
            model: Model name
            is_output: Whether these are output tokens
            is_context: Whether these are context tokens (for Gemini)
            
        Returns:
            Estimated cost in USD
        """
        if model not in self.MODEL_COSTS:
            self.logger.warning(
                f"Model {model} not found in cost table, using gpt-3.5-turbo"
            )
            model = "gpt-3.5-turbo"

        # Special handling for Gemini's tiered pricing
        if model == 'gemini-1.5-pro-latest':
            tier = 'long' if token_count > 128000 else 'standard'
            cost_type = 'context' if is_context else ('output' if is_output else 'input')
            cost_per_1k = self.MODEL_COSTS[model][tier][cost_type]
        else:
            cost_type = 'output' if is_output else 'input'
            cost_per_1k = self.MODEL_COSTS[model][cost_type]

        return (token_count / 1000) * cost_per_1k

    def analyze_text(
        self, 
        text: str, 
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Perform complete token analysis of text.
        
        Args:
            text: Text to analyze
            model: Model to use
            
        Returns:
            Dictionary containing analysis results
        """
        token_count, token_ids = self.count_tokens(text, model)
        
        # Get sample tokens for display
        try:
            encoding = tiktoken.encoding_for_model(model)
            sample_tokens = [
                {
                    'id': tid,
                    'text': encoding.decode([tid])
                }
                for tid in token_ids[:10]  # First 10 tokens as sample
            ]
        except Exception as e:
            self.logger.error(f"Error getting sample tokens: {str(e)}")
            sample_tokens = []

        return {
            'token_count': token_count,
            'input_cost': self.calculate_cost(token_count, model, False),
            'output_cost': self.calculate_cost(token_count, model, True),
            'model': model,
            'sample_tokens': sample_tokens
        }

class TokenAnalyzer:
    """High-level interface for token analysis with caching and UI-friendly output."""
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the token analyzer.
        
        Args:
            model: Default model to use for analysis
        """
        self.calculator = TokenCalculator()
        self.model = model
        self.cache = {}
        self.logger = logging.getLogger(__name__)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Number of tokens
        """
        try:
            token_count, _ = self.calculator.count_tokens(text, self.model)
            return token_count
        except Exception as e:
            self.logger.error(f"Error counting tokens: {str(e)}")
            return 0

    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content and return UI-friendly results.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary with analysis results formatted for UI display
        """
        # Check cache
        cache_key = f"{content[:100]}_{len(content)}_{self.model}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get raw analysis
            analysis = self.calculator.analyze_text(content, self.model)
            
            # Format for UI
            result = {
                'Statistics': {
                    'Total Tokens': analysis['token_count'],
                    'Estimated Input Cost': f"${analysis['input_cost']:.4f}",
                    'Estimated Output Cost': f"${analysis['output_cost']:.4f}",
                    'Model Used': analysis['model']
                },
                'Sample Tokens': [
                    f"Token {t['id']}: {t['text']}"
                    for t in analysis['sample_tokens']
                ]
            }
            
            # Cache result
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {str(e)}")
            return {
                'error': f"Analysis failed: {str(e)}",
                'Statistics': {
                    'Total Tokens': 0,
                    'Estimated Input Cost': '$0.00',
                    'Estimated Output Cost': '$0.00',
                    'Model Used': self.model
                }
            }

def get_available_models() -> List[str]:
    """Get list of available models."""
    return list(TokenCalculator.MODEL_COSTS.keys())
