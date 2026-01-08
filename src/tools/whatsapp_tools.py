import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

# Para Twilio (opcional - solo si tienes cuenta)
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

class WhatsAppTools:
    """Herramientas para manejar mensajes de WhatsApp"""
    
    def __init__(self, use_twilio: bool = False, config_file: str = "config/whatsapp_config.json"):
        self.use_twilio = use_twilio and TWILIO_AVAILABLE
        self.config_file = config_file
        self.config = self._load_config()
        
        if self.use_twilio:
            self.twilio_client = self._init_twilio()
        else:
            self.twilio_client = None
            print("⚠️  Modo simulador de WhatsApp activado (sin Twilio)")
    
    def _load_config(self) -> Dict:
        """Carga configuración de WhatsApp"""
        default_config = {
            "business_name": "Restaurante Demo",
            "business_phone": "+1234567890",
            "business_hours": "12:00 - 23:00",
            "confirmation_timeout_minutes": 30,
            "templates": {
                "welcome": "¡Hola! Soy {bot_name}, el asistente de {business_name}. ¿En qué puedo ayudarte?",
                "order_received": "📋 *Pedido Recibido*\n\nHemos recibido tu pedido:\n{order_summary}\n\nTotal: *${total}*\n\n¿Confirmas este pedido? Responde 'SÍ' para confirmar o 'NO' para cancelar.",
                "order_confirmed": "✅ *Pedido Confirmado*\n\nTu pedido #{order_id} ha sido confirmado.\n\nSe entregará alrededor de las {delivery_time}.\n\n¡Gracias por tu compra!",
                "order_cancelled": "❌ *Pedido Cancelado*\n\nTu pedido ha sido cancelado como solicitado.\n\n¿Necesitas ayuda con algo más?",
                "menu_request": "🍽️ *Nuestro Menú*\n\n{menu_items}\n\n¿Qué te gustaría ordenar?",
                "help": "🤖 *Comandos disponibles:*\n\n• *MENÚ* - Ver nuestro menú\n• *PEDIDO* - Hacer un pedido\n• *ESTADO* - Ver estado de tu pedido\n• *AYUDA* - Ver esta ayuda\n\nO simplemente escribe tu pedido en lenguaje natural.",
                "order_not_found": "⚠️ No encontramos pedidos activos para tu número.\n\nPara hacer un pedido, escribe lo que te gustaría ordenar."
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
        
        return default_config
    
    def _init_twilio(self):
        """Inicializa cliente de Twilio"""
        if not self.use_twilio:
            return None
        
        try:
            # Obtener credenciales de variables de entorno
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
            
            if not all([account_sid, auth_token, whatsapp_number]):
                print("⚠️  Variables de entorno de Twilio no configuradas")
                self.use_twilio = False
                return None
            
            return Client(account_sid, auth_token)
            
        except Exception as e:
            print(f"Error inicializando Twilio: {e}")
            self.use_twilio = False
            return None
    
    def send_message(self, to_number: str, message: str, 
                    media_url: str = None) -> Dict[str, Any]:
        """
        Envía un mensaje por WhatsApp
        
        Args:
            to_number: Número de teléfono destino (con código país)
            message: Mensaje a enviar
            media_url: URL de imagen/video (opcional)
        
        Returns:
            Dict con resultado del envío
        """
        if self.use_twilio and self.twilio_client:
            return self._send_via_twilio(to_number, message, media_url)
        else:
            return self._simulate_send(to_number, message, media_url)
    
    def _send_via_twilio(self, to_number: str, message: str, 
                        media_url: str = None) -> Dict[str, Any]:
        """Envía mensaje usando Twilio API"""
        try:
            from_number = f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}"
            to_number_formatted = f"whatsapp:{to_number}"
            
            message_args = {
                'from_': from_number,
                'body': message,
                'to': to_number_formatted
            }
            
            if media_url:
                message_args['media_url'] = [media_url]
            
            message_obj = self.twilio_client.messages.create(**message_args)
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'to': to_number,
                'timestamp': datetime.now().isoformat(),
                'provider': 'twilio'
            }
            
        except Exception as e:
            print(f"Error enviando mensaje por Twilio: {e}")
            return {
                'success': False,
                'error': str(e),
                'to': to_number,
                'timestamp': datetime.now().isoformat(),
                'provider': 'twilio'
            }
    
    def _simulate_send(self, to_number: str, message: str, 
                      media_url: str = None) -> Dict[str, Any]:
        """Simula envío de mensaje (para desarrollo)"""
        print("\n" + "="*60)
        print(f"📤 ENVIANDO MENSAJE WHATSAPP (SIMULADO)")
        print(f"Destino: {to_number}")
        if media_url:
            print(f"Media: {media_url}")
        print("-"*60)
        print(message)
        print("="*60 + "\n")
        
        # Simular delay de envío
        time.sleep(0.5)
        
        return {
            'success': True,
            'message_id': f"SIM-{int(time.time())}",
            'status': 'delivered',
            'to': to_number,
            'timestamp': datetime.now().isoformat(),
            'provider': 'simulator'
        }
    
    def format_order_summary(self, order_data: Dict, menu_tools) -> str:
        """Formatea un resumen de pedido para enviar al cliente"""
        template = self.config['templates']['order_received']
        
        # Construir resumen de items
        items_summary = ""
        for item in order_data.get('items', []):
            items_summary += f"• {item.get('quantity', 1)}x {item.get('name', '')}\n"
        
        # Calcular tiempo estimado
        requested_time = order_data.get('requested_time', 'ASAP')
        delivery_time = requested_time
        
        replacements = {
            '{bot_name}': 'Pedibot',
            '{business_name}': self.config['business_name'],
            '{order_summary}': items_summary,
            '{total}': f"{order_data.get('total_amount', 0):.2f}",
            '{delivery_time}': delivery_time,
            '{order_id}': order_data.get('order_id', 'PENDIENTE')
        }
        
        message = template
        for key, value in replacements.items():
            message = message.replace(key, str(value))
        
        return message
    
    def format_confirmation_message(self, order_id: str, 
                                  delivery_time: str) -> str:
        """Formatea mensaje de confirmación"""
        template = self.config['templates']['order_confirmed']
        
        return template.replace('{order_id}', order_id)\
                      .replace('{delivery_time}', delivery_time)
    
    def format_menu_message(self, menu_items: List[Dict]) -> str:
        """Formatea mensaje con el menú"""
        template = self.config['templates']['menu_request']
        
        # Agrupar por categoría
        categories = {}
        for item in menu_items:
            category = item.get('category', 'Otros')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Construir menú formateado
        menu_text = ""
        for category, items in categories.items():
            menu_text += f"*{category}:*\n"
            for item in items:
                menu_text += f"• {item['name']} - ${item['price']:.2f}\n"
                if item.get('description'):
                    menu_text += f"  _{item['description']}_\n"
            menu_text += "\n"
        
        return template.replace('{menu_items}', menu_text)
    
    def process_incoming_message(self, message: str, sender_number: str) -> Dict[str, Any]:
        message_lower = message.lower().strip()
        
        # Primero verificar si es ORDER (tiene prioridad)
        order_keywords = ['quiero', 'pedir', 'ordenar', 'deseo', 'para llevar', 
                        'pizza', 'hamburguesa', 'ensalada', 'pasta', 'coca', 'agua', 'jugo']
        
        is_order = any(keyword in message_lower for keyword in order_keywords)
        
        if is_order:
            return {
                'intent': 'order',
                'original_message': message,
                'sender_number': sender_number,
                'timestamp': datetime.now().isoformat(),
                'is_order': True,
                'needs_confirmation': False
            }
        
        # Luego verificar otras intenciones
        intents = {
            'greeting': any(word in message_lower for word in ['hola', 'buenas', 'hello', 'hi', 'buenos']),
            'menu_request': any(word in message_lower for word in ['menú', 'menu', 'carta', 'que tienen', 'disponible']),
            'status': any(word in message_lower for word in ['estado', 'status', 'donde está', 'cuando llega']),
            'help': any(word in message_lower for word in ['ayuda', 'help', 'comandos', 'qué puedes']),
            'cancel': any(word in message_lower for word in ['cancelar', 'cancel', 'no quiero']),
            'confirm': any(word in message_lower for word in ['sí', 'si', 'confirmo', 'ok', 'correcto', 'confirmar'])
        }
        
        detected_intent = None
        for intent, detected in intents.items():
            if detected:
                detected_intent = intent
                break
        
        return {
            'intent': detected_intent or 'unknown',
            'original_message': message,
            'sender_number': sender_number,
            'timestamp': datetime.now().isoformat(),
            'is_order': False,
            'needs_confirmation': detected_intent in ['confirm', 'cancel']
        }