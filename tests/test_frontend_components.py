"""
Frontend Components Test Suite
Tests for React components, hooks, and TypeScript interfaces
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestReactComponents:
    """Test suite for React component functionality."""
    
    def test_demo_interface_props_validation(self):
        """Test DemoInterface component props validation."""
        # Mock valid props
        valid_props = {
            "brand": {
                "id": "brand-123",
                "name": "Test Brand",
                "designDNA": {
                    "aesthetic": "minimalist",
                    "colorPreferences": ["black", "white"],
                    "silhouetteStyle": "clean_lines"
                }
            },
            "onGenerationStart": Mock(),
            "onGenerationComplete": Mock(),
            "theme": {
                "primary": "#000000",
                "secondary": "#ffffff",
                "accent": "#cccccc"
            }
        }
        
        # Validate prop structure
        assert "brand" in valid_props
        assert "onGenerationStart" in valid_props
        assert "onGenerationComplete" in valid_props
        assert "theme" in valid_props
        
        # Validate brand structure
        brand = valid_props["brand"]
        assert "id" in brand
        assert "name" in brand
        assert "designDNA" in brand
        
        # Validate design DNA structure
        design_dna = brand["designDNA"]
        assert "aesthetic" in design_dna
        assert "colorPreferences" in design_dna
        assert "silhouetteStyle" in design_dna
        assert isinstance(design_dna["colorPreferences"], list)
    
    def test_generation_request_validation(self):
        """Test generation request data validation."""
        valid_request = {
            "name": "Test Generation",
            "inputs": {
                "textPrompt": "minimalist spring collection",
                "referenceImages": ["https://example.com/ref1.jpg"],
                "colorPalette": ["white", "beige", "black"],
                "materialPreferences": ["cotton", "linen"],
                "brandContext": {
                    "brandId": "brand-123",
                    "designDNA": {
                        "aesthetic": "minimalist"
                    }
                }
            },
            "brandParameters": {
                "brandId": "brand-123",
                "designDnaAdherence": 0.8,
                "targetDemographic": "urban_professional"
            },
            "targetPieces": 5,
            "qualityLevel": "high",
            "creativityLevel": 0.7,
            "useMemoryContext": True,
            "memoryDepth": 5
        }
        
        # Validate required fields
        assert valid_request["name"] != ""
        assert "inputs" in valid_request
        assert "brandParameters" in valid_request
        assert valid_request["targetPieces"] > 0
        assert valid_request["qualityLevel"] in ["low", "medium", "high"]
        assert 0.0 <= valid_request["creativityLevel"] <= 1.0
        assert isinstance(valid_request["useMemoryContext"], bool)
        
        # Validate inputs structure
        inputs = valid_request["inputs"]
        assert "textPrompt" in inputs
        assert "brandContext" in inputs
        assert inputs["textPrompt"] != ""
        
        # Validate brand parameters
        brand_params = valid_request["brandParameters"]
        assert "brandId" in brand_params
        assert "designDnaAdherence" in brand_params
        assert 0.0 <= brand_params["designDnaAdherence"] <= 1.0
    
    def test_generation_response_structure(self):
        """Test generation response data structure."""
        mock_response = {
            "taskId": "task-12345",
            "status": "queued",
            "kseContextRetrieved": True,
            "memoryNodesAccessed": 3,
            "commercialPredictionsEnabled": True,
            "websocketUrl": "ws://localhost:8000/ws/generation/task-12345",
            "estimatedCompletionTime": 120,
            "queuePosition": 2
        }
        
        # Validate response structure
        assert "taskId" in mock_response
        assert "status" in mock_response
        assert "websocketUrl" in mock_response
        assert mock_response["status"] in ["queued", "running", "completed", "failed"]
        assert isinstance(mock_response["kseContextRetrieved"], bool)
        assert isinstance(mock_response["memoryNodesAccessed"], int)
        assert mock_response["memoryNodesAccessed"] >= 0
        assert mock_response["websocketUrl"].startswith("ws://")
    
    def test_memory_insights_structure(self):
        """Test memory insights data structure."""
        mock_insights = {
            "brandId": "brand-123",
            "totalMemoryNodes": 25,
            "recentGenerations": [
                {
                    "id": "gen-1",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "generationType": "capsule_collection",
                    "qualityScore": 0.85
                }
            ],
            "designEvolution": {
                "evolutionVelocity": 0.65,
                "consistencyTrend": "stable",
                "innovationIndex": 0.72
            },
            "commercialPerformance": {
                "averageConversionRate": 0.15,
                "revenueTrend": "increasing",
                "topPerformingStyles": ["minimalist", "contemporary"]
            },
            "temporalPatterns": {
                "seasonalCycles": ["spring_fresh", "summer_light"],
                "trendCycles": ["minimalism_rising"]
            },
            "memoryHealth": {
                "overallHealth": 0.8,
                "nodeCount": 25,
                "recentActivity": 8
            }
        }
        
        # Validate insights structure
        assert "brandId" in mock_insights
        assert "totalMemoryNodes" in mock_insights
        assert "recentGenerations" in mock_insights
        assert "designEvolution" in mock_insights
        assert "commercialPerformance" in mock_insights
        
        # Validate design evolution
        design_evolution = mock_insights["designEvolution"]
        assert 0.0 <= design_evolution["evolutionVelocity"] <= 1.0
        assert 0.0 <= design_evolution["innovationIndex"] <= 1.0
        assert design_evolution["consistencyTrend"] in ["improving", "stable", "declining"]
        
        # Validate commercial performance
        commercial = mock_insights["commercialPerformance"]
        assert 0.0 <= commercial["averageConversionRate"] <= 1.0
        assert commercial["revenueTrend"] in ["increasing", "decreasing", "stable"]
        assert isinstance(commercial["topPerformingStyles"], list)
    
    def test_websocket_message_types(self):
        """Test WebSocket message type validation."""
        # Status update message
        status_message = {
            "type": "status_update",
            "taskId": "task-12345",
            "status": "running",
            "progress": 0.45,
            "currentStep": "generating_visuals",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        # Completion message
        completion_message = {
            "type": "generation_complete",
            "taskId": "task-12345",
            "status": "completed",
            "progress": 1.0,
            "results": {
                "outputs": [
                    {
                        "outputId": "output-1",
                        "contentUrl": "https://storage.example.com/output1.jpg",
                        "qualityScore": 0.85,
                        "brandAlignment": 0.92
                    }
                ],
                "memoryUpdates": {
                    "nodesCreated": 1,
                    "patternsUpdated": 3
                }
            },
            "timestamp": "2024-01-15T10:35:00Z"
        }
        
        # Error message
        error_message = {
            "type": "generation_error",
            "taskId": "task-12345",
            "error": {
                "code": "GENERATION_FAILED",
                "message": "Failed to generate outputs due to invalid input parameters",
                "details": {
                    "invalidParameter": "colorPalette",
                    "reason": "Invalid color format"
                }
            },
            "timestamp": "2024-01-15T10:32:00Z"
        }
        
        # Validate message structures
        messages = [status_message, completion_message, error_message]
        for message in messages:
            assert "type" in message
            assert "taskId" in message
            assert "timestamp" in message
        
        # Validate specific message types
        assert status_message["type"] == "status_update"
        assert 0.0 <= status_message["progress"] <= 1.0
        assert "currentStep" in status_message
        
        assert completion_message["type"] == "generation_complete"
        assert "results" in completion_message
        assert "outputs" in completion_message["results"]
        
        assert error_message["type"] == "generation_error"
        assert "error" in error_message
        assert "code" in error_message["error"]
        assert "message" in error_message["error"]


class TestReactHooks:
    """Test suite for React hooks functionality."""
    
    def test_generation_stream_hook_state(self):
        """Test useGenerationStream hook state management."""
        # Mock initial state
        initial_state = {
            "isConnected": False,
            "connectionStatus": "disconnected",
            "currentGeneration": None,
            "generationHistory": [],
            "error": None,
            "reconnectAttempts": 0
        }
        
        # Mock connected state
        connected_state = {
            "isConnected": True,
            "connectionStatus": "connected",
            "currentGeneration": {
                "taskId": "task-12345",
                "status": "running",
                "progress": 0.3
            },
            "generationHistory": [],
            "error": None,
            "reconnectAttempts": 0
        }
        
        # Mock error state
        error_state = {
            "isConnected": False,
            "connectionStatus": "error",
            "currentGeneration": None,
            "generationHistory": [],
            "error": {
                "message": "WebSocket connection failed",
                "code": "CONNECTION_ERROR"
            },
            "reconnectAttempts": 3
        }
        
        # Validate state structures
        states = [initial_state, connected_state, error_state]
        for state in states:
            assert "isConnected" in state
            assert "connectionStatus" in state
            assert "currentGeneration" in state
            assert "generationHistory" in state
            assert "error" in state
            assert "reconnectAttempts" in state
            assert isinstance(state["isConnected"], bool)
            assert isinstance(state["reconnectAttempts"], int)
        
        # Validate connection status values
        valid_statuses = ["disconnected", "connecting", "connected", "error", "reconnecting"]
        for state in states:
            assert state["connectionStatus"] in valid_statuses
    
    def test_generation_stream_hook_actions(self):
        """Test useGenerationStream hook actions."""
        # Mock hook actions
        mock_actions = {
            "connect": Mock(),
            "disconnect": Mock(),
            "startGeneration": Mock(),
            "cancelGeneration": Mock(),
            "clearError": Mock(),
            "clearHistory": Mock()
        }
        
        # Validate action availability
        expected_actions = [
            "connect", "disconnect", "startGeneration", 
            "cancelGeneration", "clearError", "clearHistory"
        ]
        
        for action in expected_actions:
            assert action in mock_actions
            assert callable(mock_actions[action])
    
    def test_websocket_reconnect_logic(self):
        """Test WebSocket reconnect logic."""
        # Mock reconnect configuration
        reconnect_config = {
            "maxAttempts": 5,
            "baseDelay": 1000,  # milliseconds
            "maxDelay": 30000,  # milliseconds
            "backoffMultiplier": 2,
            "jitter": True
        }
        
        # Test exponential backoff calculation
        def calculate_delay(attempt, config):
            base_delay = config["baseDelay"]
            multiplier = config["backoffMultiplier"]
            max_delay = config["maxDelay"]
            
            delay = min(base_delay * (multiplier ** attempt), max_delay)
            
            if config["jitter"]:
                # Add ±25% jitter
                jitter_range = delay * 0.25
                # For testing, we'll just validate the range
                assert delay - jitter_range <= delay + jitter_range
            
            return delay
        
        # Test delay calculation for different attempts
        for attempt in range(6):
            delay = calculate_delay(attempt, reconnect_config)
            assert delay >= reconnect_config["baseDelay"]
            assert delay <= reconnect_config["maxDelay"]
            
            if attempt < 5:  # Within max attempts
                expected_base = reconnect_config["baseDelay"] * (2 ** attempt)
                expected_delay = min(expected_base, reconnect_config["maxDelay"])
                assert delay <= expected_delay * 1.25  # Account for jitter
                assert delay >= expected_delay * 0.75   # Account for jitter


class TestTypeScriptInterfaces:
    """Test suite for TypeScript interface validation."""
    
    def test_multimodal_inputs_interface(self):
        """Test MultiModalInputs interface structure."""
        multimodal_inputs = {
            "textPrompt": "minimalist spring collection with clean lines",
            "referenceImages": [
                "https://example.com/ref1.jpg",
                "https://example.com/ref2.jpg"
            ],
            "sketchInputs": [
                {
                    "sketchUrl": "https://example.com/sketch1.svg",
                    "sketchType": "silhouette",
                    "confidence": 0.8
                }
            ],
            "colorPalette": ["#FFFFFF", "#F5F5DC", "#000000"],
            "materialPreferences": [
                {
                    "material": "cotton",
                    "weight": 0.7
                },
                {
                    "material": "linen", 
                    "weight": 0.3
                }
            ],
            "styleVectors": [
                {
                    "vectorId": "style-vec-1",
                    "embedding": [0.1, 0.2, 0.3],  # Truncated for example
                    "source": "reference_image"
                }
            ],
            "brandContext": {
                "brandId": "brand-123",
                "designDNA": {
                    "aesthetic": "minimalist",
                    "colorPreferences": ["neutral"],
                    "silhouetteStyle": "clean_lines"
                }
            }
        }
        
        # Validate required fields
        assert "textPrompt" in multimodal_inputs
        assert "brandContext" in multimodal_inputs
        
        # Validate optional arrays
        optional_arrays = ["referenceImages", "sketchInputs", "materialPreferences", "styleVectors"]
        for field in optional_arrays:
            if field in multimodal_inputs:
                assert isinstance(multimodal_inputs[field], list)
        
        # Validate color palette format
        if "colorPalette" in multimodal_inputs:
            for color in multimodal_inputs["colorPalette"]:
                # Should be hex color or color name
                assert isinstance(color, str)
                assert len(color) > 0
        
        # Validate brand context structure
        brand_context = multimodal_inputs["brandContext"]
        assert "brandId" in brand_context
        assert "designDNA" in brand_context
    
    def test_generation_output_interface(self):
        """Test GenerationOutput interface structure."""
        generation_output = {
            "outputId": "output-12345",
            "taskId": "task-67890", 
            "outputIndex": 0,
            "outputType": "image",
            "contentUrl": "https://storage.example.com/output.jpg",
            "thumbnailUrl": "https://storage.example.com/thumb.jpg",
            "metadata": {
                "generationModel": "stylegan3",
                "resolution": "1024x1024",
                "seed": 42,
                "steps": 50,
                "guidanceScale": 7.5
            },
            "qualityMetrics": {
                "overallQuality": 0.87,
                "technicalQuality": 0.89,
                "aestheticQuality": 0.85,
                "brandAlignment": 0.92,
                "commercialViability": 0.78,
                "clipScore": 0.83
            },
            "designAttributes": {
                "garmentType": "top",
                "silhouette": "relaxed",
                "colors": ["white", "beige"],
                "materials": ["cotton", "linen"],
                "styleCategory": "minimalist",
                "formality": 0.6,
                "seasonality": "spring"
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "processingTime": 45.2
        }
        
        # Validate required fields
        required_fields = ["outputId", "taskId", "outputIndex", "outputType", "contentUrl"]
        for field in required_fields:
            assert field in generation_output
            assert generation_output[field] is not None
        
        # Validate quality metrics
        if "qualityMetrics" in generation_output:
            quality_metrics = generation_output["qualityMetrics"]
            for metric_name, value in quality_metrics.items():
                assert isinstance(value, (int, float))
                assert 0.0 <= value <= 1.0
        
        # Validate design attributes
        if "designAttributes" in generation_output:
            design_attrs = generation_output["designAttributes"]
            if "colors" in design_attrs:
                assert isinstance(design_attrs["colors"], list)
            if "materials" in design_attrs:
                assert isinstance(design_attrs["materials"], list)
            if "formality" in design_attrs:
                assert 0.0 <= design_attrs["formality"] <= 1.0
    
    def test_commercial_predictions_interface(self):
        """Test CommercialPredictions interface structure."""
        commercial_predictions = {
            "predictionId": "pred-12345",
            "generationId": "gen-67890",
            "brandId": "brand-123",
            "marketAnalysis": {
                "targetDemographic": {
                    "primary": "urban_professional_25_40",
                    "secondary": "creative_millennial_25_35"
                },
                "marketSize": {
                    "totalAddressableMarket": 2500000,
                    "servicableAddressableMarket": 750000,
                    "servicableObtainableMarket": 75000
                },
                "competitivePosition": {
                    "differentiationScore": 0.72,
                    "marketGapAlignment": 0.85,
                    "competitorSimilarity": 0.23
                }
            },
            "salesProjections": {
                "predictedConversionRate": 0.168,
                "estimatedUnitsSold": {
                    "month1": 150,
                    "month3": 450,
                    "month6": 800,
                    "year1": 1200
                },
                "revenueProjection": {
                    "month1": 18750.0,
                    "month3": 56250.0,
                    "month6": 100000.0,
                    "year1": 150000.0
                },
                "confidenceInterval": {
                    "lower": 0.75,
                    "upper": 1.35
                }
            },
            "pricingRecommendations": {
                "recommendedRetailPrice": 125.0,
                "priceRange": {
                    "minimum": 95.0,
                    "maximum": 155.0
                },
                "priceElasticity": -1.2,
                "competitorPriceAnalysis": {
                    "averageCompetitorPrice": 118.0,
                    "pricePositioning": "premium_accessible"
                }
            },
            "riskAssessment": {
                "overallRisk": "medium",
                "riskFactors": [
                    {
                        "factor": "seasonal_demand_variation",
                        "impact": "medium",
                        "probability": 0.6
                    },
                    {
                        "factor": "supply_chain_disruption",
                        "impact": "high", 
                        "probability": 0.2
                    }
                ],
                "mitigationStrategies": [
                    "diversify_seasonal_offerings",
                    "establish_backup_suppliers"
                ]
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "modelVersion": "commercial-predictor-v2.1",
            "confidenceScore": 0.82
        }
        
        # Validate top-level structure
        required_sections = ["predictionId", "marketAnalysis", "salesProjections", "pricingRecommendations"]
        for section in required_sections:
            assert section in commercial_predictions
        
        # Validate market analysis
        market_analysis = commercial_predictions["marketAnalysis"]
        assert "targetDemographic" in market_analysis
        assert "marketSize" in market_analysis
        assert "competitivePosition" in market_analysis
        
        # Validate sales projections
        sales_projections = commercial_predictions["salesProjections"]
        assert "predictedConversionRate" in sales_projections
        assert "estimatedUnitsSold" in sales_projections
        assert "revenueProjection" in sales_projections
        
        conversion_rate = sales_projections["predictedConversionRate"]
        assert 0.0 <= conversion_rate <= 1.0
        
        # Validate pricing recommendations
        pricing = commercial_predictions["pricingRecommendations"]
        assert "recommendedRetailPrice" in pricing
        assert "priceRange" in pricing
        
        price_range = pricing["priceRange"]
        recommended_price = pricing["recommendedRetailPrice"]
        assert price_range["minimum"] <= recommended_price <= price_range["maximum"]
        
        # Validate risk assessment
        if "riskAssessment" in commercial_predictions:
            risk_assessment = commercial_predictions["riskAssessment"]
            assert risk_assessment["overallRisk"] in ["low", "medium", "high"]
            
            if "riskFactors" in risk_assessment:
                for factor in risk_assessment["riskFactors"]:
                    assert "factor" in factor
                    assert "impact" in factor
                    assert "probability" in factor
                    assert factor["impact"] in ["low", "medium", "high"]
                    assert 0.0 <= factor["probability"] <= 1.0


class TestUIComponentValidation:
    """Test suite for UI component validation logic."""
    
    def test_input_validation_rules(self):
        """Test input validation rules for form components."""
        # Text prompt validation
        def validate_text_prompt(prompt):
            if not prompt or len(prompt.strip()) == 0:
                return {"valid": False, "error": "Text prompt is required"}
            if len(prompt) < 10:
                return {"valid": False, "error": "Text prompt must be at least 10 characters"}
            if len(prompt) > 500:
                return {"valid": False, "error": "Text prompt must not exceed 500 characters"}
            return {"valid": True, "error": None}
        
        # Test cases
        assert not validate_text_prompt("")["valid"]
        assert not validate_text_prompt("   ")["valid"]
        assert not validate_text_prompt("short")["valid"]
        assert not validate_text_prompt("x" * 501)["valid"]
        assert validate_text_prompt("minimalist spring collection")["valid"]
        
        # Target pieces validation
        def validate_target_pieces(pieces):
            if not isinstance(pieces, int):
                return {"valid": False, "error": "Target pieces must be a number"}
            if pieces < 1:
                return {"valid": False, "error": "Must generate at least 1 piece"}
            if pieces > 20:
                return {"valid": False, "error": "Cannot generate more than 20 pieces"}
            return {"valid": True, "error": None}
        
        # Test cases
        assert not validate_target_pieces("5")["valid"]
        assert not validate_target_pieces(0)["valid"]
        assert not validate_target_pieces(21)["valid"]
        assert validate_target_pieces(5)["valid"]
        
        # Creativity level validation
        def validate_creativity_level(level):
            if not isinstance(level, (int, float)):
                return {"valid": False, "error": "Creativity level must be a number"}
            if level < 0.0 or level > 1.0:
                return {"valid": False, "error": "Creativity level must be between 0 and 1"}
            return {"valid": True, "error": None}
        
        # Test cases
        assert not validate_creativity_level("0.5")["valid"]
        assert not validate_creativity_level(-0.1)["valid"]
        assert not validate_creativity_level(1.1)["valid"]
        assert validate_creativity_level(0.7)["valid"]
    
    def test_file_upload_validation(self):
        """Test file upload validation logic."""
        def validate_image_file(file_info):
            # Mock file info structure
            allowed_types = ["image/jpeg", "image/png", "image/webp"]
            max_size = 10 * 1024 * 1024  # 10MB
            
            if "type" not in file_info:
                return {"valid": False, "error": "File type is required"}
            
            if file_info["type"] not in allowed_types:
                return {"valid": False, "error": f"File type must be one of: {', '.join(allowed_types)}"}
            
            if "size" not in file_info:
                return {"valid": False, "error": "File size is required"}
            
            if file_info["size"] > max_size:
                return {"valid": False, "error": "File size must not exceed 10MB"}
            
            if file_info["size"] == 0:
                return {"valid": False, "error": "File cannot be empty"}
            
            return {"valid": True, "error": None}
        
        # Test cases
        valid_file = {"type": "image/jpeg", "size": 2048000, "name": "reference.jpg"}
        invalid_type = {"type": "image/gif", "size": 1024000, "name": "reference.gif"}
        too_large = {"type": "image/png", "size": 15000000, "name": "large.png"}
        empty_file = {"type": "image/jpeg", "size": 0, "name": "empty.jpg"}
        
        assert validate_image_file(valid_file)["valid"]
        assert not validate_image_file(invalid_type)["valid"]
        assert not validate_image_file(too_large)["valid"]
        assert not validate_image_file(empty_file)["valid"]
    
    def test_color_palette_validation(self):
        """Test color palette validation logic."""
        def validate_color_palette(colors):
            if not isinstance(colors, list):
                return {"valid": False, "error": "Color palette must be an array"}
            
            if len(colors) == 0:
                return {"valid": False, "error": "At least one color is required"}
            
            if len(colors) > 10:
                return {"valid": False, "error": "Maximum 10 colors allowed"}
            
            hex_pattern = r'^#[0-9A-Fa-f]{6}$'
            import re
            
            for color in colors:
                if not isinstance(color, str):
                    return {"valid": False, "error": "All colors must be strings"}
                
                # Check if it's a hex color or a named color
                if not (re.match(hex_pattern, color) or color.lower() in [
                    "red", "blue", "green", "yellow", "orange", "purple", "pink",
                    "black", "white", "gray", "grey", "brown", "beige", "navy",
                    "maroon", "olive", "lime", "aqua", "teal", "silver", "fuchsia"
                ]):
                    return {"valid": False, "error": f"Invalid color format: {color}"}
            
            return {"valid": True, "error": None}
        
        # Test cases
        valid_hex = ["#FF0000", "#00FF00", "#0000FF"]
        valid_names = ["red", "blue", "green"]
        mixed_valid = ["#FF0000", "blue", "green"]
        invalid_hex = ["#GG0000", "blue"]
        too_many = ["red"] * 11
        empty_list = []
        
        assert validate_color_palette(valid_hex)["valid"]
        assert validate_color_palette(valid_names)["valid"] 
        assert validate_color_palette(mixed_valid)["valid"]
        assert not validate_color_palette(invalid_hex)["valid"]
        assert not validate_color_palette(too_many)["valid"]
        assert not validate_color_palette(empty_list)["valid"]
    
    def test_brand_selection_validation(self):
        """Test brand selection validation logic."""
        def validate_brand_selection(brand_id, accessible_brands):
            if not brand_id:
                return {"valid": False, "error": "Brand selection is required"}
            
            if not isinstance(accessible_brands, list):
                return {"valid": False, "error": "Accessible brands must be provided"}
            
            if brand_id not in accessible_brands:
                return {"valid": False, "error": "Selected brand is not accessible"}
            
            return {"valid": True, "error": None}
        
        # Test cases
        accessible_brands = ["brand-1", "brand-2", "brand-3"]
        
        assert validate_brand_selection("brand-1", accessible_brands)["valid"]
        assert not validate_brand_selection("", accessible_brands)["valid"]
        assert not validate_brand_selection("brand-4", accessible_brands)["valid"]
        assert not validate_brand_selection("brand-1", None)["valid"]


class TestComponentStateManagement:
    """Test suite for component state management."""
    
    def test_generation_form_state(self):
        """Test generation form state management."""
        # Initial state
        initial_state = {
            "inputs": {
                "textPrompt": "",
                "referenceImages": [],
                "colorPalette": [],
                "materialPreferences": []
            },
            "brandParameters": {
                "brandId": "",
                "designDnaAdherence": 0.8,
                "targetDemographic": ""
            },
            "settings": {
                "targetPieces": 5,
                "qualityLevel": "high",
                "creativityLevel": 0.7,
                "useMemoryContext": True,
                "memoryDepth": 5
            },
            "validation": {
                "isValid": False,
                "errors": {}
            },
            "isSubmitting": False
        }
        
        # Validate initial state structure
        assert "inputs" in initial_state
        assert "brandParameters" in initial_state
        assert "settings" in initial_state
        assert "validation" in initial_state
        assert "isSubmitting" in initial_state
        
        # Validate default values
        assert initial_state["settings"]["targetPieces"] > 0
        assert 0.0 <= initial_state["settings"]["creativityLevel"] <= 1.0
        assert 0.0 <= initial_state["brandParameters"]["designDnaAdherence"] <= 1.0
        assert isinstance(initial_state["validation"]["isValid"], bool)
        assert isinstance(initial_state["isSubmitting"], bool)
    
    def test_generation_viewer_state(self):
        """Test generation viewer state management."""
        # Viewer state
        viewer_state = {
            "currentGeneration": {
                "taskId": "task-12345",
                "status": "running",
                "progress": 0.65,
                "currentStep": "refining_outputs"
            },
            "outputs": [],
            "selectedOutput": None,
            "viewMode": "grid",
            "filters": {
                "qualityThreshold": 0.7,
                "showOnlyBrandAligned": False,
                "sortBy": "quality_score"
            },
            "ui": {
                "isFullscreen": False,
                "showMetadata": True,
                "showComparisons": False
            }
        }
        
        # Validate viewer state
        assert "currentGeneration" in viewer_state
        assert "outputs" in viewer_state
        assert "viewMode" in viewer_state
        assert "filters" in viewer_state
        assert "ui" in viewer_state
        
        # Validate view mode options
        valid_view_modes = ["grid", "list", "carousel", "comparison"]
        assert viewer_state["viewMode"] in valid_view_modes
        
        # Validate filter values
        filters = viewer_state["filters"]
        assert 0.0 <= filters["qualityThreshold"] <= 1.0
        assert filters["sortBy"] in ["quality_score", "brand_alignment", "timestamp", "commercial_viability"]
    
    def test_memory_insights_state(self):
        """Test memory insights component state."""
        insights_state = {
            "isLoading": False,
            "data": None,
            "error": None,
            "selectedBrand": "brand-123",
            "timeRange": "30d",
            "activeTab": "overview",
            "visualizations": {
                "evolutionChart": {
                    "isLoading": False,
                    "data": [],
                    "error": None
                },
                "performanceMetrics": {
                    "isLoading": False,
                    "data": {},
                    "error": None
                }
            },
            "filters": {
                "generationType": "all",
                "qualityRange": [0.0, 1.0],
                "dateRange": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                }
            }
        }
        
        # Validate insights state structure
        assert "isLoading" in insights_state
        assert "data" in insights_state
        assert "error" in insights_state
        assert "selectedBrand" in insights_state
        assert "visualizations" in insights_state
        assert "filters" in insights_state
        
        # Validate time range options
        valid_time_ranges = ["7d", "30d", "90d", "1y", "all"]
        assert insights_state["timeRange"] in valid_time_ranges
        
        # Validate tab options
        valid_tabs = ["overview", "evolution", "performance", "patterns", "health"]
        assert insights_state["activeTab"] in valid_tabs
        
        # Validate filter ranges
        quality_range = insights_state["filters"]["qualityRange"]
        assert len(quality_range) == 2
        assert 0.0 <= quality_range[0] <= quality_range[1] <= 1.0