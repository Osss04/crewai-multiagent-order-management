import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, time
import os

@dataclass
class MenuItem:
    """Modelo para items del menú"""
    id: str
    name: str
    description: str
    price: float
    category: str
    available: bool = True
    preparation_time: int = 20  # minutos
    ingredients: List[str] = None
    allergens: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.ingredients is None:
            self.ingredients = []
        if self.allergens is None:
            self.allergens = []
        if self.tags is None:
            self.tags = []

class MenuTools:
    """Herramientas para consultar y validar el menú"""
    
    def __init__(self, menu_file: str = "data/menu.json"):
        self.menu_file = menu_file
        self.menu = self._load_menu()
        
    def _load_menu(self) -> Dict[str, MenuItem]:
        """Carga el menú desde archivo JSON"""
        try:
            if os.path.exists(self.menu_file):
                with open(self.menu_file, 'r', encoding='utf-8') as f:
                    menu_data = json.load(f)
                
                menu = {}
                for item_id, item_data in menu_data.items():
                    menu[item_id] = MenuItem(**item_data)
                return menu
            else:
                # Menú por defecto para demo
                return self._create_default_menu()
        except Exception as e:
            print(f"Error cargando menú: {e}")
            return self._create_default_menu()
    
    def _create_default_menu(self) -> Dict[str, MenuItem]:
        """Crea un menú por defecto para la demo"""
        default_menu = {
            "PIZ-001": MenuItem(
                id="PIZ-001",
                name="Pizza Margarita",
                description="Pizza clásica con tomate, mozzarella y albahaca",
                price=12.50,
                category="Pizzas",
                preparation_time=25,
                ingredients=["masa pizza", "salsa tomate", "mozzarella", "albahaca"],
                allergens=["gluten", "lactosa"]
            ),
            "PIZ-002": MenuItem(
                id="PIZ-002",
                name="Pizza Pepperoni",
                description="Pizza con pepperoni y extra queso",
                price=14.00,
                category="Pizzas",
                preparation_time=25,
                ingredients=["masa pizza", "salsa tomate", "mozzarella", "pepperoni"],
                allergens=["gluten", "lactosa"]
            ),
            "ENS-001": MenuItem(
                id="ENS-001",
                name="Ensalada César",
                description="Ensalada con pollo, crutones y salsa césar",
                price=9.50,
                category="Ensaladas",
                preparation_time=15,
                ingredients=["lechuga", "pollo", "crutones", "salsa césar", "parmesano"],
                allergens=["gluten", "lactosa", "mostaza"]
            ),
            "HMB-001": MenuItem(
                id="HMB-001",
                name="Hamburguesa Clásica",
                description="Hamburguesa con carne, queso, lechuga y tomate",
                price=10.50,
                category="Hamburguesas",
                preparation_time=20,
                ingredients=["pan hamburguesa", "carne", "queso", "lechuga", "tomate"],
                allergens=["gluten", "lactosa"]
            ),
            "BEB-001": MenuItem(
                id="BEB-001",
                name="Coca-Cola",
                description="Refresco de cola 330ml",
                price=2.50,
                category="Bebidas",
                preparation_time=1,
                ingredients=[],
                allergens=[]
            )
        }
        
        # Guardar menú por defecto
        self.save_menu(default_menu)
        return default_menu
    
    def save_menu(self, menu: Dict[str, MenuItem] = None):
        """Guarda el menú en archivo JSON"""
        if menu is None:
            menu = self.menu
            
        menu_dict = {}
        for item_id, item in menu.items():
            menu_dict[item_id] = asdict(item)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.menu_file), exist_ok=True)
        
        with open(self.menu_file, 'w', encoding='utf-8') as f:
            json.dump(menu_dict, f, indent=2, ensure_ascii=False)
    
    def get_item_by_name(self, item_name: str) -> Optional[MenuItem]:
        """Busca un item por nombre aproximado"""
        item_name_lower = item_name.lower()
        
        for item in self.menu.values():
            if item_name_lower in item.name.lower():
                return item
        
        # Búsqueda más flexible
        for item in self.menu.values():
            if any(word in item_name_lower for word in item.name.lower().split()):
                return item
        
        return None
    
    def get_item_by_id(self, item_id: str) -> Optional[MenuItem]:
        """Obtiene un item por su ID"""
        return self.menu.get(item_id)
    
    def search_items(self, category: str = None, available: bool = True) -> List[MenuItem]:
        """Busca items por categoría y disponibilidad"""
        results = []
        
        for item in self.menu.values():
            if available and not item.available:
                continue
            if category and item.category != category:
                continue
            results.append(item)
        
        return results
    
    def validate_order_items(self, items: List[Dict]) -> Dict[str, Any]:
        """
        Valida una lista de items solicitados
        
        Args:
            items: Lista de dicts con {name: str, quantity: int}
        
        Returns:
            Dict con resultados de validación
        """
        validated_items = []
        total_price = 0.0
        issues = []
        max_preparation_time = 0
        
        for item_request in items:
            item_name = item_request.get('name', '')
            quantity = item_request.get('quantity', 1)
            
            item = self.get_item_by_name(item_name)
            
            if not item:
                issues.append(f"Producto no encontrado: {item_name}")
                continue
            
            if not item.available:
                issues.append(f"Producto no disponible: {item.name}")
                continue
            
            # Calcular subtotal
            subtotal = item.price * quantity
            total_price += subtotal
            
            # Actualizar tiempo máximo de preparación
            if item.preparation_time > max_preparation_time:
                max_preparation_time = item.preparation_time
            
            validated_items.append({
                'item_id': item.id,
                'name': item.name,
                'quantity': quantity,
                'unit_price': item.price,
                'subtotal': subtotal,
                'allergens': item.allergens,
                'preparation_time': item.preparation_time
            })
        
        return {
            'valid': len(issues) == 0 and len(validated_items) > 0,
            'validated_items': validated_items,
            'total_price': round(total_price, 2),
            'issues': issues,
            'estimated_preparation_minutes': max_preparation_time
        }
    
    def check_availability(self, requested_time: str) -> Dict[str, Any]:
        """
        Verifica disponibilidad para un horario
        
        Args:
            requested_time: String en formato "HH:MM" o "HH:MM am/pm"
        
        Returns:
            Dict con disponibilidad
        """
        try:
            # Convertir string a time
            if 'am' in requested_time.lower() or 'pm' in requested_time.lower():
                time_obj = datetime.strptime(requested_time, '%I:%M %p').time()
            else:
                time_obj = datetime.strptime(requested_time, '%H:%M').time()
            
            # Horario del restaurante (ejemplo)
            opening_time = time(12, 0)  # 12:00 PM
            closing_time = time(23, 0)  # 11:00 PM
            
            # Verificar si está dentro del horario
            is_within_hours = opening_time <= time_obj <= closing_time
            
            # Verificar si hay suficiente tiempo (mínimo 30 minutos para preparar)
            current_time = datetime.now().time()
            time_difference = datetime.combine(datetime.today(), time_obj) - datetime.combine(datetime.today(), current_time)
            minutes_difference = time_difference.total_seconds() / 60
            
            available = is_within_hours and minutes_difference >= 30
            
            issues = []
            if not is_within_hours:
                issues.append(f"Horario fuera del horario de atención ({opening_time.strftime('%H:%M')} - {closing_time.strftime('%H:%M')})")
            if minutes_difference < 30:
                issues.append(f"Necesita al menos 30 minutos para preparación. Tiempo disponible: {int(minutes_difference)} minutos")
            
            return {
                'available': available,
                'requested_time': time_obj.strftime('%H:%M'),
                'issues': issues,
                'opening_time': opening_time.strftime('%H:%M'),
                'closing_time': closing_time.strftime('%H:%M'),
                'minutes_until_request': int(minutes_difference) if minutes_difference > 0 else 0
            }
            
        except ValueError as e:
            return {
                'available': False,
                'issues': [f"Formato de hora inválido: {requested_time}. Use formato 'HH:MM' o 'HH:MM AM/PM'"]
            }