"""
API Flask com suporte a estrutura de árvores hierárquicas
Implementa todas as funcionalidades requeridas: CRUD, explosão e implosão
"""

from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models_tree import Base, Product, Component, ItemFormula
from tree_operations import (
    buildTree, printTree, calcularTotal,
    buildTreeFromComponents, explodeProduct,
    implodeComponent, printTreeFormatted
)
from flask_cors import CORS
import os
from io import StringIO
import sys
import re

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = "sqlite:///" + os.path.join(basedir, "database_tree.db")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Força a criação das tabelas no banco de dados
Base.metadata.create_all(engine)

app = Flask(__name__)
CORS(app)

COMPONENT_NAME_PATTERN = re.compile(r'^[a-z\s]+$')


def sanitize_component_name(raw_name):
    """Normaliza e valida nomes de componentes/produtos."""
    if not isinstance(raw_name, str):
        return None

    sanitized = raw_name.strip().lower()
    if not sanitized or not COMPONENT_NAME_PATTERN.fullmatch(sanitized):
        return None

    return sanitized

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    return db


@app.route("/", methods=["GET"])
def home():
    """Endpoint raiz com informações da API"""
    return jsonify({
        "message": "API de Gerenciamento de Produtos com Estrutura de Árvores",
        "version": "2.0",
        "endpoints": {
            "POST /products": "Criar produto com estrutura hierárquica",
            "GET /products": "Listar todos os produtos",
            "GET /products/<id>": "Obter detalhes de um produto",
            "GET /products/<id>/tree": "Visualizar árvore do produto",
            "GET /products/<id>/explosion/<qty>": "Calcular explosão do produto",
            "PUT /products/<id>": "Atualizar produto",
            "DELETE /products/<id>": "Excluir produto (lógico)",
            "PUT /components/<id>": "Atualizar componente (com implosão)",
            "PUT /components/<id>/quantity": "Atualizar quantidade de componente",
            "DELETE /components/<id>": "Excluir componente",
        }
    }), 200


