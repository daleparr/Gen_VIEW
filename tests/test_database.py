"""
Database Test Suite
Tests for SQLAlchemy models, relationships, and database operations
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from services.generation_api.src.models.fashion_models import (
    Brand, Collection, Product, DesignDNA
)
from services.generation_api.src.models.generation_models import (
    GenerationJob, GenerationOutput, GenerationFeedback, GenerationType, GenerationStatus
)
from services.generation_api.src.models.user_models import (
    User, UserRole
)


class TestFashionModels:
    """Test suite for fashion domain models."""
    
    @pytest.mark.asyncio
    async def test_create_brand(self, test_db_session: AsyncSession, sample_brand_data):
        """Test creating a brand entity."""
        brand = Brand(
            id=uuid.UUID(sample_brand_data["id"]),
            name=sample_brand_data["name"],
            description=sample_brand_data["description"],
            design_dna=sample_brand_data["design_dna"],
            target_demographic=sample_brand_data["target_demographic"],
            market_segment=sample_brand_data["market_segment"]
        )
        
        test_db_session.add(brand)
        await test_db_session.commit()
        
        # Verify brand was created
        result = await test_db_session.get(Brand, uuid.UUID(sample_brand_data["id"]))
        assert result is not None
        assert result.name == sample_brand_data["name"]
        assert result.description == sample_brand_data["description"]
        assert result.market_segment == sample_brand_data["market_segment"]
        assert result.is_active is True
        assert result.created_at is not None
    
    @pytest.mark.asyncio
    async def test_brand_design_dna_json(self, test_db_session: AsyncSession):
        """Test brand design DNA JSON field handling."""
        design_dna = {
            "aesthetic": "minimalist",
            "sustainability_focus": True,
            "color_preference": ["black", "white", "beige"],
            "silhouette_style": "clean_lines",
            "innovation_level": 0.7
        }
        
        brand = Brand(
            name="Test Brand with DNA",
            description="Testing design DNA storage",
            design_dna=design_dna,
            market_segment="luxury"
        )
        
        test_db_session.add(brand)
        await test_db_session.commit()
        
        # Retrieve and verify JSON data
        result = await test_db_session.get(Brand, brand.id)
        assert result.design_dna == design_dna
        assert result.design_dna["aesthetic"] == "minimalist"
        assert result.design_dna["sustainability_focus"] is True
        assert len(result.design_dna["color_preference"]) == 3
    
    @pytest.mark.asyncio
    async def test_create_collection(
        self, 
        test_db_session: AsyncSession, 
        sample_brand_data, 
        sample_collection_data
    ):
        """Test creating a collection with brand relationship."""
        # First create a brand
        brand = Brand(
            id=uuid.UUID(sample_brand_data["id"]),
            name=sample_brand_data["name"],
            description=sample_brand_data["description"],
            market_segment=sample_brand_data["market_segment"]
        )
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create collection
        collection = Collection(
            id=uuid.UUID(sample_collection_data["id"]),
            name=sample_collection_data["name"],
            description=sample_collection_data["description"],
            brand_id=brand.id,
            season=sample_collection_data["season"],
            year=sample_collection_data["year"],
            theme=sample_collection_data["theme"],
            target_pieces=sample_collection_data["target_pieces"]
        )
        
        test_db_session.add(collection)
        await test_db_session.commit()
        
        # Verify collection and relationship
        result = await test_db_session.get(Collection, uuid.UUID(sample_collection_data["id"]))
        assert result is not None
        assert result.name == sample_collection_data["name"]
        assert result.brand_id == brand.id
        assert result.season == sample_collection_data["season"]
        assert result.year == sample_collection_data["year"]
        
        # Test relationship loading
        await test_db_session.refresh(result, ["brand"])
        assert result.brand is not None
        assert result.brand.name == sample_brand_data["name"]
    
    @pytest.mark.asyncio
    async def test_create_product(self, test_db_session: AsyncSession):
        """Test creating a product with full specifications."""
        # Create brand first
        brand = Brand(
            name="Product Test Brand",
            description="Brand for product testing",
            market_segment="mid-market"
        )
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create collection
        collection = Collection(
            name="Test Product Collection",
            brand_id=brand.id,
            season="spring",
            year=2024,
            target_pieces=3
        )
        test_db_session.add(collection)
        await test_db_session.flush()
        
        # Create product
        product = Product(
            name="Test Minimalist Top",
            description="A clean, minimalist top design",
            brand_id=brand.id,
            collection_id=collection.id,
            garment_type="top",
            design_dna={
                "silhouette": "relaxed",
                "materials": ["cotton", "linen"],
                "colors": ["white", "beige"],
                "style_attributes": {
                    "formality": 0.6,
                    "comfort": 0.9,
                    "versatility": 0.8
                }
            },
            target_price=85.00,
            generated_by_ai=True
        )
        
        test_db_session.add(product)
        await test_db_session.commit()
        
        # Verify product creation
        result = await test_db_session.get(Product, product.id)
        assert result is not None
        assert result.name == "Test Minimalist Top"
        assert result.garment_type == "top"
        assert result.target_price == 85.00
        assert result.generated_by_ai is True
        assert result.design_dna["silhouette"] == "relaxed"
        assert len(result.design_dna["materials"]) == 2
    
    @pytest.mark.asyncio
    async def test_brand_collections_relationship(self, test_db_session: AsyncSession):
        """Test one-to-many relationship between brands and collections."""
        # Create brand
        brand = Brand(
            name="Multi-Collection Brand",
            description="Brand with multiple collections",
            market_segment="luxury"
        )
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create multiple collections
        collections = []
        for i in range(3):
            collection = Collection(
                name=f"Collection {i+1}",
                brand_id=brand.id,
                season="spring" if i % 2 == 0 else "fall",
                year=2024,
                target_pieces=5 + i
            )
            collections.append(collection)
            test_db_session.add(collection)
        
        await test_db_session.commit()
        
        # Query brand with collections
        stmt = select(Brand).where(Brand.id == brand.id)
        result = await test_db_session.execute(stmt)
        brand_with_collections = result.scalar_one()
        
        # Load collections relationship
        await test_db_session.refresh(brand_with_collections, ["collections"])
        
        assert len(brand_with_collections.collections) == 3
        collection_names = [c.name for c in brand_with_collections.collections]
        assert "Collection 1" in collection_names
        assert "Collection 2" in collection_names
        assert "Collection 3" in collection_names
    
    @pytest.mark.asyncio
    async def test_collection_products_relationship(self, test_db_session: AsyncSession):
        """Test one-to-many relationship between collections and products."""
        # Create brand and collection
        brand = Brand(name="Product Relationship Brand", market_segment="mid-market")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        collection = Collection(
            name="Product Test Collection",
            brand_id=brand.id,
            season="summer",
            year=2024,
            target_pieces=4
        )
        test_db_session.add(collection)
        await test_db_session.flush()
        
        # Create multiple products
        garment_types = ["top", "bottom", "dress", "outerwear"]
        products = []
        
        for i, garment_type in enumerate(garment_types):
            product = Product(
                name=f"Test {garment_type.title()} {i+1}",
                brand_id=brand.id,
                collection_id=collection.id,
                garment_type=garment_type,
                target_price=50.0 + (i * 20)
            )
            products.append(product)
            test_db_session.add(product)
        
        await test_db_session.commit()
        
        # Query collection with products
        stmt = select(Collection).where(Collection.id == collection.id)
        result = await test_db_session.execute(stmt)
        collection_with_products = result.scalar_one()
        
        # Load products relationship
        await test_db_session.refresh(collection_with_products, ["products"])
        
        assert len(collection_with_products.products) == 4
        product_types = [p.garment_type for p in collection_with_products.products]
        assert set(product_types) == set(garment_types)


class TestGenerationModels:
    """Test suite for AI generation models."""
    
    @pytest.mark.asyncio
    async def test_create_generation_job(self, test_db_session: AsyncSession):
        """Test creating a generation job."""
        # Create brand for reference
        brand = Brand(name="Generation Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create generation job
        job = GenerationJob(
            name="Test Capsule Generation",
            description="Testing generation job creation",
            generation_type=GenerationType.CAPSULE_COLLECTION,
            brand_id=brand.id,
            input_parameters={
                "text_prompt": "minimalist spring collection",
                "target_pieces": 5,
                "quality_level": "high"
            },
            model_config={
                "primary_model": "stylegan3",
                "resolution": 1024,
                "guidance_scale": 7.5
            },
            num_outputs=5,
            quality_level="high",
            creativity_level=0.7,
            brand_adherence=0.8,
            status=GenerationStatus.QUEUED
        )
        
        test_db_session.add(job)
        await test_db_session.commit()
        
        # Verify job creation
        result = await test_db_session.get(GenerationJob, job.id)
        assert result is not None
        assert result.name == "Test Capsule Generation"
        assert result.generation_type == GenerationType.CAPSULE_COLLECTION
        assert result.status == GenerationStatus.QUEUED
        assert result.input_parameters["target_pieces"] == 5
        assert result.model_config["primary_model"] == "stylegan3"
        assert result.num_outputs == 5
        assert result.creativity_level == 0.7
    
    @pytest.mark.asyncio
    async def test_generation_job_status_transitions(self, test_db_session: AsyncSession):
        """Test generation job status transitions."""
        job = GenerationJob(
            name="Status Test Job",
            generation_type=GenerationType.SINGLE_PRODUCT,
            input_parameters={"text_prompt": "elegant blouse"},
            status=GenerationStatus.PENDING
        )
        
        test_db_session.add(job)
        await test_db_session.commit()
        
        # Test status transitions
        job.status = GenerationStatus.QUEUED
        job.queued_at = datetime.utcnow()
        await test_db_session.commit()
        
        job.status = GenerationStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.progress = 0.5
        job.current_step = "generating_visuals"
        await test_db_session.commit()
        
        job.status = GenerationStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress = 1.0
        job.output_count = 3
        job.average_quality_score = 0.85
        await test_db_session.commit()
        
        # Verify final state
        result = await test_db_session.get(GenerationJob, job.id)
        assert result.status == GenerationStatus.COMPLETED
        assert result.progress == 1.0
        assert result.output_count == 3
        assert result.average_quality_score == 0.85
        assert result.queued_at is not None
        assert result.started_at is not None
        assert result.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_create_generation_outputs(self, test_db_session: AsyncSession):
        """Test creating generation outputs linked to a job."""
        # Create generation job
        job = GenerationJob(
            name="Output Test Job",
            generation_type=GenerationType.CAPSULE_COLLECTION,
            input_parameters={"target_pieces": 3},
            num_outputs=3
        )
        test_db_session.add(job)
        await test_db_session.flush()
        
        # Create multiple outputs
        outputs = []
        for i in range(3):
            output = GenerationOutput(
                job_id=job.id,
                output_index=i,
                output_type="image",
                content_url=f"https://storage.example.com/output_{i}.jpg",
                thumbnail_url=f"https://storage.example.com/thumb_{i}.jpg",
                generation_parameters={
                    "seed": 12345 + i,
                    "model": "stylegan3",
                    "steps": 50
                },
                quality_score=0.8 + (i * 0.05),
                technical_quality=0.85 + (i * 0.03),
                aesthetic_quality=0.82 + (i * 0.04),
                brand_alignment=0.88,
                commercial_viability=0.75 + (i * 0.08),
                clip_score=0.79 + (i * 0.02),
                user_rating=4.0 + (i * 0.3)
            )
            outputs.append(output)
            test_db_session.add(output)
        
        await test_db_session.commit()
        
        # Verify outputs and relationship
        stmt = select(GenerationOutput).where(GenerationOutput.job_id == job.id).order_by(GenerationOutput.output_index)
        result = await test_db_session.execute(stmt)
        retrieved_outputs = result.scalars().all()
        
        assert len(retrieved_outputs) == 3
        for i, output in enumerate(retrieved_outputs):
            assert output.output_index == i
            assert output.job_id == job.id
            assert output.quality_score == 0.8 + (i * 0.05)
            assert f"output_{i}.jpg" in output.content_url
    
    @pytest.mark.asyncio
    async def test_generation_feedback(self, test_db_session: AsyncSession):
        """Test generation feedback creation and relationships."""
        # Create job and output
        job = GenerationJob(
            name="Feedback Test Job",
            generation_type=GenerationType.SINGLE_PRODUCT,
            input_parameters={"garment_type": "dress"}
        )
        test_db_session.add(job)
        await test_db_session.flush()
        
        output = GenerationOutput(
            job_id=job.id,
            output_index=0,
            output_type="image",
            content_url="https://storage.example.com/dress_output.jpg",
            quality_score=0.88
        )
        test_db_session.add(output)
        await test_db_session.flush()
        
        # Create feedback
        feedback = GenerationFeedback(
            job_id=job.id,
            output_id=output.id,
            rating=4.5,
            feedback_type="user_rating",
            comments="Beautiful dress design, love the silhouette!",
            specific_aspects={
                "color": 5,
                "silhouette": 4,
                "materials": 4,
                "overall_appeal": 5
            },
            would_purchase=True,
            price_expectation=150.00,
            target_market_fit=0.85,
            time_spent_viewing=45.2,
            interaction_count=3,
            shared=True
        )
        
        test_db_session.add(feedback)
        await test_db_session.commit()
        
        # Verify feedback
        result = await test_db_session.get(GenerationFeedback, feedback.id)
        assert result is not None
        assert result.rating == 4.5
        assert result.would_purchase is True
        assert result.price_expectation == 150.00
        assert result.specific_aspects["color"] == 5
        assert result.comments == "Beautiful dress design, love the silhouette!"
    
    @pytest.mark.asyncio
    async def test_generation_job_performance_metrics(self, test_db_session: AsyncSession):
        """Test generation job performance tracking."""
        job = GenerationJob(
            name="Performance Test Job",
            generation_type=GenerationType.STYLE_TRANSFER,
            input_parameters={"source_style": "bohemian", "target_style": "minimalist"},
            status=GenerationStatus.COMPLETED,
            started_at=datetime.utcnow() - timedelta(minutes=2),
            completed_at=datetime.utcnow(),
            generation_time=120.5,  # seconds
            compute_cost=0.25,      # dollars
            memory_usage=2048.0,    # MB
            gpu_utilization=0.85,   # percentage
            output_count=2,
            success_rate=1.0,
            average_quality_score=0.82
        )
        
        test_db_session.add(job)
        await test_db_session.commit()
        
        # Verify performance metrics
        result = await test_db_session.get(GenerationJob, job.id)
        assert result.generation_time == 120.5
        assert result.compute_cost == 0.25
        assert result.memory_usage == 2048.0
        assert result.gpu_utilization == 0.85
        assert result.success_rate == 1.0
        assert result.average_quality_score == 0.82


class TestUserModels:
    """Test suite for user management models."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db_session: AsyncSession, sample_user_data):
        """Test creating a user account."""
        user = User(
            id=uuid.UUID(sample_user_data["id"]),
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=sample_user_data["hashed_password"],
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"],
            role=UserRole.DESIGNER,
            is_active=sample_user_data["is_active"],
            is_verified=sample_user_data["is_verified"]
        )
        
        test_db_session.add(user)
        await test_db_session.commit()
        
        # Verify user creation
        result = await test_db_session.get(User, uuid.UUID(sample_user_data["id"]))
        assert result is not None
        assert result.email == sample_user_data["email"]
        assert result.username == sample_user_data["username"]
        assert result.role == UserRole.DESIGNER
        assert result.is_active is True
        assert result.is_verified is True
        assert result.created_at is not None
    
    @pytest.mark.asyncio
    async def test_user_brand_association(self, test_db_session: AsyncSession):
        """Test user-brand association."""
        # Create brand
        brand = Brand(name="User Association Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create user with brand association
        user = User(
            email="branduser@test.com",
            username="branduser",
            hashed_password="hashed_password",
            first_name="Brand",
            last_name="User",
            role=UserRole.BRAND_MANAGER,
            primary_brand_id=brand.id,
            accessible_brands=[str(brand.id)]
        )
        
        test_db_session.add(user)
        await test_db_session.commit()
        
        # Verify brand association
        result = await test_db_session.get(User, user.id)
        assert result.primary_brand_id == brand.id
        assert str(brand.id) in result.accessible_brands
        assert result.role == UserRole.BRAND_MANAGER
    
    @pytest.mark.asyncio
    async def test_user_preferences_and_settings(self, test_db_session: AsyncSession):
        """Test user preferences and UI settings storage."""
        user = User(
            email="preferences@test.com",
            username="prefuser",
            hashed_password="hashed_password",
            preferences={
                "generation_defaults": {
                    "quality_level": "high",
                    "creativity_level": 0.8,
                    "preferred_styles": ["minimalist", "contemporary"]
                },
                "notification_frequency": "daily",
                "language": "en"
            },
            ui_settings={
                "theme": "dark",
                "layout": "grid",
                "items_per_page": 20,
                "auto_save": True
            },
            notification_settings={
                "email_notifications": True,
                "push_notifications": False,
                "generation_complete": True,
                "weekly_summary": True
            }
        )
        
        test_db_session.add(user)
        await test_db_session.commit()
        
        # Verify JSON field storage
        result = await test_db_session.get(User, user.id)
        assert result.preferences["generation_defaults"]["quality_level"] == "high"
        assert result.preferences["generation_defaults"]["creativity_level"] == 0.8
        assert "minimalist" in result.preferences["generation_defaults"]["preferred_styles"]
        assert result.ui_settings["theme"] == "dark"
        assert result.ui_settings["auto_save"] is True
        assert result.notification_settings["email_notifications"] is True
    
    @pytest.mark.asyncio
    async def test_user_activity_tracking(self, test_db_session: AsyncSession):
        """Test user activity and login tracking."""
        user = User(
            email="activity@test.com",
            username="activeuser",
            hashed_password="hashed_password",
            last_login=datetime.utcnow() - timedelta(hours=2),
            last_activity=datetime.utcnow() - timedelta(minutes=15),
            login_count=25
        )
        
        test_db_session.add(user)
        await test_db_session.commit()
        
        # Simulate user activity update
        user.last_activity = datetime.utcnow()
        user.login_count += 1
        await test_db_session.commit()
        
        # Verify activity tracking
        result = await test_db_session.get(User, user.id)
        assert result.login_count == 26
        assert result.last_activity > result.last_login


class TestDatabaseQueries:
    """Test suite for complex database queries and operations."""
    
    @pytest.mark.asyncio
    async def test_brand_search_query(self, test_db_session: AsyncSession):
        """Test brand search functionality."""
        # Create test brands
        brands_data = [
            {"name": "Sustainable Luxury Co", "market_segment": "luxury", "aesthetic": "minimalist"},
            {"name": "Urban Street Fashion", "market_segment": "streetwear", "aesthetic": "edgy"},
            {"name": "Eco-Friendly Basics", "market_segment": "sustainable", "aesthetic": "minimalist"},
            {"name": "High-End Couture", "market_segment": "luxury", "aesthetic": "elegant"}
        ]
        
        for brand_data in brands_data:
            brand = Brand(
                name=brand_data["name"],
                market_segment=brand_data["market_segment"],
                design_dna={"aesthetic": brand_data["aesthetic"]}
            )
            test_db_session.add(brand)
        
        await test_db_session.commit()
        
        # Test market segment filter
        stmt = select(Brand).where(Brand.market_segment == "luxury")
        result = await test_db_session.execute(stmt)
        luxury_brands = result.scalars().all()
        assert len(luxury_brands) == 2
        
        # Test name search
        stmt = select(Brand).where(Brand.name.ilike("%sustainable%"))
        result = await test_db_session.execute(stmt)
        sustainable_brands = result.scalars().all()
        assert len(sustainable_brands) == 1
        assert "Sustainable" in sustainable_brands[0].name
        
        # Test JSON field query (aesthetic)
        stmt = select(Brand).where(Brand.design_dna["aesthetic"].astext == "minimalist")
        result = await test_db_session.execute(stmt)
        minimalist_brands = result.scalars().all()
        assert len(minimalist_brands) == 2
    
    @pytest.mark.asyncio
    async def test_generation_analytics_queries(self, test_db_session: AsyncSession):
        """Test analytics queries for generation performance."""
        # Create test brand
        brand = Brand(name="Analytics Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create test generation jobs with different statuses and performance
        jobs_data = [
            {"status": GenerationStatus.COMPLETED, "quality": 0.85, "time": 45.0},
            {"status": GenerationStatus.COMPLETED, "quality": 0.92, "time": 52.0},
            {"status": GenerationStatus.COMPLETED, "quality": 0.78, "time": 38.0},
            {"status": GenerationStatus.FAILED, "quality": None, "time": 15.0},
            {"status": GenerationStatus.RUNNING, "quality": None, "time": None}
        ]
        
        for i, job_data in enumerate(jobs_data):
            job = GenerationJob(
                name=f"Analytics Job {i+1}",
                generation_type=GenerationType.CAPSULE_COLLECTION,
                brand_id=brand.id,
                input_parameters={"target_pieces": 5},
                status=job_data["status"],
                average_quality_score=job_data["quality"],
                generation_time=job_data["time"],
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            test_db_session.add(job)
        
        await test_db_session.commit()
        
        # Test success rate calculation
        stmt = select(
            func.count(GenerationJob.id).label("total"),
            func.count(GenerationJob.id).filter(
                GenerationJob.status == GenerationStatus.COMPLETED
            ).label("completed")
        ).where(GenerationJob.brand_id == brand.id)
        
        result = await test_db_session.execute(stmt)
        stats = result.first()
        
        success_rate = stats.completed / stats.total if stats.total > 0 else 0
        assert stats.total == 5
        assert stats.completed == 3
        assert success_rate == 0.6
        
        # Test average quality for completed jobs
        stmt = select(func.avg(GenerationJob.average_quality_score)).where(
            and_(
                GenerationJob.brand_id == brand.id,
                GenerationJob.status == GenerationStatus.COMPLETED,
                GenerationJob.average_quality_score.isnot(None)
            )
        )
        
        result = await test_db_session.execute(stmt)
        avg_quality = result.scalar()
        
        expected_avg = (0.85 + 0.92 + 0.78) / 3
        assert abs(avg_quality - expected_avg) < 0.01
        
        # Test average generation time
        stmt = select(func.avg(GenerationJob.generation_time)).where(
            and_(
                GenerationJob.brand_id == brand.id,
                GenerationJob.generation_time.isnot(None)
            )
        )
        
        result = await test_db_session.execute(stmt)
        avg_time = result.scalar()
        
        expected_avg_time = (45.0 + 52.0 + 38.0 + 15.0) / 4
        assert abs(avg_time - expected_avg_time) < 0.01
    
    @pytest.mark.asyncio
    async def test_product_search_with_filters(self, test_db_session: AsyncSession):
        """Test complex product search with multiple filters."""
        # Create test data
        brand = Brand(name="Product Search Brand", market_segment="mid-market")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        collection = Collection(
            name="Search Test Collection",
            brand_id=brand.id,
            season="spring",
            year=2024
        )
        test_db_session.add(collection)
        await test_db_session.flush()
        
        # Create products with various attributes
        products_data = [
            {"name": "Cotton T-Shirt", "type": "top", "price": 45.0, "materials": ["cotton"], "colors": ["white", "black"]},
            {"name": "Linen Pants", "type": "bottom", "price": 85.0, "materials": ["linen"], "colors": ["beige", "navy"]},
            {"name": "Silk Blouse", "type": "top", "price": 120.0, "materials": ["silk"], "colors": ["cream", "burgundy"]},
            {"name": "Denim Jacket", "type": "outerwear", "price": 95.0, "materials": ["denim"], "colors": ["blue", "black"]},
            {"name": "Summer Dress", "type": "dress", "price": 75.0, "materials": ["cotton", "modal"], "colors": ["floral", "solid"]}
        ]
        
        for product_data in products_data:
            product = Product(
                name=product_data["name"],
                brand_id=brand.id,
                collection_id=collection.id,
                garment_type=product_data["type"],
                target_price=product_data["price"],
                design_dna={
                    "materials": product_data["materials"],
                    "colors": product_data["colors"]
                }
            )
            test_db_session.add(product)
        
        await test_db_session.commit()
        
        # Test garment type filter
        stmt = select(Product).where(Product.garment_type == "top")
        result = await test_db_session.execute(stmt)
        tops = result.scalars().all()
        assert len(tops) == 2
        
        # Test price range filter
        stmt = select(Product).where(
            and_(
                Product.target_price >= 50.0,
                Product.target_price <= 100.0
            )
        )
        result = await test_db_session.execute(stmt)
        mid_price_products = result.scalars().all()
        assert len(mid_price_products) == 3
        
        # Test JSON field search (materials containing cotton)
        stmt = select(Product).where(
            Product.design_dna["materials"].astext.contains("cotton")
        )
        result = await test_db_session.execute(stmt)
        cotton_products = result.scalars().all()
        assert len(cotton_products) >= 1
    
    @pytest.mark.asyncio
    async def test_user_generation_history(self, test_db_session: AsyncSession):
        """Test querying user generation history with pagination."""
        # Create user and brand
        user = User(
            email="history@test.com",
            username="historyuser",
            hashed_password="hashed_password"
        )
        test_db_session.add(user)
        
        brand = Brand(name="History Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Create multiple generation jobs for the user
        for i in range(15):
            job = GenerationJob(
                name=f"User Job {i+1}",
                generation_type=GenerationType.CAPSULE_COLLECTION if i % 2 == 0 else GenerationType.SINGLE_PRODUCT,
                brand_id=brand.id,
                user_id=user.id,
                input_parameters={"index": i},
                status=GenerationStatus.COMPLETED if i < 12 else GenerationStatus.RUNNING,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            test_db_session.add(job)
        
        await test_db_session.commit()
        
        # Test pagination query
        page_size = 5
        offset = 0
        
        stmt = (
            select(GenerationJob)
            .where(GenerationJob.user_id == user.id)
            .order_by(GenerationJob.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await test_db_session.execute(stmt)
        first_page = result.scalars().all()
        
        assert len(first_page) == 5
        # Verify ordering (newest first)
        for i in range(len(first_page) - 1):
            assert first_page[i].created_at >= first_page[i + 1].created_at
        
        # Test second page
        offset = page_size
        stmt = (
            select(GenerationJob)
            .where(GenerationJob.user_id == user.id)
            .order_by(GenerationJob.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        
        result = await test_db_session.execute(stmt)
        second_page = result.scalars().all()
        
        assert len(second_page) == 5
        # Verify no overlap between pages
        first_page_ids = {job.id for job in first_page}
        second_page_ids = {job.id for job in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)
    
    @pytest.mark.asyncio
    async def test_cascade_deletions(self, test_db_session: AsyncSession):
        """Test cascade deletion behavior."""
        # Create brand with collections and products
        brand = Brand(name="Cascade Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        collection = Collection(
            name="Cascade Test Collection",
            brand_id=brand.id,
            season="fall",
            year=2024
        )
        test_db_session.add(collection)
        await test_db_session.flush()
        
        product = Product(
            name="Cascade Test Product",
            brand_id=brand.id,
            collection_id=collection.id,
            garment_type="top",
            target_price=100.0
        )
        test_db_session.add(product)
        
        generation_job = GenerationJob(
            name="Cascade Test Job",
            generation_type=GenerationType.SINGLE_PRODUCT,
            brand_id=brand.id,
            input_parameters={"test": True}
        )
        test_db_session.add(generation_job)
        await test_db_session.flush()
        
        output = GenerationOutput(
            job_id=generation_job.id,
            output_index=0,
            output_type="image",
            content_url="https://example.com/test.jpg",
            quality_score=0.8
        )
        test_db_session.add(output)
        await test_db_session.commit()
        
        # Verify all entities exist
        assert await test_db_session.get(Brand, brand.id) is not None
        assert await test_db_session.get(Collection, collection.id) is not None
        assert await test_db_session.get(Product, product.id) is not None
        assert await test_db_session.get(GenerationJob, generation_job.id) is not None
        assert await test_db_session.get(GenerationOutput, output.id) is not None
        
        # Delete brand (should cascade to collections and products)
        await test_db_session.delete(brand)
        await test_db_session.commit()
        
        # Verify cascade deletion
        assert await test_db_session.get(Brand, brand.id) is None
        assert await test_db_session.get(Collection, collection.id) is None
        assert await test_db_session.get(Product, product.id) is None
        
        # Generation job should still exist (brand_id set to NULL due to ON DELETE SET NULL)
        remaining_job = await test_db_session.get(GenerationJob, generation_job.id)
        assert remaining_job is not None
        assert remaining_job.brand_id is None
        
        # Output should still exist (linked to job, not brand)
        remaining_output = await test_db_session.get(GenerationOutput, output.id)
        assert remaining_output is not None


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_complete_fashion_workflow(self, test_db_session: AsyncSession):
        """Test complete workflow from brand creation to generation feedback."""
        # 1. Create brand
        brand = Brand(
            name="Integration Test Brand",
            description="Complete workflow test",
            market_segment="luxury",
            design_dna={
                "aesthetic": "minimalist",
                "color_preference": ["black", "white", "beige"]
            }
        )
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # 2. Create collection
        collection = Collection(
            name="Spring 2024 Collection",
            brand_id=brand.id,
            season="spring",
            year=2024,
            theme="Minimalist Elegance",
            target_pieces=5
        )
        test_db_session.add(collection)
        await test_db_session.flush()
        
        # 3. Create generation job
        job = GenerationJob(
            name="Spring Collection Generation",
            generation_type=GenerationType.CAPSULE_COLLECTION,
            brand_id=brand.id,
            collection_id=collection.id,
            input_parameters={
                "text_prompt": "minimalist spring collection",
                "target_pieces": 5,
                "quality_level": "high"
            },
            num_outputs=5,
            status=GenerationStatus.COMPLETED,
            average_quality_score=0.87
        )
        test_db_session.add(job)
        await test_db_session.flush()
        
        # 4. Create outputs
        for i in range(5):
            output = GenerationOutput(
                job_id=job.id,
                output_index=i,
                output_type="image",
                content_url=f"https://storage.example.com/spring_piece_{i}.jpg",
                quality_score=0.85 + (i * 0.02),
                brand_alignment=0.9,
                commercial_viability=0.8
            )
            test_db_session.add(output)
        
        await test_db_session.flush()
        
        # 5. Create products from outputs
        garment_types = ["top", "bottom", "dress", "outerwear", "accessory"]
        for i, garment_type in enumerate(garment_types):
            product = Product(
                name=f"Spring {garment_type.title()} {i+1}",
                brand_id=brand.id,
                collection_id=collection.id,
                garment_type=garment_type,
                target_price=100.0 + (i * 25),
                generated_by_ai=True,
                parent_generation_id=job.id,
                design_score=0.85 + (i * 0.02),
                brand_alignment_score=0.9,
                commercial_viability_score=0.8
            )
            test_db_session.add(product)
        
        await test_db_session.flush()
        
        # 6. Add feedback
        outputs = await test_db_session.execute(
            select(GenerationOutput).where(GenerationOutput.job_id == job.id)
        )
        outputs_list = outputs.scalars().all()
        
        for output in outputs_list[:3]:  # Feedback on first 3 outputs
            feedback = GenerationFeedback(
                job_id=job.id,
                output_id=output.id,
                rating=4.0 + (output.output_index * 0.2),
                comments=f"Great design for piece {output.output_index}",
                would_purchase=True,
                price_expectation=120.0 + (output.output_index * 20)
            )
            test_db_session.add(feedback)
        
        await test_db_session.commit()
        
        # 7. Verify complete workflow
        # Check brand with relationships
        brand_result = await test_db_session.get(Brand, brand.id)
        await test_db_session.refresh(brand_result, ["collections"])
        assert len(brand_result.collections) == 1
        
        # Check collection with products
        collection_result = await test_db_session.get(Collection, collection.id)
        await test_db_session.refresh(collection_result, ["products"])
        assert len(collection_result.products) == 5
        
        # Check generation job with outputs and feedback
        job_result = await test_db_session.get(GenerationJob, job.id)
        
        outputs_stmt = select(GenerationOutput).where(GenerationOutput.job_id == job.id)
        outputs_result = await test_db_session.execute(outputs_stmt)
        job_outputs = outputs_result.scalars().all()
        assert len(job_outputs) == 5
        
        feedback_stmt = select(GenerationFeedback).where(GenerationFeedback.job_id == job.id)
        feedback_result = await test_db_session.execute(feedback_stmt)
        job_feedback = feedback_result.scalars().all()
        assert len(job_feedback) == 3
        
        # Verify data integrity
        for product in collection_result.products:
            assert product.brand_id == brand.id
            assert product.collection_id == collection.id
            assert product.generated_by_ai is True
            assert product.parent_generation_id == job.id
        
        for feedback in job_feedback:
            assert feedback.job_id == job.id
            assert feedback.rating >= 4.0
            assert feedback.would_purchase is True
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, test_db_session: AsyncSession):
        """Test concurrent database operations."""
        # Create base entities
        brand = Brand(name="Concurrent Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Simulate concurrent operations
        tasks = []
        
        # Concurrent collection creation
        for i in range(5):
            async def create_collection(index):
                collection = Collection(
                    name=f"Concurrent Collection {index}",
                    brand_id=brand.id,
                    season="spring" if index % 2 == 0 else "fall",
                    year=2024,
                    target_pieces=3 + index
                )
                test_db_session.add(collection)
                return collection
            
            tasks.append(create_collection(i))
        
        # Execute concurrent operations
        collections = await asyncio.gather(*tasks)
        await test_db_session.commit()
        
        # Verify all collections were created
        stmt = select(Collection).where(Collection.brand_id == brand.id)
        result = await test_db_session.execute(stmt)
        created_collections = result.scalars().all()
        
        assert len(created_collections) == 5
        collection_names = [c.name for c in created_collections]
        for i in range(5):
            assert f"Concurrent Collection {i}" in collection_names