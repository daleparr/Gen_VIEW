"""
KSE Memory Service Test Suite
Tests for temporal knowledge graphs, cross-modal embeddings, and commercial feedback loops
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

from services.generation_api.src.services.kse_memory_service import (
    KSEMemoryService, 
    MultiModalInputs, 
    CommercialOutcomes,
    KnowledgeGraph,
    EmbeddingService,
    VectorStore,
    FeedbackLoop,
    TemporalReasoner
)


class TestKSEMemoryService:
    """Test suite for KSE Memory Service."""
    
    @pytest.fixture
    def sample_multimodal_inputs(self):
        """Sample multi-modal inputs for testing."""
        return MultiModalInputs(
            modalities=['text', 'images', 'colors'],
            embeddings={
                'text': [0.1] * 512,
                'images': [[0.2] * 512, [0.3] * 512],
                'colors': [0.4] * 512
            },
            metadata={
                'text_prompt': 'minimalist spring collection',
                'reference_images': ['https://example.com/ref1.jpg'],
                'color_palette': ['white', 'beige', 'black'],
                'brand_context': {
                    'brand_id': str(uuid.uuid4()),
                    'aesthetic': 'minimalist'
                }
            }
        )
    
    @pytest.fixture
    def sample_commercial_outcomes(self):
        """Sample commercial outcomes for testing."""
        return CommercialOutcomes(
            conversion_rate=0.15,
            revenue=25000.0,
            user_engagement={
                'time_on_page': 45.2,
                'bounce_rate': 0.25,
                'social_shares': 12
            }
        )
    
    @pytest.mark.asyncio
    async def test_store_generation_context(
        self, 
        mock_kse_memory_service, 
        sample_multimodal_inputs,
        sample_commercial_outcomes
    ):
        """Test storing generation context in KSE memory."""
        generation_id = str(uuid.uuid4())
        mock_outputs = {'outputs': [{'id': 'output_1', 'quality': 0.85}]}
        
        await mock_kse_memory_service.store_generation_context(
            generation_id,
            sample_multimodal_inputs,
            mock_outputs,
            sample_commercial_outcomes
        )
        
        # Verify storage
        assert generation_id in mock_kse_memory_service.memory_store
        stored_data = mock_kse_memory_service.memory_store[generation_id]
        
        assert stored_data['inputs'] == sample_multimodal_inputs
        assert stored_data['outputs'] == mock_outputs
        assert stored_data['commercial_data'] == sample_commercial_outcomes
        assert 'stored_at' in stored_data
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_context(
        self, 
        mock_kse_memory_service,
        sample_multimodal_inputs
    ):
        """Test retrieving relevant context from KSE memory."""
        brand_id = str(uuid.uuid4())
        
        context = await mock_kse_memory_service.retrieve_relevant_context(
            sample_multimodal_inputs.metadata,
            brand_id=brand_id,
            depth=5
        )
        
        # Verify context structure
        assert 'memory_nodes' in context
        assert 'temporal_context' in context
        assert 'design_evolution' in context
        assert 'brand_consistency_patterns' in context
        assert 'commercial_insights' in context
        
        # Verify memory nodes
        memory_nodes = context['memory_nodes']
        assert len(memory_nodes) <= 5  # Respects depth limit
        
        for node in memory_nodes:
            assert 'id' in node
            assert 'similarity_score' in node
            assert 'metadata' in node
    
    @pytest.mark.asyncio
    async def test_integrate_feedback(
        self, 
        mock_kse_memory_service,
        mock_redis_client
    ):
        """Test integrating feedback into KSE memory."""
        generation_id = str(uuid.uuid4())
        commercial_outcomes = {
            'conversion_rate': 0.18,
            'revenue': 30000.0
        }
        user_ratings = {
            'overall_rating': 4.5,
            'comments': 'Excellent collection!'
        }
        
        await mock_kse_memory_service.integrate_feedback(
            generation_id,
            commercial_outcomes=commercial_outcomes,
            user_ratings=user_ratings
        )
        
        # Verify feedback storage
        assert generation_id in mock_kse_memory_service.feedback_store
        feedback_data = mock_kse_memory_service.feedback_store[generation_id]
        
        assert feedback_data['commercial_outcomes'] == commercial_outcomes
        assert feedback_data['user_ratings'] == user_ratings
        assert 'integrated_at' in feedback_data
    
    @pytest.mark.asyncio
    async def test_get_brand_memory_insights(
        self, 
        mock_kse_memory_service
    ):
        """Test getting comprehensive brand memory insights."""
        brand_id = str(uuid.uuid4())
        
        insights = await mock_kse_memory_service.get_brand_memory_insights(brand_id)
        
        # Verify insights structure
        assert 'total_nodes' in insights
        assert 'recent_generations' in insights
        assert 'design_evolution' in insights
        assert 'commercial_performance' in insights
        assert 'temporal_patterns' in insights
        assert 'memory_health' in insights
        assert 'learning_velocity' in insights
        
        # Verify data types and ranges
        assert isinstance(insights['total_nodes'], int)
        assert insights['total_nodes'] >= 0
        
        assert isinstance(insights['recent_generations'], list)
        
        design_evolution = insights['design_evolution']
        assert 0.0 <= design_evolution['evolution_velocity'] <= 1.0
        assert 0.0 <= design_evolution['innovation_index'] <= 1.0
        
        learning_velocity = insights['learning_velocity']
        assert learning_velocity['velocity_category'] in ['minimal', 'slow', 'moderate', 'rapid']


class TestKnowledgeGraph:
    """Test suite for Knowledge Graph component."""
    
    @pytest.fixture
    def knowledge_graph(self):
        """Create knowledge graph instance for testing."""
        return KnowledgeGraph()
    
    @pytest.fixture
    def sample_generation_inputs(self):
        """Sample generation inputs for knowledge graph testing."""
        return MultiModalInputs(
            modalities=['text', 'images'],
            embeddings={'text': [0.1] * 512, 'images': [[0.2] * 512]},
            metadata={
                'text_prompt': 'modern capsule collection',
                'brand_context': {'brand_id': str(uuid.uuid4())}
            }
        )
    
    @pytest.mark.asyncio
    async def test_add_generation_node(
        self, 
        knowledge_graph, 
        sample_generation_inputs,
        mock_redis_client
    ):
        """Test adding generation node to knowledge graph."""
        generation_id = str(uuid.uuid4())
        mock_outputs = [{'id': 'output_1', 'quality': 0.85}]
        timestamp = datetime.utcnow()
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await knowledge_graph.add_generation_node(
                generation_id,
                sample_generation_inputs,
                mock_outputs,
                timestamp
            )
        
        # Verify node was stored
        node_key = f"kg_node:{generation_id}"
        assert await mock_redis_client.exists(node_key)
        
        node_data = await mock_redis_client.get(node_key)
        assert node_data['id'] == generation_id
        assert node_data['type'] == 'generation'
        assert node_data['timestamp'] == timestamp.isoformat()
    
    @pytest.mark.asyncio
    async def test_get_design_evolution(
        self, 
        knowledge_graph,
        mock_redis_client
    ):
        """Test getting design evolution patterns."""
        brand_id = str(uuid.uuid4())
        
        # Mock stored generation data
        generation_ids = [str(uuid.uuid4()) for _ in range(3)]
        mock_redis_client.lists[f"kg_brand:{brand_id}"] = generation_ids
        
        for i, gen_id in enumerate(generation_ids):
            mock_redis_client.data[f"kg_node:{gen_id}"] = {
                'value': {
                    'id': gen_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'inputs': {'modalities': ['text', 'images']},
                    'outputs': {'quality_scores': [0.8 + i * 0.05]}
                }
            }
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            evolution = await knowledge_graph.get_design_evolution(brand_id, depth=5)
        
        # Verify evolution structure
        assert 'generations' in evolution
        assert 'evolution_trends' in evolution
        assert 'consistency_score' in evolution
        
        # Verify trend analysis
        if len(evolution['generations']) >= 2:
            trends = evolution['evolution_trends']
            assert 'trend' in trends
            assert trends['trend'] in ['improving', 'declining', 'stable', 'insufficient_data']
    
    @pytest.mark.asyncio
    async def test_get_recent_generations(
        self, 
        knowledge_graph,
        mock_redis_client
    ):
        """Test getting recent generations for a brand."""
        brand_id = str(uuid.uuid4())
        
        # Mock recent generations
        generation_ids = [str(uuid.uuid4()) for _ in range(5)]
        mock_redis_client.lists[f"kg_brand:{brand_id}"] = generation_ids
        
        for gen_id in generation_ids:
            mock_redis_client.data[f"kg_node:{gen_id}"] = {
                'value': {
                    'id': gen_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'type': 'generation'
                }
            }
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            recent_gens = await knowledge_graph.get_recent_generations(brand_id, limit=3)
        
        assert len(recent_gens) <= 3
        for gen in recent_gens:
            assert 'id' in gen
            assert 'timestamp' in gen
            assert 'type' in gen
    
    def test_calculate_consistency_score(self, knowledge_graph):
        """Test consistency score calculation."""
        # Test with consistent modalities
        consistent_data = [
            {'inputs': {'modalities': ['text', 'images']}},
            {'inputs': {'modalities': ['text', 'images']}},
            {'inputs': {'modalities': ['text', 'images']}}
        ]
        
        score = knowledge_graph._calculate_consistency_score(consistent_data)
        assert score == 1.0  # Perfect consistency
        
        # Test with varying modalities
        varying_data = [
            {'inputs': {'modalities': ['text', 'images']}},
            {'inputs': {'modalities': ['text', 'colors']}},
            {'inputs': {'modalities': ['images', 'materials']}}
        ]
        
        score = knowledge_graph._calculate_consistency_score(varying_data)
        assert 0.0 <= score <= 1.0
        assert score < 1.0  # Less than perfect consistency


class TestEmbeddingService:
    """Test suite for Embedding Service."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance for testing."""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_encode_multimodal(
        self, 
        embedding_service, 
        sample_multimodal_inputs
    ):
        """Test multi-modal encoding."""
        mock_outputs = {'outputs': [{'id': 'output_1'}]}
        
        embeddings = await embedding_service.encode_multimodal(
            sample_multimodal_inputs,
            mock_outputs
        )
        
        # Verify embedding structure
        assert isinstance(embeddings, dict)
        assert 'output' in embeddings
        
        # Verify modality embeddings are preserved
        for modality in sample_multimodal_inputs.modalities:
            if modality in sample_multimodal_inputs.embeddings:
                assert modality in embeddings
    
    @pytest.mark.asyncio
    async def test_encode_query(self, embedding_service):
        """Test query encoding for similarity search."""
        query_inputs = {
            'embeddings': {
                'text': [0.1] * 100,
                'images': [[0.2] * 100, [0.3] * 100],
                'colors': [0.4] * 100
            }
        }
        
        query_embedding = await embedding_service.encode_query(query_inputs)
        
        # Verify query embedding
        assert isinstance(query_embedding, list)
        assert len(query_embedding) == 512  # Standard size
        assert all(isinstance(x, float) for x in query_embedding)
    
    @pytest.mark.asyncio
    async def test_encode_outputs(self, embedding_service):
        """Test output encoding."""
        mock_outputs = {'outputs': [{'id': 'output_1', 'content': 'generated_image'}]}
        
        output_embedding = await embedding_service._encode_outputs(mock_outputs)
        
        assert isinstance(output_embedding, list)
        assert len(output_embedding) == 512
        assert all(isinstance(x, float) for x in output_embedding)


