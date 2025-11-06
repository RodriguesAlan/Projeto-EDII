from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Product(Base):
    """Produto final que possui uma árvore de componentes"""
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    is_deleted = Column(Integer, default=0)  # 0 = ativo, 1 = excluído
    
    # Relacionamento com o componente raiz (o produto em si)
    root_component_id = Column(Integer, ForeignKey('components.id'), nullable=True)
    root_component = relationship('Component', foreign_keys=[root_component_id], post_update=True)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"


class Component(Base):
    """Componente que pode ter subcomponentes (estrutura de árvore)"""
    __tablename__ = 'components'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_name = Column(String, nullable=True)  # Nome do componente pai (para facilitar construção)
    quantity = Column(Integer, default=1)  # Quantidade necessária deste componente
    cost = Column(Float, nullable=False)  # Custo unitário
    
    # Auto-relacionamento para criar hierarquia
    parent_id = Column(Integer, ForeignKey('components.id'), nullable=True)
    parent = relationship('Component', remote_side=[id], backref='children')
    
    # Relacionamento com produto (apenas para o componente raiz)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)

    def __repr__(self):
        return f"<Component(id={self.id}, name='{self.name}', parent='{self.parent_name}', qty={self.quantity}, cost={self.cost})>"
    
    def calculate_total_cost(self):
        """Calcula o custo total deste componente incluindo todos os filhos"""
        if not self.children:
            # Componente folha: retorna apenas seu custo
            return self.cost * self.quantity
        else:
            # Componente intermediário: soma o custo dos filhos
            children_cost = sum(child.calculate_total_cost() for child in self.children)
            return children_cost


class ItemFormula:
    """Classe auxiliar para compatibilidade com os testes fornecidos"""
    def __init__(self, name, parent, quantity, cost):
        self.name = name
        self.parent = parent
        self.quantity = quantity
        self.cost = cost
    
    def __repr__(self):
        return f"ItemFormula(name='{self.name}', parent='{self.parent}', qty={self.quantity}, cost={self.cost})"


# Configuração do banco de dados
import os

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = "sqlite:///" + os.path.join(basedir, "database_tree.db")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
