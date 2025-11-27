"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from app.services.cost_tracking_service import CostTrackingService


class TestCostTrackingService:
    """Test suite for CostTrackingService."""
    
    def test_extract_costs_from_result_with_provider_details(self):
        """Test cost extraction from result with OpenRouter provider_details."""
        # Mock result object
        result = Mock()
        
        # Mock message with provider_details
        message = Mock()
        message.provider_details = {
            'cost': 0.001234,
            'cost_details': {
                'upstream_inference_prompt_cost': 0.000500,
                'upstream_inference_completions_cost': 0.000734
            }
        }
        result.new_messages.return_value = [message]
        
        # Extract costs
        costs = CostTrackingService.extract_costs_from_result(
            result,
            requested_model="google/gemini-2.5-flash",
            session_id="test-session"
        )
        
        # Verify
        assert costs["total_cost"] == 0.001234
        assert costs["prompt_cost"] == 0.000500
        assert costs["completion_cost"] == 0.000734
    
    def test_extract_costs_from_result_missing_provider_details(self):
        """Test cost extraction when provider_details is missing."""
        # Mock result with no provider_details
        result = Mock()
        message = Mock()
        message.provider_details = None
        result.new_messages.return_value = [message]
        
        # Extract costs
        costs = CostTrackingService.extract_costs_from_result(
            result,
            requested_model="google/gemini-2.5-flash"
        )
        
        # Should return zero costs
        assert costs["total_cost"] == 0.0
        assert costs["prompt_cost"] == 0.0
        assert costs["completion_cost"] == 0.0
    
    def test_extract_costs_from_result_no_messages(self):
        """Test cost extraction when no messages exist."""
        # Mock result with no messages
        result = Mock()
        result.new_messages.return_value = None
        
        # Extract costs
        costs = CostTrackingService.extract_costs_from_result(
            result,
            requested_model="google/gemini-2.5-flash"
        )
        
        # Should return zero costs
        assert costs["total_cost"] == 0.0
        assert costs["prompt_cost"] == 0.0
        assert costs["completion_cost"] == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_streaming_costs_genai_prices_success(self):
        """Test streaming cost calculation using genai-prices."""
        # Mock usage data
        usage_data = Mock()
        usage_data.input_tokens = 1000
        usage_data.output_tokens = 500
        
        # Mock genai-prices price object
        mock_price = Mock()
        mock_price.input_price = 0.00025
        mock_price.output_price = 0.000375
        mock_price.total_price = 0.000625
        
        with patch('genai_prices.calc_price', return_value=mock_price):
            costs = await CostTrackingService.calculate_streaming_costs(
                usage_data,
                requested_model="google/gemini-2.5-flash",
                session_id="test-session"
            )
        
        # Verify
        assert costs["prompt_cost"] == 0.00025
        assert costs["completion_cost"] == 0.000375
        assert costs["total_cost"] == 0.000625
    
    @pytest.mark.asyncio
    async def test_calculate_streaming_costs_fallback_pricing(self):
        """Test streaming cost calculation falling back to YAML config."""
        # Mock usage data
        usage_data = Mock()
        usage_data.input_tokens = 1000
        usage_data.output_tokens = 500
        
        # Mock fallback pricing config
        fallback_config = {
            'models': {
                'google/test-model': {
                    'input_per_1m': 250.0,
                    'output_per_1m': 750.0,
                    'source': 'manual'
                }
            }
        }
        
        yaml_content = """
models:
  google/test-model:
    input_per_1m: 250.0
    output_per_1m: 750.0
    source: manual
"""
        
        with patch('genai_prices.calc_price', side_effect=LookupError("Model not found")):
            with patch('builtins.open', mock_open(read_data=yaml_content)):
                with patch('pathlib.Path.exists', return_value=True):
                    costs = await CostTrackingService.calculate_streaming_costs(
                        usage_data,
                        requested_model="google/test-model",
                        session_id="test-session"
                    )
        
        # Verify fallback calculation
        # prompt_cost = (1000 / 1_000_000) * 250.0 = 0.25
        # completion_cost = (500 / 1_000_000) * 750.0 = 0.375
        # total = 0.625
        assert costs["prompt_cost"] == 0.25
        assert costs["completion_cost"] == 0.375
        assert costs["total_cost"] == 0.625
    
    @pytest.mark.asyncio
    async def test_calculate_streaming_costs_no_usage_data(self):
        """Test streaming cost calculation with no usage data."""
        costs = await CostTrackingService.calculate_streaming_costs(
            usage_data=None,
            requested_model="google/gemini-2.5-flash"
        )
        
        # Should return zero costs
        assert costs["total_cost"] == 0.0
        assert costs["prompt_cost"] == 0.0
        assert costs["completion_cost"] == 0.0
    
    def test_get_fallback_pricing_model_found(self):
        """Test fallback pricing when model exists in config."""
        yaml_content = """
models:
  google/test-model:
    input_per_1m: 250.0
    output_per_1m: 750.0
    source: openrouter_website
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = CostTrackingService.get_fallback_pricing(
                    model="google/test-model",
                    prompt_tokens=1000,
                    completion_tokens=500
                )
        
        # Verify
        assert result is not None
        assert result["prompt_cost"] == 0.25
        assert result["completion_cost"] == 0.375
        assert result["total_cost"] == 0.625
        assert result["source"] == "openrouter_website"
        assert "config_file" in result
    
    def test_get_fallback_pricing_model_not_found(self):
        """Test fallback pricing when model not in config."""
        yaml_content = """
models:
  other/model:
    input_per_1m: 100.0
    output_per_1m: 200.0
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = CostTrackingService.get_fallback_pricing(
                    model="google/missing-model",
                    prompt_tokens=1000,
                    completion_tokens=500
                )
        
        # Should return None
        assert result is None
    
    def test_get_fallback_pricing_config_missing(self):
        """Test fallback pricing when config file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = CostTrackingService.get_fallback_pricing(
                model="google/test-model",
                prompt_tokens=1000,
                completion_tokens=500
            )
        
        # Should return None
        assert result is None
    
    def test_get_fallback_pricing_calculation_accuracy(self):
        """Test that fallback pricing calculations are accurate."""
        yaml_content = """
models:
  test/model:
    input_per_1m: 500.0
    output_per_1m: 1500.0
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = CostTrackingService.get_fallback_pricing(
                    model="test/model",
                    prompt_tokens=5000,
                    completion_tokens=2000
                )
        
        # Verify calculations
        # prompt_cost = (5000 / 1_000_000) * 500.0 = 2.5
        # completion_cost = (2000 / 1_000_000) * 1500.0 = 3.0
        # total = 5.5
        assert result["prompt_cost"] == 2.5
        assert result["completion_cost"] == 3.0
        assert result["total_cost"] == 5.5