class TestVectorStore:
    """Test suite for Vector Store."""
    
    @pytest.fixture
    def vector_store(self):
        """Create vector store instance for testing."""
        return VectorStore()
    
    @pytest.mark.asyncio
    async def test_upsert_embeddings(
        self, 
        vector_store,
        mock_redis_client
    ):
        """Test storing embeddings in vector database."""
        generation_id = str(uuid.uuid4())
        embeddings = {
            'text': [0.1] * 100,
            'images': [0.2] * 100,
            'colors': [0.3] * 100
        }
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await vector_store.upsert(generation_id, embeddings)
        
        # Verify storage
        embedding_key = f"embedding:{generation_id}"
        assert await mock_redis_client.exists(embedding_key)
        
        stored_data = await mock_redis_client.get(embedding_key)
        assert 'embedding' in stored_data
        assert 'metadata' in stored_data
        assert stored_data['metadata']['generation_id'] == generation_id
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, vector_store):
        """Test similarity search functionality."""
        query_embedding = [0.1] * 512
        
        results = await vector_store.similarity_search(
            query_embedding,
            limit=5,
            filters={'brand_id': 'test_brand'}
        )
        
        # Verify search results
        assert isinstance(results, list)
        assert len(results) <= 5
        
        for result in results:
            assert 'id' in result
            assert 'similarity_score' in result
            assert 'metadata' in result
            assert 0.0 <= result['similarity_score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_find_style_bridges(self, vector_store):
        """Test finding style bridge patterns."""
        source_embedding = [0.1] * 512
        target_embedding = [0.2] * 512
        brand_id = str(uuid.uuid4())
        
        bridges = await vector_store.find_style_bridges(
            source_embedding,
            target_embedding,
            brand_id
        )
        
        assert isinstance(bridges, list)
        for bridge in bridges:
            assert 'bridge_id' in bridge
            assert 'compatibility_score' in bridge
            assert 'success_rate' in bridge
            assert 0.0 <= bridge['compatibility_score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_get_brand_patterns(self, vector_store):
        """Test getting brand-specific patterns."""
        brand_id = str(uuid.uuid4())
        
        patterns = await vector_store.get_brand_patterns(brand_id)
        
        assert isinstance(patterns, dict)
        assert 'dominant_styles' in patterns
        assert 'color_preferences' in patterns
        assert 'consistency_score' in patterns
        assert 0.0 <= patterns['consistency_score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_count_brand_nodes(
        self, 
        vector_store,
        mock_redis_client
    ):
        """Test counting memory nodes for a brand."""
        brand_id = str(uuid.uuid4())
        
        # Mock brand nodes
        generation_ids = [str(uuid.uuid4()) for _ in range(10)]
        mock_redis_client.lists[f"kg_brand:{brand_id}"] = generation_ids
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            count = await vector_store.count_brand_nodes(brand_id)
        
        assert count == 10


class TestFeedbackLoop:
    """Test suite for Feedback Loop."""
    
    @pytest.fixture
    def feedback_loop(self):
        """Create feedback loop instance for testing."""
        return FeedbackLoop()
    
    @pytest.mark.asyncio
    async def test_integrate_outcomes(
        self, 
        feedback_loop,
        sample_commercial_outcomes,
        mock_redis_client
    ):
        """Test integrating commercial outcomes."""
        generation_id = str(uuid.uuid4())
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await feedback_loop.integrate_outcomes(generation_id, sample_commercial_outcomes)
        
        # Verify outcome storage
        outcome_key = f"commercial_outcome:{generation_id}"
        assert await mock_redis_client.exists(outcome_key)
        
        stored_outcome = await mock_redis_client.get(outcome_key)
        assert stored_outcome['generation_id'] == generation_id
        assert stored_outcome['conversion_rate'] == sample_commercial_outcomes.conversion_rate
        assert stored_outcome['revenue'] == sample_commercial_outcomes.revenue
    
    @pytest.mark.asyncio
    async def test_process_feedback(
        self, 
        feedback_loop,
        mock_redis_client
    ):
        """Test processing feedback for learning updates."""
        generation_id = str(uuid.uuid4())
        commercial_outcomes = {'conversion_rate': 0.18}
        user_ratings = {'overall_rating': 4.5}
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await feedback_loop.process_feedback(
                generation_id,
                commercial_outcomes,
                user_ratings
            )
        
        # Verify feedback processing
        feedback_key = f"processed_feedback:{generation_id}"
        assert await mock_redis_client.exists(feedback_key)
        
        processed_feedback = await mock_redis_client.get(feedback_key)
        assert processed_feedback['generation_id'] == generation_id
        assert processed_feedback['commercial_outcomes'] == commercial_outcomes
        assert processed_feedback['user_ratings'] == user_ratings
    
    @pytest.mark.asyncio
    async def test_get_performance_patterns(self, feedback_loop):
        """Test getting commercial performance patterns."""
        brand_id = str(uuid.uuid4())
        
        patterns = await feedback_loop.get_performance_patterns(brand_id)
        
        assert isinstance(patterns, dict)
        assert 'average_conversion_rate' in patterns
        assert 'revenue_trend' in patterns
        assert 'top_performing_styles' in patterns
        assert 'engagement_metrics' in patterns
        
        # Verify data types
        assert isinstance(patterns['average_conversion_rate'], float)
        assert patterns['revenue_trend'] in ['increasing', 'decreasing', 'stable']
        assert isinstance(patterns['top_performing_styles'], list)
    
    @pytest.mark.asyncio
    async def test_get_recent_feedback(self, feedback_loop):
        """Test getting recent feedback for a brand."""
        brand_id = str(uuid.uuid4())
        
        recent_feedback = await feedback_loop.get_recent_feedback(brand_id, days=30)
        
        assert isinstance(recent_feedback, list)
        for feedback in recent_feedback:
            assert 'generation_id' in feedback
            assert 'rating' in feedback
            assert 'timestamp' in feedback


class TestTemporalReasoner:
    """Test suite for Temporal Reasoner."""
    
    @pytest.fixture
    def temporal_reasoner(self):
        """Create temporal reasoner instance for testing."""
        return TemporalReasoner()
    
    @pytest.mark.asyncio
    async def test_update_patterns(
        self, 
        temporal_reasoner,
        sample_multimodal_inputs,
        mock_redis_client
    ):
        """Test updating temporal patterns."""
        generation_id = str(uuid.uuid4())
        mock_outputs = {'outputs': [{'id': 'output_1'}]}
        timestamp = datetime.utcnow()
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await temporal_reasoner.update_patterns(
                generation_id,
                sample_multimodal_inputs,
                mock_outputs,
                timestamp
            )
        
        # Verify pattern update
        patterns_key = "temporal_patterns"
        patterns_list = await mock_redis_client.get_list(patterns_key)
        
        assert len(patterns_list) > 0
        latest_pattern = patterns_list[-1]
        assert latest_pattern['generation_id'] == generation_id
        assert latest_pattern['timestamp'] == timestamp.isoformat()
    
    @pytest.mark.asyncio
    async def test_get_temporal_context(self, temporal_reasoner):
        """Test getting temporal context from memory nodes."""
        memory_nodes = [
            {'id': 'node_1', 'timestamp': datetime.utcnow().isoformat()},
            {'id': 'node_2', 'timestamp': datetime.utcnow().isoformat()}
        ]
        brand_id = str(uuid.uuid4())
        
        context = await temporal_reasoner.get_temporal_context(memory_nodes, brand_id)
        
        assert isinstance(context, dict)
        assert 'temporal_coherence' in context
        assert 'evolution_stage' in context
        assert 'seasonal_patterns' in context
        assert 'trend_alignment' in context
        
        # Verify value ranges
        assert 0.0 <= context['temporal_coherence'] <= 1.0
        assert 0.0 <= context['trend_alignment'] <= 1.0
        assert context['evolution_stage'] in ['emerging', 'growing', 'mature', 'declining']
    
    @pytest.mark.asyncio
    async def test_integrate_feedback(
        self, 
        temporal_reasoner,
        mock_redis_client
    ):
        """Test integrating feedback into temporal reasoning."""
        generation_id = str(uuid.uuid4())
        commercial_outcomes = {'conversion_rate': 0.18}
        user_ratings = {'overall_rating': 4.5}
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await temporal_reasoner.integrate_feedback(
                generation_id,
                commercial_outcomes,
                user_ratings
            )
        
        # Verify feedback integration
        feedback_key = "temporal_feedback"
        feedback_list = await mock_redis_client.get_list(feedback_key)
        
        assert len(feedback_list) > 0
        latest_feedback = feedback_list[-1]
        assert latest_feedback['generation_id'] == generation_id
        assert latest_feedback['feedback_type'] == 'commercial'
        assert 'impact_score' in latest_feedback
    
    def test_calculate_feedback_impact(self, temporal_reasoner):
        """Test calculating feedback impact score."""
        # Test with commercial outcomes only
        commercial_outcomes = {'conversion_rate': 0.2}
        impact = temporal_reasoner._calculate_feedback_impact(commercial_outcomes, None)
        
        assert 0.0 <= impact <= 1.0
        assert impact > 0.5  # Should be above base impact
        
        # Test with user ratings only
        user_ratings = {'overall_rating': 4.0}
        impact = temporal_reasoner._calculate_feedback_impact(None, user_ratings)
        
        assert 0.0 <= impact <= 1.0
        
        # Test with both
        impact = temporal_reasoner._calculate_feedback_impact(commercial_outcomes, user_ratings)
        
        assert 0.0 <= impact <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_design_evolution(self, temporal_reasoner):
        """Test analyzing design evolution patterns."""
        brand_id = str(uuid.uuid4())
        
        evolution = await temporal_reasoner.analyze_design_evolution(brand_id)
        
        assert isinstance(evolution, dict)
        assert 'evolution_velocity' in evolution
        assert 'consistency_trend' in evolution
        assert 'innovation_index' in evolution
        assert 'market_alignment' in evolution
        
        # Verify value ranges
        assert 0.0 <= evolution['evolution_velocity'] <= 1.0
        assert 0.0 <= evolution['innovation_index'] <= 1.0
        assert 0.0 <= evolution['market_alignment'] <= 1.0
        assert evolution['consistency_trend'] in ['improving', 'declining', 'stable']
    
    @pytest.mark.asyncio
    async def test_get_temporal_patterns(self, temporal_reasoner):
        """Test getting temporal patterns for a brand."""
        brand_id = str(uuid.uuid4())
        
        patterns = await temporal_reasoner.get_temporal_patterns(brand_id)
        
        assert isinstance(patterns, dict)
        assert 'seasonal_cycles' in patterns
        assert 'trend_cycles' in patterns
        assert 'innovation_rhythm' in patterns
        assert 'consistency_patterns' in patterns
        
        # Verify data types
        assert isinstance(patterns['seasonal_cycles'], list)
        assert isinstance(patterns['trend_cycles'], list)
    
    @pytest.mark.asyncio
    async def test_priority_pattern_update(
        self, 
        temporal_reasoner,
        mock_redis_client
    ):
        """Test triggering priority pattern updates."""
        generation_id = str(uuid.uuid4())
        
        with patch('services.generation_api.src.services.kse_memory_service.redis_manager', mock_redis_client):
            await temporal_reasoner.priority_pattern_update(generation_id)
        
        # Verify priority update
        updates_key = "priority_pattern_updates"
        updates_list = await mock_redis_client.get_list(updates_key)
        
        assert len(updates_list) > 0
        latest_update = updates_list[-1]
        assert latest_update['generation_id'] == generation_id
        assert latest_update['priority'] == 'high'
    
    @pytest.mark.asyncio
    async def test_calculate_improvement_trend(self, temporal_reasoner):
        """Test calculating improvement trend for a brand."""
        brand_id = str(uuid.uuid4())
        
        trend = await temporal_reasoner.calculate_improvement_trend(brand_id)
        
        assert isinstance(trend, float)
        assert 0.0 <= trend <= 1.0


@pytest.mark.integration
class TestKSEMemoryIntegration:
    """Integration tests for KSE Memory Service components."""
    
    @pytest.mark.asyncio
    async def test_complete_memory_workflow(
        self, 
        mock_kse_memory_service,
        sample_multimodal_inputs,
        sample_commercial_outcomes
    ):
        """Test complete memory workflow from storage to retrieval."""
        generation_id = str(uuid.uuid4())
        brand_id = str(uuid.uuid4())
        
        # 1. Store generation context
        mock_outputs = {'outputs': [{'id': 'output_1', 'quality': 0.85}]}
        
        await mock_kse_memory_service.store_generation_context(
            generation_id,
            sample_multimodal_inputs,
            mock_outputs,
            sample_commercial_outcomes
        )
        
        # 2. Retrieve relevant context
        context = await mock_kse_memory_service.retrieve_relevant_context(
            sample_multimodal_inputs.metadata,
            brand_id=brand_id,
            depth=5
        )
        
        assert 'memory_nodes' in context
        assert 'temporal_context' in context
        
        # 3. Integrate feedback
        await mock_kse_memory_service.integrate_feedback(
            generation_id,
            commercial_outcomes={'conversion_rate': 0.2},
            user_ratings={'overall_rating': 4.5}
        )
        
        # 4. Get brand insights
        insights = await mock_kse_memory_service.get_brand_memory_insights(brand_id)
        
        assert 'total_nodes' in insights
        assert 'learning_velocity' in insights
    
    @pytest.mark.asyncio
    async def test_memory_performance_under_load(
        self, 
        mock_kse_memory_service,
        sample_multimodal_inputs
    ):
        """Test memory service performance under concurrent load."""
        tasks = []
        
        # Create multiple concurrent operations
        for i in range(10):
            generation_id = str(uuid.uuid4())
            brand_id = str(uuid.uuid4())
            
            # Store operation
            store_task = mock_kse_memory_service.store_generation_context(
                generation_id,
                sample_multimodal_inputs,
                {'outputs': [{'id': f'output_{i}'}]}
            )
            tasks.append(store_task)
            
            # Retrieve operation
            retrieve_task = mock_kse_memory_service.retrieve_relevant_context(
                sample_multimodal_inputs.metadata,
                brand_id=brand_id
            )
            tasks.append(retrieve_task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0
        
        # Verify operations completed successfully
        assert len(results) == 20  # 10 store + 10 retrieve operations
    
    @pytest.mark.asyncio
    async def test_memory_consistency(
        self, 
        mock_kse_memory_service,
        sample_multimodal_inputs
    ):
        """Test memory consistency across operations."""
        generation_id = str(uuid.uuid4())
        brand_id = str(uuid.uuid4())
        
        # Store initial context
        initial_outputs = {'outputs': [{'id': 'output_1', 'quality': 0.8}]}
        
        await mock_kse_memory_service.store_generation_context(
            generation_id,
            sample_multimodal_inputs,
            initial_outputs
        )
        
        # Verify storage
        assert generation_id in mock_kse_memory_service.memory_store
        stored_data = mock_kse_memory_service.memory_store[generation_id]
        assert stored_data['outputs'] == initial_outputs
        
        # Add feedback
        await mock_kse_memory_service.integrate_feedback(
            generation_id,
            commercial_outcomes={'conversion_rate': 0.15}
        )
        
        # Verify feedback integration
        assert generation_id in mock_kse_memory_service.feedback_store
        
        # Retrieve context and verify consistency
        context = await mock_kse_memory_service.retrieve_relevant_context(
            sample_multimodal_inputs.metadata,
            brand_id=brand_id
        )
        
        # Context should be consistent and contain expected structure
        assert isinstance(context, dict)
        assert 'memory_nodes' in context
        assert len(context['memory_nodes']) >= 0