@app.route("/products", methods=["POST"])
def create_product():
    """
    Cria um novo produto com estrutura hierárquica de componentes
    
    Body JSON:
    {
        "name": "Nome do Produto",
        "components": [
            {"name": "Componente1", "parent": null, "quantity": 1, "cost": 10.0},
            {"name": "Subcomponente1", "parent": "Componente1", "quantity": 2, "cost": 5.0}
        ]
    }
    """
    db = get_db()
    try:
        data = request.get_json()
        raw_product_name = data.get("name")
        if not raw_product_name:
            return jsonify({"error": "O nome do produto é obrigatório"}), 400

        product_name = sanitize_component_name(raw_product_name)
        components_data = data.get("components", [])

        if not product_name:
            return jsonify({"error": "O nome do produto deve conter apenas letras minúsculas e espaços"}), 400

        # Verifica se já existe produto com este nome
        existing_product = db.query(Product).filter_by(name=product_name).first()
        if existing_product and existing_product.is_deleted == 0:
            return jsonify({"error": "Já existe um produto com este nome"}), 400

        # Cria o produto
        new_product = Product(name=product_name)
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        # Cria os componentes com hierarquia
        component_map = {}  # Mapeia nome -> objeto Component
        
        # Primeira passagem: cria todos os componentes
        for comp_data in components_data:
            component_name = comp_data.get("name")
            parent_name = comp_data.get("parent_name") or comp_data.get("parent")  # Aceita ambos os nomes
            component_cost = comp_data.get("cost")
            quantity = comp_data.get("quantity", 1)

            if not component_name or component_cost is None:
                db.rollback()
                return jsonify({"error": "Nome e custo são obrigatórios para todos os componentes"}), 400

            sanitized_component_name = sanitize_component_name(component_name)
            sanitized_parent_name = sanitize_component_name(parent_name) if parent_name else None

            if not sanitized_component_name:
                db.rollback()
                return jsonify({"error": "Os nomes dos componentes devem conter apenas letras minúsculas e espaços"}), 400

            if parent_name and not sanitized_parent_name:
                db.rollback()
                return jsonify({"error": "Os nomes dos componentes devem conter apenas letras minúsculas e espaços"}), 400

            # Mantém o parent_name como está (pode ser None para raiz)

            component = Component(
                name=sanitized_component_name,
                parent_name=sanitized_parent_name,
                cost=component_cost,
                quantity=quantity,
                product_id=new_product.id  # Todos os componentes pertencem ao produto
            )
            db.add(component)
            component_map[sanitized_component_name] = component
            comp_data["_sanitized_name"] = sanitized_component_name
            comp_data["_sanitized_parent"] = sanitized_parent_name

        db.flush()  # Para obter os IDs

        # Segunda passagem: conecta pais e filhos
        for comp_data in components_data:
            sanitized_component_name = comp_data.get("_sanitized_name")
            sanitized_parent_name = comp_data.get("_sanitized_parent")

            if sanitized_parent_name and sanitized_parent_name in component_map:
                component = component_map[sanitized_component_name]
                parent = component_map[sanitized_parent_name]
                component.parent_id = parent.id
        
        # Define o componente raiz (primeiro sem pai)
        root_component = None
        for comp in component_map.values():
            if comp.parent_name is None or comp.parent_name == "":
                root_component = comp
                break
        
        if root_component:
            new_product.root_component_id = root_component.id
        
        db.commit()
        db.refresh(new_product)
        
        return jsonify({
            "message": "Produto criado com sucesso",
            "product_id": new_product.id,
            "product_name": new_product.name
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route("/products", methods=["GET"])
def get_all_products():
    """Lista todos os produtos ativos"""
    db = get_db()
    try:
        products = db.query(Product).filter_by(is_deleted=0).all()
        products_list = []
        for product in products:
            # Calcula o custo total
            if product.root_component:
                components = db.query(Component).filter_by(product_id=product.id).all()
                if components:
                    tree = buildTreeFromComponents(components)
                    total_cost = calcularTotal(tree)
                else:
                    total_cost = 0
            else:
                total_cost = 0
            
            products_list.append({
                "id": product.id,
                "name": product.name,
                "total_cost": round(total_cost, 2)
            })
        return jsonify(products_list), 200
    finally:
        db.close()


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Obtém detalhes de um produto específico"""
    db = get_db()
    try:
        product = db.query(Product).filter_by(id=product_id, is_deleted=0).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        
        # Busca todos os componentes do produto
        components = db.query(Component).filter_by(product_id=product_id).all()
        
        if not components:
            return jsonify({
                "id": product.id,
                "name": product.name,
                "components": [],
                "total_cost": 0
            }), 200
        
        # Constrói a árvore e calcula o custo
        tree = buildTreeFromComponents(components)
        total_cost = calcularTotal(tree)
        
        # Monta a lista de componentes
        components_list = []
        for comp in components:
            components_list.append({
                "id": comp.id,
                "name": comp.name,
                "parent_name": comp.parent_name,
                "quantity": comp.quantity,
                "cost": comp.cost
            })
        
        return jsonify({
            "id": product.id,
            "name": product.name,
            "components": components_list,
            "total_cost": round(total_cost, 2)
        }), 200
        
    finally:
        db.close()


@app.route("/products/<int:product_id>/tree", methods=["GET"])
def get_product_tree(product_id):
    """Visualiza a árvore hierárquica do produto"""
    db = get_db()
    try:
        product = db.query(Product).filter_by(id=product_id, is_deleted=0).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        
        components = db.query(Component).filter_by(product_id=product_id).all()
        
        if not components:
            return jsonify({
                "product_name": product.name,
                "tree": "Produto sem componentes"
            }), 200
        
        # Constrói e formata a árvore
        tree = buildTreeFromComponents(components)
        tree_str = printTreeFormatted(tree)
        total_cost = calcularTotal(tree)
        
        return jsonify({
            "product_id": product.id,
            "product_name": product.name,
            "tree": tree_str,
            "total_cost": round(total_cost, 2)
        }), 200
        
    finally:
        db.close()


@app.route("/products/<int:product_id>/explosion/<int:quantity>", methods=["GET"])
def get_product_explosion(product_id, quantity):
    """
    Calcula a explosão do produto: quantos componentes são necessários
    para produzir uma determinada quantidade
    """
    db = get_db()
    try:
        product = db.query(Product).filter_by(id=product_id, is_deleted=0).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        
        components = db.query(Component).filter_by(product_id=product_id).all()
        
        if not components:
            return jsonify({"error": "Produto sem componentes"}), 400
        
        # Constrói a árvore e realiza a explosão
        tree = buildTreeFromComponents(components)
        explosion_data = explodeProduct(tree, quantity)
        
        # Formata os componentes para a resposta
        components_needed = []
        for comp_key, comp_info in explosion_data['components'].items():
            components_needed.append({
                "name": comp_info['name'],  # Usa o nome do comp_info
                "required_quantity": comp_info['quantity'],
                "unit_cost": comp_info['unit_cost'],
                "total_cost": comp_info['total_cost'],
                "path": comp_info.get('path', comp_info['name'])  # Caminho completo
            })
        
        return jsonify({
            "product_id": product.id,
            "product_name": product.name,
            "production_quantity": quantity,
            "components_needed": components_needed,
            "total_acquisition_cost": round(explosion_data['total_cost'], 2)
        }), 200
        
    finally:
        db.close()


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Exclui um produto (exclusão lógica)"""
    db = get_db()
    try:
        product = db.query(Product).filter_by(id=product_id).first()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        
        if product.is_deleted == 1:
            return jsonify({"error": "Produto já está excluído"}), 400
        
        product.is_deleted = 1
        db.commit()
        
        return jsonify({
            "message": f"Produto {product.name} excluído com sucesso"
        }), 200
        
    finally:
        db.close()


@app.route("/components/<int:component_id>", methods=["PUT"])
def update_component(component_id):
    """
    Atualiza um componente e realiza a implosão:
    recalcula o custo de todos os produtos que o utilizam
    
    Body JSON:
    {
        "cost": 15.50
    }
    """
    db = get_db()
    try:
        data = request.get_json()
        new_cost = data.get("cost")
        
        if new_cost is None:
            return jsonify({"error": "Custo é obrigatório"}), 400
        
        component = db.query(Component).filter_by(id=component_id).first()
        
        if not component:
            return jsonify({"error": "Componente não encontrado"}), 404
        
        old_cost = component.cost
        component.cost = new_cost
        db.commit()
        
        # Realiza a implosão: encontra produtos afetados
        affected_products_ids = implodeComponent(db, component_id)
        
        affected_products = []
        for prod_id in affected_products_ids:
            product = db.query(Product).filter_by(id=prod_id).first()
            if product:
                # Recalcula o custo do produto
                components = db.query(Component).filter_by(product_id=prod_id).all()
                if components:
                    tree = buildTreeFromComponents(components)
                    new_total = calcularTotal(tree)
                    affected_products.append({
                        "id": product.id,
                        "name": product.name,
                        "new_total_cost": round(new_total, 2)
                    })
        
        return jsonify({
            "message": "Componente atualizado com sucesso",
            "component_name": component.name,
            "old_cost": old_cost,
            "new_cost": new_cost,
            "affected_products": affected_products,
            "implosion_performed": len(affected_products) > 0
        }), 200
        
    finally:
        db.close()


@app.route("/components/<int:component_id>/quantity", methods=["PUT"])
def update_component_quantity(component_id):
    """
    Atualiza a quantidade de um componente
    
    Body JSON:
    {
        "quantity": 5
    }
    """
    db = get_db()
    try:
        data = request.get_json()
        new_quantity = data.get("quantity")
        
        if new_quantity is None or new_quantity < 1:
            return jsonify({"error": "Quantidade deve ser maior ou igual a 1"}), 400
        
        component = db.query(Component).filter_by(id=component_id).first()
        
        if not component:
            return jsonify({"error": "Componente não encontrado"}), 404
        
        old_quantity = component.quantity
        component.quantity = new_quantity
        db.commit()
        
        # Recalcula o custo do produto
        product = db.query(Product).filter_by(id=component.product_id).first()
        components = db.query(Component).filter_by(product_id=component.product_id).all()
        tree = buildTreeFromComponents(components)
        new_total = calcularTotal(tree)
        
        return jsonify({
            "message": "Quantidade atualizada com sucesso",
            "component_name": component.name,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "product_new_total_cost": round(new_total, 2)
        }), 200
        
    finally:
        db.close()


@app.route("/components/<int:component_id>", methods=["DELETE"])
def delete_component(component_id):
    """
    Exclui um componente e seus filhos
    """
    db = get_db()
    try:
        component = db.query(Component).filter_by(id=component_id).first()
        
        if not component:
            return jsonify({"error": "Componente não encontrado"}), 404
        
        # Verifica se é o componente raiz do produto
        product = db.query(Product).filter_by(root_component_id=component_id).first()
        if product:
            return jsonify({"error": "Não é possível excluir o componente raiz do produto"}), 400
        
        # Função recursiva para excluir filhos
        def delete_children(comp):
            children = db.query(Component).filter_by(parent_id=comp.id).all()
            for child in children:
                delete_children(child)
                db.delete(child)
        
        # Exclui filhos primeiro
        delete_children(component)
        
        # Guarda informações antes de excluir
        component_name = component.name
        product_id = component.product_id
        
        # Exclui o componente
        db.delete(component)
        db.commit()
        
        # Recalcula o custo do produto
        product = db.query(Product).filter_by(id=product_id).first()
        components = db.query(Component).filter_by(product_id=product_id).all()
        if components:
            tree = buildTreeFromComponents(components)
            new_total = calcularTotal(tree)
        else:
            new_total = 0
        
        return jsonify({
            "message": f"Componente {component_name} excluído com sucesso",
            "product_new_total_cost": round(new_total, 2)
        }), 200
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("API de Gerenciamento de Produtos com Estrutura de Árvores")
    print("="*80)
    print("Servidor rodando em: http://localhost:5000")
    print("Documentação: http://localhost:5000/")
    print("="*80 + "\n")
    app.run(debug=True, port=5000)