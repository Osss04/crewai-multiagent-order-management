from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime
import json

@dataclass
class Customer:
    """Modelo de cliente"""
    name: str
    phone: str
    address: Optional[str] = None
    preferences: List[str] = field(default_factory=list)
    order_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        return cls(**data)

@dataclass
class OrderItem:
    """Modelo de item en pedido"""
    item_id: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OrderItem':
        return cls(**data)

@dataclass
class Order:
    """Modelo principal de pedido"""
    order_id: str
    customer: Customer
    items: List[OrderItem]
    total_amount: float
    status: str  # pending, confirmed, preparing, ready, delivered, cancelled
    requested_time: str
    created_at: str
    estimated_delivery: Optional[str] = None
    confirmed_at: Optional[str] = None
    confirmed_by: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: str = 'pending'
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        data = asdict(self)
        data['customer'] = self.customer.to_dict()
        data['items'] = [item.to_dict() for item in self.items]
        return data
    
    def to_json(self) -> str:
        """Convierte a JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Order':
        """Crea desde diccionario"""
        # Convertir sub-objetos
        customer = Customer.from_dict(data.get('customer', {}))
        items = [OrderItem.from_dict(item) for item in data.get('items', [])]
        
        # Crear instancia
        return cls(
            order_id=data.get('order_id'),
            customer=customer,
            items=items,
            total_amount=data.get('total_amount', 0.0),
            status=data.get('status', 'pending'),
            requested_time=data.get('requested_time'),
            created_at=data.get('created_at'),
            estimated_delivery=data.get('estimated_delivery'),
            confirmed_at=data.get('confirmed_at'),
            confirmed_by=data.get('confirmed_by'),
            notes=data.get('notes'),
            payment_method=data.get('payment_method'),
            payment_status=data.get('payment_status', 'pending')
        )
    
    def calculate_total(self) -> float:
        """Calcula el total basado en los items"""
        return sum(item.subtotal for item in self.items)
    
    def update_status(self, new_status: str, updated_by: str = None):
        """Actualiza el estado del pedido"""
        self.status = new_status
        
        if new_status == 'confirmed' and updated_by:
            self.confirmed_at = datetime.now().isoformat()
            self.confirmed_by = updated_by
    
    def get_summary_text(self) -> str:
        """Genera un texto resumen del pedido"""
        items_text = "\n".join(
            f"  • {item.quantity}x {item.name} - ${item.subtotal:.2f}"
            for item in self.items
        )
        
        return f"""📋 Pedido #{self.order_id}
Cliente: {self.customer.name} ({self.customer.phone})
Estado: {self.status.upper()}
Hora solicitada: {self.requested_time}
Creado: {self.created_at}

Items:
{items_text}

Total: ${self.total_amount:.2f}
{self._get_status_emoji()}"""
    
    def _get_status_emoji(self) -> str:
        """Retorna emoji según estado"""
        emoji_map = {
            'pending': '⏳',
            'confirmed': '✅',
            'preparing': '👨‍🍳',
            'ready': '📦',
            'delivered': '🚚',
            'cancelled': '❌'
        }
        return emoji_map.get(self.status, '📝')
    
    def get_customer_view(self) -> str:
        """Genera vista simplificada para el cliente"""
        items_text = "\n".join(
            f"• {item.quantity}x {item.name}"
            for item in self.items
        )
        
        status_es = {
            'pending': 'Pendiente de confirmación',
            'confirmed': 'Confirmado',
            'preparing': 'En preparación',
            'ready': 'Listo para recoger',
            'delivered': 'Entregado',
            'cancelled': 'Cancelado'
        }
        
        return f"""✅ *Tu Pedido #{self.order_id}*

{items_text}

*Total:* ${self.total_amount:.2f}
*Estado:* {status_es.get(self.status, self.status)}
*Hora solicitada:* {self.requested_time}

{self._get_status_message()}"""
    
    def _get_status_message(self) -> str:
        """Mensaje adicional según estado"""
        if self.status == 'confirmed':
            return f"Tu pedido estará listo para las {self.estimated_delivery or self.requested_time}"
        elif self.status == 'preparing':
            return "Nuestros chefs están preparando tu pedido 🍳"
        elif self.status == 'ready':
            return "¡Tu pedido está listo para recoger! 🎉"
        elif self.status == 'delivered':
            return "¡Esperamos que disfrutes tu comida! 😊"
        else:
            return ""

@dataclass
class Restaurant:
    """Modelo de restaurante"""
    name: str
    phone: str
    address: str
    opening_hours: Dict[str, str]  # Ej: {"monday": "12:00-23:00"}
    delivery_radius_km: float = 5.0
    minimum_order: float = 10.0
    delivery_fee: float = 2.50
    payment_methods: List[str] = field(default_factory=lambda: ["efectivo", "tarjeta"])
    
    def is_open(self, day: str = None, time: str = None) -> bool:
        """Verifica si el restaurante está abierto"""
        # Implementación simplificada
        # En producción, usar datetime para verificación real
        return True
    
    def get_delivery_fee(self, distance_km: float) -> float:
        """Calcula costo de envío"""
        if distance_km <= 2.0:
            return 0.0
        elif distance_km <= self.delivery_radius_km:
            return self.delivery_fee
        else:
            return None  # Fuera de zona de entrega

@dataclass
class DailyReport:
    """Modelo para reporte diario"""
    date: str
    total_orders: int
    total_revenue: float
    avg_order_value: float
    orders_by_status: Dict[str, int]
    top_items: List[Dict[str, any]]
    busiest_hour: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Convierte a formato markdown para reportes"""
        top_items_text = "\n".join(
            f"- {item['name']}: {item['count']} pedidos (${item['revenue']:.2f})"
            for item in self.top_items[:5]
        )
        
        return f"""# 📊 Reporte Diario - {self.date}

## 📈 Resumen
- **Total Pedidos:** {self.total_orders}
- **Ingresos Totales:** ${self.total_revenue:.2f}
- **Ticket Promedio:** ${self.avg_order_value:.2f}
- **Hora Más Ocupada:** {self.busiest_hour}

## 📋 Pedidos por Estado
{chr(10).join(f"- {status}: {count}" for status, count in self.orders_by_status.items())}

## 🏆 Items Más Populares
{top_items_text}"""