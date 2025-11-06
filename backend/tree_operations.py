"""
Módulo com operações de árvore para gerenciamento de produtos
Implementa as funções exigidas nos testes: buildTree, printTree, calcularTotal
"""

from typing import List, Optional, Dict
from models_tree import Component, ItemFormula


class TreeNode:
    """Nó da árvore de componentes"""
    def __init__(self, name: str, quantity: int, cost: float, parent_name: Optional[str] = None):
        self.name = name
        self.quantity = quantity
        self.cost = cost
        self.parent_name = parent_name
        self.children: List[TreeNode] = []
    
    def add_child(self, child: 'TreeNode'):
        """Adiciona um filho a este nó"""
        self.children.append(child)
    
    def __repr__(self):
        return f"TreeNode(name='{self.name}', qty={self.quantity}, cost={self.cost}, children={len(self.children)})"


def buildTree(itens: List[ItemFormula]) -> TreeNode:
    """
    Constrói uma árvore a partir de uma lista de ItemFormula
    
    Args:
        itens: Lista de ItemFormula com name, parent, quantity e cost
    
    Returns:
        TreeNode: Nó raiz da árvore construída
    """
    # Dicionário para mapear índice -> TreeNode
    nodes: Dict[int, TreeNode] = {}
    # Dicionário para mapear nome do pai -> lista de índices dos filhos
    parent_to_children: Dict[str, List[int]] = {}
    root = None
    root_idx = None
    
    # Primeira passagem: criar todos os nós
    for idx, item in enumerate(itens):
        node = TreeNode(
            name=item.name,
            quantity=item.quantity,
            cost=item.cost,
            parent_name=item.parent
        )
        nodes[idx] = node
        
        # O item sem parent é a raiz
        if item.parent is None or item.parent == "":
            root = node
            root_idx = idx
        else:
            # Mapeia pai -> filhos
            if item.parent not in parent_to_children:
                parent_to_children[item.parent] = []
            parent_to_children[item.parent].append(idx)
    
    # Segunda passagem: conectar pais e filhos
    for idx, item in enumerate(itens):
        node = nodes[idx]
        # Adiciona filhos deste nó
        if item.name in parent_to_children:
            for child_idx in parent_to_children[item.name]:
                child_node = nodes[child_idx]
                node.add_child(child_node)
    
    return root


def printTree(node: TreeNode, level: int = 0):
    """
    Imprime a árvore de forma hierárquica
    
    Args:
        node: Nó atual da árvore
        level: Nível de indentação (profundidade na árvore)
    """
    indent = "  " * level
    print(f"{indent}{node.name} (Qtd: {node.quantity}, Custo: R$ {node.cost:.2f})")
    
    for child in node.children:
        printTree(child, level + 1)


def calcularTotal(node: TreeNode, parent_quantity: int = 1) -> float:
    """
    Calcula o custo total de um produto baseado na árvore de componentes.
    
    Args:
        node: Nó atual da árvore
        parent_quantity: Quantidade acumulada dos pais (para multiplicação)
    
    Returns:
        float: Custo total calculado
    """
    # Validação: se node é None, retorna 0
    if node is None:
        return 0.0
    
    current_quantity = node.quantity * parent_quantity
    
    # Custo próprio do nó (se tiver)
    total = node.cost * current_quantity
    
    # Soma o custo dos filhos (se tiver)
    for child in node.children:
        total += calcularTotal(child, current_quantity)
    
    return total


def buildTreeFromComponents(components: List[Component]) -> TreeNode:
    """
    Constrói uma árvore a partir de uma lista de objetos Component do banco de dados
    
    Args:
        components: Lista de objetos Component
    
    Returns:
        TreeNode: Nó raiz da árvore construída ou None se não houver componentes
    """
    # Validação: se não houver componentes, retorna None
    if not components:
        return None
    
    # Converter Components para ItemFormula
    itens = []
    for comp in components:
        item = ItemFormula(
            name=comp.name,
            parent=comp.parent_name,
            quantity=comp.quantity,
            cost=comp.cost
        )
        itens.append(item)
    
    return buildTree(itens)


