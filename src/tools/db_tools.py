import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import os
from dataclasses import dataclass, asdict

@dataclass
class Order:
    """Modelo para pedidos"""
    order_id: str
    customer_name: str
    customer_phone: str
    items: List[Dict]
    total_amount: float
    status: str  # pending, confirmed, preparing, ready, delivered, cancelled
    requested_time: str
    created_at: str
    confirmed_at: Optional[str] = None
    confirmed_by: Optional[str] = None
    notes: Optional[str] = None

class DatabaseTools:
    """Herramientas para manejar la base de datos SQLite"""
    
    def __init__(self, db_file: str = "data/orders.db"):
        self.db_file = db_file
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos y crea tablas si no existen"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Tabla de pedidos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL,
            requested_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            confirmed_at TEXT,
            confirmed_by TEXT,
            notes TEXT
        )
        ''')
        
        # Tabla de menú (cache)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_cache (
            item_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            available INTEGER DEFAULT 1,
            last_updated TEXT NOT NULL
        )
        ''')
        
        # Índices para búsquedas rápidas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_phone ON orders(customer_phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON orders(created_at)')
        
        conn.commit()
        conn.close()
    
    def generate_order_id(self) -> str:
        """Genera un ID único para el pedido"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"PED-{timestamp}-{unique_id}"
    
    def create_order(self, order_data: Dict) -> Dict[str, Any]:
        """
        Crea un nuevo pedido en la base de datos
        
        Args:
            order_data: Dict con datos del pedido
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            order_id = self.generate_order_id()
            current_time = datetime.now().isoformat()
            
            # Preparar datos
            order = Order(
                order_id=order_id,
                customer_name=order_data.get('customer_name', 'Cliente'),
                customer_phone=order_data.get('customer_phone', ''),
                items=order_data.get('items', []),
                total_amount=order_data.get('total_amount', 0.0),
                status='pending_confirmation',
                requested_time=order_data.get('requested_time', ''),
                created_at=current_time,
                notes=order_data.get('notes', '')
            )
            
            # Guardar en base de datos
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO orders 
            (order_id, customer_name, customer_phone, items_json, total_amount, 
             status, requested_time, created_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.order_id,
                order.customer_name,
                order.customer_phone,
                json.dumps(order.items, ensure_ascii=False),
                order.total_amount,
                order.status,
                order.requested_time,
                order.created_at,
                order.notes
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'order_id': order_id,
                'status': order.status,
                'created_at': current_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'order_id': None
            }
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Obtiene un pedido por su ID"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return Order(
                    order_id=row['order_id'],
                    customer_name=row['customer_name'],
                    customer_phone=row['customer_phone'],
                    items=json.loads(row['items_json']),
                    total_amount=row['total_amount'],
                    status=row['status'],
                    requested_time=row['requested_time'],
                    created_at=row['created_at'],
                    confirmed_at=row['confirmed_at'],
                    confirmed_by=row['confirmed_by'],
                    notes=row['notes']
                )
            return None
            
        except Exception as e:
            print(f"Error obteniendo pedido: {e}")
            return None
    
    def update_order_status(self, order_id: str, status: str, 
                           confirmed_by: str = None, notes: str = None) -> bool:
        """Actualiza el estado de un pedido"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            update_fields = ['status = ?']
            params = [status]
            
            if status == 'confirmed' and confirmed_by:
                update_fields.append('confirmed_at = ?')
                update_fields.append('confirmed_by = ?')
                params.append(datetime.now().isoformat())
                params.append(confirmed_by)
            
            if notes:
                update_fields.append('notes = ?')
                params.append(notes)
            
            params.append(order_id)
            
            query = f'UPDATE orders SET {", ".join(update_fields)} WHERE order_id = ?'
            cursor.execute(query, params)
            
            conn.commit()
            affected = cursor.rowcount > 0
            conn.close()
            
            return affected
            
        except Exception as e:
            print(f"Error actualizando estado: {e}")
            return False
    
    def get_orders_by_status(self, status: str = None, 
                           hours_back: int = 24) -> List[Order]:
        """Obtiene pedidos por estado y período"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            time_threshold = (datetime.now() - timedelta(hours=hours_back)).isoformat()
            
            if status:
                cursor.execute('''
                SELECT * FROM orders 
                WHERE status = ? AND created_at > ?
                ORDER BY created_at DESC
                ''', (status, time_threshold))
            else:
                cursor.execute('''
                SELECT * FROM orders 
                WHERE created_at > ?
                ORDER BY created_at DESC
                ''', (time_threshold,))
            
            rows = cursor.fetchall()
            conn.close()
            
            orders = []
            for row in rows:
                orders.append(Order(
                    order_id=row['order_id'],
                    customer_name=row['customer_name'],
                    customer_phone=row['customer_phone'],
                    items=json.loads(row['items_json']),
                    total_amount=row['total_amount'],
                    status=row['status'],
                    requested_time=row['requested_time'],
                    created_at=row['created_at'],
                    confirmed_at=row['confirmed_at'],
                    confirmed_by=row['confirmed_by'],
                    notes=row['notes']
                ))
            
            return orders
            
        except Exception as e:
            print(f"Error obteniendo pedidos: {e}")
            return []
    
    def get_customer_orders(self, customer_phone: str, 
                          limit: int = 10) -> List[Order]:
        """Obtiene historial de pedidos de un cliente"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM orders 
            WHERE customer_phone = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (customer_phone, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            orders = []
            for row in rows:
                orders.append(Order(
                    order_id=row['order_id'],
                    customer_name=row['customer_name'],
                    customer_phone=row['customer_phone'],
                    items=json.loads(row['items_json']),
                    total_amount=row['total_amount'],
                    status=row['status'],
                    requested_time=row['requested_time'],
                    created_at=row['created_at'],
                    confirmed_at=row['confirmed_at'],
                    confirmed_by=row['confirmed_by'],
                    notes=row['notes']
                ))
            
            return orders
            
        except Exception as e:
            print(f"Error obteniendo pedidos de cliente: {e}")
            return []
    
    def get_daily_stats(self, date_str: str = None) -> Dict[str, Any]:
        """Obtiene estadísticas del día"""
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Total pedidos del día
            cursor.execute('''
            SELECT COUNT(*) as total_orders, 
                   SUM(total_amount) as total_revenue,
                   AVG(total_amount) as avg_order_value
            FROM orders 
            WHERE DATE(created_at) = ?
            ''', (date_str,))
            
            stats = cursor.fetchone()
            
            # Pedidos por estado
            cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM orders 
            WHERE DATE(created_at) = ?
            GROUP BY status
            ''', (date_str,))
            
            status_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'date': date_str,
                'total_orders': stats[0] or 0,
                'total_revenue': float(stats[1] or 0),
                'avg_order_value': float(stats[2] or 0),
                'orders_by_status': status_counts
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'date': date_str,
                'total_orders': 0,
                'total_revenue': 0.0,
                'avg_order_value': 0.0,
                'orders_by_status': {}
            }