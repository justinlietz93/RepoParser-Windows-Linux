from typing import Tuple, List, Dict, Optional, Any
import tiktoken
import logging

class TokenCalculator:
    """Handles token calculation and cost estimation for different models."""
    
    # Token cost per 1K tokens (as of 2024)
    MODEL_COSTS = {
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-32k': {'input': 0.06, 'output': 0.12},
        'gpt-3.5-turbo': {'input': 0.0010, 'output': 0.0020},
        'gpt-3.5-turbo-16k': {'input': 0.0030, 'output': 0.0040}
    }

    def __init__(self):
        """Initialize the token calculator."""
        self.logger = logging.getLogger(__name__)

    def count_tokens(
        self, 
        text: str, 
        model: str = "gpt-3.5-turbo"
    ) -> Tuple[int, List[int]]:
        """
        Count tokens in text for a specific model.
        
        Args:
            text: Text to analyze
            model: Model name to use for tokenization
            
        Returns:
            Tuple of (token count, list of token IDs)
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.logger.warning(
                f"Model {model} not found, falling back to cl100k_base"
            )
            encoding = tiktoken.get_encoding("cl100k_base")

        token_ids = encoding.encode(text)
        return len(token_ids), token_ids

    def calculate_cost(
        self, 
        token_count: int, 
        model: str = "gpt-3.5-turbo", 
        is_output: bool = False
    ) -> float:
        """
        Calculate cost for token count.
        
        Args:
            token_count: Number of tokens
            model: Model name
            is_output: Whether these are output tokens
            
        Returns:
            Estimated cost in USD
        """
        if model not in self.MODEL_COSTS:
            self.logger.warning(
                f"Model {model} not found in cost table, using gpt-3.5-turbo"
            )
            model = "gpt-3.5-turbo"

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
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
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