def explodeProduct(root: TreeNode, production_quantity: int) -> Dict:
    """
    Realiza a explosão do produto: calcula quantos componentes são necessários
    para produzir uma determinada quantidade
    
    Args:
        root: Nó raiz do produto
        production_quantity: Quantidade de produtos a produzir
    
    Returns:
        Dict com informações da explosão
    """
    components_needed = {}
    
    def _explode_recursive(node: TreeNode, accumulated_quantity: int, parent_path: str = ""):
        """Função recursiva para explodir a árvore"""
        current_quantity = node.quantity * accumulated_quantity
        
        # Cria chave única: nome + custo (para diferenciar componentes com mesmo nome)
        # Usa o custo como parte da chave para separar componentes homônimos
        key = f"{node.name}_{node.cost:.2f}"
        
        # Adiciona TODOS os componentes (não apenas folhas)
        if key in components_needed:
            components_needed[key]['quantity'] += current_quantity
            components_needed[key]['total_cost'] += current_quantity * node.cost
        else:
            components_needed[key] = {
                'name': node.name,
                'quantity': current_quantity,
                'unit_cost': node.cost,
                'total_cost': current_quantity * node.cost,
                'path': parent_path + node.name if parent_path else node.name
            }
        
        # Recursão para todos os filhos
        new_path = (parent_path + node.name + " → ") if parent_path or node.children else ""
        for child in node.children:
            _explode_recursive(child, current_quantity, new_path)
    
    # Inicia a explosão a partir da raiz
    _explode_recursive(root, production_quantity)
    
    # Calcula custo total
    total_cost = sum(comp['total_cost'] for comp in components_needed.values())
    
    return {
        'product_name': root.name,
        'production_quantity': production_quantity,
        'components': components_needed,
        'total_cost': total_cost
    }


def implodeComponent(db_session, component_id: int) -> List[int]:
    """
    Realiza a implosão: quando um componente é atualizado, recalcula o custo
    de todos os produtos que o utilizam (direta ou indiretamente)
    
    Args:
        db_session: Sessão do banco de dados
        component_id: ID do componente que foi atualizado
    
    Returns:
        List[int]: Lista de IDs de produtos afetados
    """
    from models_tree import Component, Product
    
    affected_products = set()
    
    # Encontra o componente atualizado
    component = db_session.query(Component).filter_by(id=component_id).first()
    if not component:
        return []
    
    # Função recursiva para encontrar todos os pais
    def find_parents(comp: Component):
        # Se este componente pertence a um produto, adiciona à lista
        if comp.product_id:
            affected_products.add(comp.product_id)
        
        # Busca todos os componentes que têm este como filho
        parents = db_session.query(Component).filter_by(parent_id=comp.id).all()
        for parent in parents:
            find_parents(parent)
    
    # Inicia a busca recursiva
    find_parents(component)
    
    return list(affected_products)


def printTreeFormatted(node: TreeNode, level: int = 0, is_last: bool = True, prefix: str = "") -> str:
    """
    Retorna a árvore formatada como string com caracteres de árvore bonitos
    
    Args:
        node: Nó atual da árvore
        level: Nível de indentação
        is_last: Se é o último filho do pai
        prefix: Prefixo acumulado para indentação
    
    Returns:
        str: Representação formatada da árvore
    """
    result = ""
    
    if level == 0:
        result += f"{node.name} (Qtd: {node.quantity}, Custo: R$ {node.cost:.2f})\n"
    else:
        connector = "└── " if is_last else "├── "
        result += f"{prefix}{connector}{node.name} (Qtd: {node.quantity}, Custo: R$ {node.cost:.2f})\n"
    
    # Prepara o prefixo para os filhos
    if level > 0:
        extension = "    " if is_last else "│   "
        new_prefix = prefix + extension
    else:
        new_prefix = ""
    
    # Processa todos os filhos
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)
        result += printTreeFormatted(child, level + 1, is_last_child, new_prefix)
    
    return result
