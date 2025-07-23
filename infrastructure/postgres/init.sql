-- GEN-VIEW-KSE Database Schema
-- Enhanced schema with KSE substrate entities and vector support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create custom types
CREATE TYPE generation_status AS ENUM (
    'pending', 'queued', 'running', 'completed', 'failed', 'cancelled', 'timeout'
);

CREATE TYPE generation_type AS ENUM (
    'capsule_collection', 'single_product', 'product_variation', 
    'style_transfer', 'design_evolution'
);

CREATE TYPE garment_type AS ENUM (
    'top', 'bottom', 'dress', 'outerwear', 'accessory', 'footwear', 'underwear'
);

CREATE TYPE season AS ENUM (
    'spring', 'summer', 'fall', 'winter', 'resort', 'pre_fall'
);

CREATE TYPE user_role AS ENUM (
    'admin', 'designer', 'brand_manager', 'viewer', 'api_client'
);

-- Fashion-specific entities
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Brand DNA and characteristics
    design_dna JSONB,
    target_demographic JSONB,
    brand_values JSONB,
    
    -- Visual characteristics
    color_palette JSONB,
    silhouette_preferences JSONB,
    fabric_preferences JSONB,
    
    -- Market positioning
    price_range JSONB,
    market_segment VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Collection metadata
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    season season,
    year INTEGER,
    collection_type VARCHAR(100) DEFAULT 'main',
    
    -- Design theme and inspiration
    theme VARCHAR(255),
    inspiration TEXT,
    mood_board JSONB,
    
    -- Generation parameters
    generation_config JSONB,
    design_constraints JSONB,
    target_pieces INTEGER DEFAULT 5,
    
    -- Status and workflow
    status VARCHAR(50) DEFAULT 'draft',
    generation_progress REAL DEFAULT 0.0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Product categorization
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    collection_id UUID REFERENCES collections(id) ON DELETE SET NULL,
    garment_type garment_type NOT NULL,
    category VARCHAR(100),
    
    -- Design specifications
    design_dna JSONB,
    silhouette JSONB,
    materials JSONB,
    colors JSONB,
    patterns JSONB,
    
    -- Technical specifications
    sizes JSONB,
    measurements JSONB,
    construction_details JSONB,
    
    -- Pricing and production
    target_price REAL,
    cost_estimate REAL,
    production_complexity REAL,
    
    -- AI generation metadata
    generated_by_ai BOOLEAN DEFAULT FALSE,
    generation_parameters JSONB,
    parent_generation_id UUID,
    
    -- Quality and performance metrics
    design_score REAL,
    brand_alignment_score REAL,
    commercial_viability_score REAL,
    
    -- Status and workflow
    status VARCHAR(50) DEFAULT 'concept',
    approval_status VARCHAR(50) DEFAULT 'pending',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- AI Generation entities
CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    generation_type generation_type NOT NULL,
    
    -- Relationships
    brand_id UUID REFERENCES brands(id) ON DELETE SET NULL,
    collection_id UUID REFERENCES collections(id) ON DELETE SET NULL,
    user_id UUID,
    
    -- Generation parameters
    input_parameters JSONB NOT NULL,
    model_config JSONB,
    generation_constraints JSONB,
    
    -- Multi-modal inputs
    text_prompt TEXT,
    reference_images TEXT[],
    style_references JSONB,
    design_dna_input JSONB,
    
    -- AI model configuration
    primary_model VARCHAR(50),
    model_version VARCHAR(100),
    secondary_models JSONB,
    
    -- Generation settings
    num_outputs INTEGER DEFAULT 1,
    quality_level VARCHAR(50) DEFAULT 'standard',
    creativity_level REAL DEFAULT 0.7,
    brand_adherence REAL DEFAULT 0.8,
    
    -- Execution tracking
    status generation_status DEFAULT 'pending',
    progress REAL DEFAULT 0.0,
    current_step VARCHAR(255),
    
    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    
    -- Performance metrics
    generation_time REAL,
    compute_cost REAL,
    memory_usage REAL,
    gpu_utilization REAL,
    
    -- Results
    output_count INTEGER DEFAULT 0,
    success_rate REAL,
    average_quality_score REAL,
    
    -- Error handling
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE generation_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    
    -- Output identification
    output_index INTEGER NOT NULL,
    output_type VARCHAR(50),
    
    -- Generated content
    content_url VARCHAR(500),
    content_data JSONB,
    thumbnail_url VARCHAR(500),
    
    -- Generation metadata
    generation_parameters JSONB,
    model_outputs JSONB,
    processing_steps JSONB,
    
    -- Quality assessment
    quality_score REAL,
    technical_quality REAL,
    aesthetic_quality REAL,
    brand_alignment REAL,
    commercial_viability REAL,
    
    -- CLIP-based assessments
    clip_score REAL,
    style_consistency REAL,
    novelty_score REAL,
    
    -- User interaction
    user_rating REAL,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    
    -- Product association
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE generation_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES generation_jobs(id) ON DELETE CASCADE,
    output_id UUID REFERENCES generation_outputs(id) ON DELETE CASCADE,
    user_id UUID,
    
    -- Feedback content
    rating REAL NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback_type VARCHAR(50),
    
    -- Detailed feedback
    comments TEXT,
    specific_aspects JSONB,
    improvement_suggestions JSONB,
    
    -- Commercial feedback
    would_purchase BOOLEAN,
    price_expectation REAL,
    target_market_fit REAL,
    
    -- Behavioral data
    time_spent_viewing REAL,
    interaction_count INTEGER,
    shared BOOLEAN DEFAULT FALSE,
    
    -- Learning integration
    feedback_weight REAL DEFAULT 1.0,
    used_for_training BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- KSE substrate entities
