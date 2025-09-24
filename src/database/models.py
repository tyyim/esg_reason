"""
Database models for ESG reasoning project using SQLAlchemy.
Defines tables for documents, evidence, and embeddings storage.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()


class Document(Base):
    """ESG document metadata"""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    doc_id = Column(String(255), unique=True, nullable=False, index=True)
    doc_type = Column(String(100), nullable=False)
    page_count = Column(Integer)
    file_path = Column(String(500))
    file_size = Column(Integer)  # File size in bytes
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to evidence
    evidence = relationship("Evidence", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(doc_id='{self.doc_id}', doc_type='{self.doc_type}')>"


class Evidence(Base):
    """Processed evidence from documents"""
    __tablename__ = 'evidence'

    id = Column(Integer, primary_key=True)
    doc_id = Column(String(255), ForeignKey('documents.doc_id'), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    evidence_type = Column(String(50), nullable=False)  # 'text', 'table', 'chart', 'image'
    text_content = Column(Text)
    image_path = Column(String(500))  # Path to extracted image if applicable
    bbox = Column(ARRAY(Float))  # Bounding box coordinates [x1, y1, x2, y2]
    embeddings = Column(Vector(1024))  # Qwen text-embedding-v4 dimension
    embedding_model = Column(String(100))  # Track which model generated embeddings
    processed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to document
    document = relationship("Document", back_populates="evidence")

    def __repr__(self):
        return f"<Evidence(doc_id='{self.doc_id}', page={self.page_number}, type='{self.evidence_type}')>"


class QAAnnotation(Base):
    """Question-Answer annotations from MMESGBench"""
    __tablename__ = 'qa_annotations'

    id = Column(Integer, primary_key=True)
    doc_id = Column(String(255), ForeignKey('documents.doc_id'), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    answer_format = Column(String(50))  # 'Str', 'Int', 'Float', 'List', 'None'
    evidence_pages = Column(ARRAY(Integer))  # List of page numbers
    evidence_sources = Column(ARRAY(String))  # List of evidence types
    split = Column(String(20))  # 'train', 'val', 'test'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to document
    document = relationship("Document")

    def __repr__(self):
        return f"<QAAnnotation(doc_id='{self.doc_id}', answer_format='{self.answer_format}')>"


class ExperimentRun(Base):
    """Track experiment runs and results"""
    __tablename__ = 'experiment_runs'

    id = Column(Integer, primary_key=True)
    experiment_name = Column(String(200), nullable=False)
    model_config = Column(Text)  # JSON string of model configuration
    optimizer_type = Column(String(50))  # 'baseline', 'gepa', 'miprov2'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(20))  # 'running', 'completed', 'failed'
    metrics = Column(Text)  # JSON string of results
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to predictions
    predictions = relationship("Prediction", back_populates="experiment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExperimentRun(name='{self.experiment_name}', status='{self.status}')>"


class Prediction(Base):
    """Individual prediction results"""
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey('experiment_runs.id'), nullable=False, index=True)
    qa_annotation_id = Column(Integer, ForeignKey('qa_annotations.id'), nullable=False, index=True)
    predicted_answer = Column(Text)
    confidence_score = Column(Float)
    reasoning_trace = Column(Text)  # DSPy reasoning trace
    processing_time = Column(Float)  # Time in seconds
    cost_estimate = Column(Float)  # API cost estimate
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    experiment = relationship("ExperimentRun", back_populates="predictions")
    qa_annotation = relationship("QAAnnotation")

    def __repr__(self):
        return f"<Prediction(experiment_id={self.experiment_id}, confidence={self.confidence_score})>"


def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)


def get_table_names():
    """Get list of all table names"""
    return [table.name for table in Base.metadata.tables.values()]