CREATE TABLE kse_memory_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_type VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    
    -- Vector embeddings (using pgvector extension)
    embeddings vector(1536),
    
    -- Node metadata
    metadata JSONB,
    parent_nodes UUID[],
    child_nodes UUID[],
    
    -- Temporal information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Relevance and quality metrics
    relevance_score REAL DEFAULT 0.0,
    quality_score REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE feedback_loops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_id UUID REFERENCES generation_jobs(id) ON DELETE CASCADE,
    
    -- Commercial outcomes
    commercial_outcomes JSONB,
    performance_metrics JSONB,
    learning_adjustments JSONB,
    
    -- Feedback processing
    feedback_type VARCHAR(50),
    impact_score REAL,
    confidence_level REAL,
    
    -- Integration status
    integrated BOOLEAN DEFAULT FALSE,
    integration_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE design_dna_evolution (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- DNA identification
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    collection_id UUID REFERENCES collections(id) ON DELETE SET NULL,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    
    -- DNA characteristics
    aesthetic_vector vector(512),
    style_attributes JSONB,
    color_dna JSONB,
    silhouette_dna JSONB,
    material_dna JSONB,
    
    -- Temporal tracking
    evolution_history JSONB,
    influence_sources JSONB,
    
    -- Performance metrics
    commercial_success_correlation REAL,
    brand_alignment_strength REAL,
    uniqueness_score REAL,
    
    -- Version control
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES design_dna_evolution(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE temporal_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Pattern identification
    pattern_type VARCHAR(100) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    
    -- Pattern data
    pattern_data JSONB NOT NULL,
    pattern_strength REAL DEFAULT 0.0,
    confidence_level REAL DEFAULT 0.0,
    
    -- Temporal context
    time_window_start TIMESTAMP WITH TIME ZONE,
    time_window_end TIMESTAMP WITH TIME ZONE,
    seasonal_component JSONB,
    trend_component JSONB,
    
    -- Pattern evolution
    evolution_rate REAL DEFAULT 0.0,
    stability_score REAL DEFAULT 0.0,
    
    -- Usage and validation
    usage_count INTEGER DEFAULT 0,
    validation_score REAL DEFAULT 0.0,
    last_validated TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User management entities
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Profile information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    bio TEXT,
    avatar_url VARCHAR(500),
    
    -- Role and permissions
    role user_role DEFAULT 'viewer',
    permissions JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Subscription and usage
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_expires TIMESTAMP WITH TIME ZONE,
    api_quota_limit INTEGER DEFAULT 100,
    api_quota_used INTEGER DEFAULT 0,
    
    -- Preferences
    preferences JSONB DEFAULT '{}'::jsonb,
    notification_settings JSONB DEFAULT '{}'::jsonb,
    ui_settings JSONB DEFAULT '{}'::jsonb,
    
    -- Brand associations
    primary_brand_id UUID REFERENCES brands(id) ON DELETE SET NULL,
    accessible_brands TEXT[],
    
    -- Activity tracking
    last_login TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    
    -- Security
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    email_verification_token VARCHAR(255),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_brands_name ON brands(name);
CREATE INDEX idx_brands_market_segment ON brands(market_segment);
CREATE INDEX idx_brands_active ON brands(is_active);

CREATE INDEX idx_collections_brand_id ON collections(brand_id);
CREATE INDEX idx_collections_season_year ON collections(season, year);
CREATE INDEX idx_collections_status ON collections(status);

CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_collection_id ON products(collection_id);
CREATE INDEX idx_products_garment_type ON products(garment_type);
CREATE INDEX idx_products_generated_by_ai ON products(generated_by_ai);
CREATE INDEX idx_products_active ON products(is_active);

CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX idx_generation_jobs_brand_id ON generation_jobs(brand_id);
CREATE INDEX idx_generation_jobs_created_at ON generation_jobs(created_at);
CREATE INDEX idx_generation_jobs_type ON generation_jobs(generation_type);

CREATE INDEX idx_generation_outputs_job_id ON generation_outputs(job_id);
CREATE INDEX idx_generation_outputs_quality ON generation_outputs(quality_score);

CREATE INDEX idx_generation_feedback_job_id ON generation_feedback(job_id);
CREATE INDEX idx_generation_feedback_output_id ON generation_feedback(output_id);
CREATE INDEX idx_generation_feedback_rating ON generation_feedback(rating);

-- KSE substrate indexes
CREATE INDEX idx_kse_memory_nodes_type_domain ON kse_memory_nodes(node_type, domain);
CREATE INDEX idx_kse_memory_nodes_created_at ON kse_memory_nodes(created_at);
CREATE INDEX idx_kse_memory_nodes_relevance ON kse_memory_nodes(relevance_score);

-- Vector similarity search index (using pgvector)
CREATE INDEX idx_kse_memory_embeddings ON kse_memory_nodes USING ivfflat (embeddings vector_cosine_ops);
CREATE INDEX idx_design_dna_aesthetic_vector ON design_dna_evolution USING ivfflat (aesthetic_vector vector_cosine_ops);

CREATE INDEX idx_feedback_loops_generation_id ON feedback_loops(generation_id);
CREATE INDEX idx_feedback_loops_integrated ON feedback_loops(integrated);

CREATE INDEX idx_temporal_patterns_type_domain ON temporal_patterns(pattern_type, domain);
CREATE INDEX idx_temporal_patterns_brand_id ON temporal_patterns(brand_id);
CREATE INDEX idx_temporal_patterns_time_window ON temporal_patterns(time_window_start, time_window_end);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_generation_jobs_updated_at BEFORE UPDATE ON generation_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kse_memory_nodes_updated_at BEFORE UPDATE ON kse_memory_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_design_dna_evolution_updated_at BEFORE UPDATE ON design_dna_evolution
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_temporal_patterns_updated_at BEFORE UPDATE ON temporal_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for development
INSERT INTO brands (id, name, description, design_dna, market_segment) VALUES
(
    uuid_generate_v4(),
    'Sustainable Luxe',
    'Premium sustainable fashion with timeless design',
    '{"aesthetic": "minimalist", "sustainability_focus": true, "color_preference": ["black", "white", "beige"], "silhouette_style": "clean_lines"}',
    'luxury'
),
(
    uuid_generate_v4(),
    'Urban Contemporary',
    'Modern streetwear with contemporary edge',
    '{"aesthetic": "contemporary", "urban_influence": true, "color_preference": ["gray", "navy", "olive"], "silhouette_style": "relaxed_fit"}',
    'mid-market'
),
(
    uuid_generate_v4(),
    'Fast Fashion Forward',
    'Trend-driven accessible fashion',
    '{"aesthetic": "trendy", "fast_fashion": true, "color_preference": ["bright", "seasonal"], "silhouette_style": "trend_following"}',
    'fast-fashion'
);

-- Insert sample users
INSERT INTO users (id, email, username, hashed_password, first_name, last_name, role) VALUES
(
    uuid_generate_v4(),
    'admin@genviewkse.com',
    'admin',
    crypt('admin123', gen_salt('bf')),
    'System',
    'Administrator',
    'admin'
),
(
    uuid_generate_v4(),
    'designer@genviewkse.com',
    'designer',
    crypt('designer123', gen_salt('bf')),
    'Creative',
    'Designer',
    'designer'
);

-- Grant appropriate permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;