#!/usr/bin/env python3
import sys
import os
from datetime import datetime
import time
import litellm

litellm.disable_logging = True
litellm.set_verbose = False
litellm.drop_params = True
litellm.telemetry = False
litellm.suppress_debug_info = True


sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.crew_setup import CrewConfigLoader
from src.tools.menu_tools import MenuTools
from src.tools.db_tools import DatabaseTools
from src.tools.whatsapp_tools import WhatsAppTools
from src.tools.llm_tools import GroqLLMFactory, OrderExtractor
from data.demo_messages import DEMO_MESSAGES


# Para Groq LLM
from dotenv import load_dotenv

load_dotenv()

class PedibotDemo:
    
    def __init__(self, use_groq=True):
        print("🚀 Inicializando Pedibot Demo...")
        
        # Inicializar herramientas
        self.menu_tools = MenuTools()
        self.db_tools = DatabaseTools()
        self.whatsapp_tools = WhatsAppTools(use_twilio=False)
        self.llm = GroqLLMFactory.create() if use_groq else None
        self.extractor = OrderExtractor(self.llm)
        self.demo_messages = DEMO_MESSAGES

        # Inicializar crew
        if self.llm and use_groq:
            print("🤖 Configurando CrewAI con Groq...")
            try:
                self.loader = CrewConfigLoader("config")
                self.crew = self.loader.create_crew()
                print("✅ CrewAI configurado exitosamente")
            except Exception as e:
                print(f"⚠️  Error configurando CrewAI: {e}")
                print("📝 Usando modo simplificado sin CrewAI")
                self.crew = None
        else:
            print("📝 Usando modo simplificado sin LLM")
            self.crew = None
    
    
    
    def print_header(self):
        """Imprime el encabezado de la demo"""
        print("="*70)
        print("🚀 PEDIBOT - DEMOSTRACIÓN DEL SISTEMA")
        print("🤖 Automatización de Pedidos por WhatsApp")
        print(f"🧠 Motor: {'Groq LLM' if self.llm else 'Modo Simulado'}")
        print("="*70)
        print()
    
    def print_menu_preview(self):
        """Muestra una vista previa del menú"""
        print("🍽️  MENÚ DE DEMOSTRACIÓN")
        print("-"*40)
        
        menu_items = list(self.menu_tools.menu.values())
        categories = {}
        
        for item in menu_items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        for category, items in categories.items():
            print(f"\n{category.upper()}:")
            for item in items[:3]:  # Mostrar solo 3 por categoría
                print(f"  • {item.name} - ${item.price:.2f}")
            if len(items) > 3:
                print(f"  ... y {len(items)-3} más")
        
        print()
    
    
    def simulate_whatsapp_conversation(self, message_data: dict):
        """Simula una conversación por WhatsApp"""
        print(f"\n💬 CONVERSACIÓN CON {message_data['customer']}")
        print(f"📱 Teléfono: {message_data['phone']}")
        print("-"*50)
        
        # Mensaje del cliente
        print(f"👤 Cliente: {message_data['message']}")
        
        # Procesar el mensaje
        analysis = self.whatsapp_tools.process_incoming_message(
            message_data['message'], 
            message_data['phone']
        )
        
        print(f"🤖 Análisis: INTENCIÓN = {analysis['intent'].upper()}")
        
        # Si es un pedido, procesarlo
        if analysis['is_order']:
            print("\n⚙️  PROCESANDO PEDIDO...")
            
            # Extraer información (con IA si está disponible)
            extracted_data = self.extractor.extract(message_data['message'])

            extracted_data = {
                "items": extracted_data.get("items", []),
                "requested_time": extracted_data.get("requested_time", "ASAP"),
                "notes": extracted_data.get("notes", "")
            }

            print(f"📋 Items detectados: {extracted_data['items']}")
            print(f"⏰ Hora solicitada: {extracted_data['requested_time']}")

            # Validar items
            validation = self.menu_tools.validate_order_items(extracted_data['items'])
            
            if validation['valid']:
                # Verificar disponibilidad horaria
                time_check = self.menu_tools.check_availability(extracted_data['requested_time'])
                
                if time_check['available'] or extracted_data['requested_time'] == 'ASAP':
                    # Crear orden
                    order_data = {
                        'customer_name': message_data['customer'],
                        'customer_phone': message_data['phone'],
                        'items': validation['validated_items'],
                        'total_amount': validation['total_price'],
                        'requested_time': extracted_data['requested_time'],
                        'notes': extracted_data['notes']
                    }
                    
                    order_result = self.db_tools.create_order(order_data)
                    
                    if order_result['success']:
                        print(f"✅ Pedido registrado: #{order_result['order_id']}")
                        
                        # Preparar mensaje de confirmación
                        order_summary = self.whatsapp_tools.format_order_summary(
                            {**order_data, **order_result},
                            self.menu_tools
                        )
                        
                        # Enviar mensaje
                        print("\n📤 RESPUESTA AUTOMÁTICA:")
                        print("-"*40)
                        print(order_summary)
                        
                        # Guardar para confirmación posterior
                        self._pending_order = {
                            'order_id': order_result['order_id'],
                            'customer_phone': message_data['phone'],
                            'customer_name': message_data['customer']
                        }
                    else:
                        print(f"❌ Error registrando pedido: {order_result.get('error')}")
                else:
                    print(f"❌ Horario no disponible: {time_check['issues']}")
                    
                    # Ofrecer alternativa
                    alt_time = "20:00"  # Hora alternativa
                    print(f"💡 Sugerencia: ¿Podría ser para las {alt_time}?")
            else:
                print(f"❌ Problemas con el pedido: {validation['issues']}")
                
                # Sugerir alternativas
                available_items = self.menu_tools.search_items(available=True)
                if available_items:
                    print("💡 Alternativas disponibles:")
                    for item in available_items[:3]:
                        print(f"  • {item.name} - ${item.price:.2f}")
        
        elif analysis['intent'] == 'menu_request':
            # Enviar menú
            menu_items = list(self.menu_tools.menu.values())
            simplified_items = [
                {
                    'name': item.name,
                    'price': item.price,
                    'description': item.description[:50] + "..." if len(item.description) > 50 else item.description,
                    'category': item.category
                }
                for item in menu_items[:8]  # Solo primeros 8
            ]
            
            menu_message = self.whatsapp_tools.format_menu_message(simplified_items)
            
            print("\n📤 RESPUESTA AUTOMÁTICA:")
            print("-"*40)
            print(menu_message)
        
        elif analysis['intent'] == 'confirm' and hasattr(self, '_pending_order'):
            # Confirmar pedido pendiente
            success = self.db_tools.update_order_status(
                self._pending_order['order_id'],
                'confirmed',
                confirmed_by=self._pending_order['customer_name']
            )
            
            if success:
                order = self.db_tools.get_order(self._pending_order['order_id'])
                
                confirmation_msg = self.whatsapp_tools.format_confirmation_message(
                    order.order_id,
                    order.requested_time if order.requested_time != 'ASAP' else 'lo antes posible'
                )
                
                print("\n📤 RESPUESTA AUTOMÁTICA:")
                print("-"*40)
                print(confirmation_msg)
                
                # Limpiar pedido pendiente
                delattr(self, '_pending_order')
                
                # Mostrar resumen en consola
                print(f"\n📊 Pedido #{order.order_id} confirmado:")
                print(f"   Cliente: {order.customer_name}")
                print(f"   Total: ${order.total_amount:.2f}")
                print(f"   Estado: {order.status}")
            else:
                print("❌ Error confirmando pedido")
        
        elif analysis['intent'] == 'help':
            help_message = self.whatsapp_tools.config['templates']['help']
            print("\n📤 RESPUESTA AUTOMÁTICA:")
            print("-"*40)
            print(help_message)
        
        elif analysis['intent'] == 'greeting':
            welcome_msg = self.whatsapp_tools.config['templates']['welcome']
            welcome_msg = welcome_msg.replace('{bot_name}', 'Pedibot')
            welcome_msg = welcome_msg.replace('{business_name}', 'Restaurante Demo')
            
            print("\n📤 RESPUESTA AUTOMÁTICA:")
            print("-"*40)
            print(welcome_msg)
        
        print("-"*50)
        time.sleep(1)
    
    def show_dashboard(self):
        """Muestra un dashboard simple"""
        print("\n📊 TABLERO DE CONTROL")
        print("="*50)
        
        # Estadísticas del día
        stats = self.db_tools.get_daily_stats()
        
        print(f"📅 Fecha: {stats['date']}")
        print(f"📦 Total Pedidos: {stats['total_orders']}")
        print(f"💰 Ingresos: ${stats['total_revenue']:.2f}")
        print(f"📈 Ticket Promedio: ${stats['avg_order_value']:.2f}")
        
        # Pedidos por estado
        if stats['orders_by_status']:
            print(f"\n📋 Distribución por estado:")
            for status, count in stats['orders_by_status'].items():
                print(f"  • {status}: {count}")
        
        # Pedidos recientes
        recent_orders = self.db_tools.get_orders_by_status(hours_back=24)
        
        print(f"\n🔄 Pedidos Recientes ({len(recent_orders)}):")
        print("-"*40)
        
        for order in recent_orders[:5]:  # Mostrar solo 5
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅',
                'preparing': '👨‍🍳',
                'ready': '📦',
                'delivered': '🚚',
                'cancelled': '❌'
            }.get(order.status, '📝')
            
            print(f"{status_emoji} #{order.order_id} | {order.customer_name} | ${order.total_amount:.2f} | {order.status}")
        
        if len(recent_orders) > 5:
            print(f"... y {len(recent_orders)-5} más")
    
    def run_interactive_demo(self):
        """Ejecuta demo interactiva con casos predefinidos"""
        self.print_header()
        
        # Paso 1: Mostrar menú
        self.print_menu_preview()
        
        input("\nPresiona Enter para comenzar la simulación...")
        
        # Paso 2: Simular conversaciones
        print("\n" + "="*70)
        print("📱 SIMULACIÓN DE CONVERSACIONES WHATSAPP")
        print("="*70)
        
        for i, message_data in enumerate(self.demo_messages):
            print(f"\n🎬 Escenario {i+1}/{len(self.demo_messages)}")
            self.simulate_whatsapp_conversation(message_data)
            
            if i < len(self.demo_messages) - 1:
                cont = input("\n¿Continuar con siguiente escenario? (s/n): ").lower()
                if cont != 's':
                    break
                print()
        
        # Paso 3: Mostrar dashboard
        print("\n" + "="*70)
        print("📈 RESUMEN DE LA DEMOSTRACIÓN")
        print("="*70)
        
        self.show_dashboard()
        
        # Paso 4: Menú interactivo
        self._interactive_menu()
    
    def _interactive_menu(self):
        """Menú interactivo para explorar funcionalidades"""
        print("\n" + "="*70)
        print("🔧 MENÚ INTERACTIVO")
        print("="*70)
        
        while True:
            print("\nOpciones:")
            print("1. 📋 Ver todos los pedidos")
            print("2. 🔍 Buscar pedido por ID")
            print("3. 👤 Ver pedidos por cliente")
            print("4. 🍽️ Ver menú completo")
            print("5. 💬 Probar mensaje personalizado")
            print("6. 📊 Ver estadísticas avanzadas")
            print("7. 🚀 Probar con CrewAI (si está configurado)")
            print("8. ❌ Salir")
            
            try:
                choice = input("\nSelecciona una opción (1-8): ").strip()
                
                if choice == '1':
                    self._show_all_orders()
                elif choice == '2':
                    self._search_order_by_id()
                elif choice == '3':
                    self._show_orders_by_customer()
                elif choice == '4':
                    self._show_full_menu()
                elif choice == '5':
                    self._test_custom_message()
                elif choice == '6':
                    self._show_advanced_stats()
                elif choice == '7':
                    self._test_crewai()
                elif choice == '8':
                    print("\n🎉 ¡Demostración completada!")
                    print("Gracias por probar Pedibot 🤖")
                    break
                else:
                    print("❌ Opción inválida. Intenta de nuevo.")
            
            except KeyboardInterrupt:
                print("\n\n👋 ¡Interrumpido por el usuario!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_all_orders(self):
        """Muestra todos los pedidos"""
        orders = self.db_tools.get_orders_by_status(hours_back=168)  # Última semana
        print(f"\n📋 Total pedidos: {len(orders)}")
        
        if not orders:
            print("No hay pedidos registrados.")
            return
        
        for i, order in enumerate(orders, 1):
            print(f"\n#{i}. {order.order_id}")
            print(f"   Cliente: {order.customer_name}")
            print(f"   Teléfono: {order.customer_phone}")
            print(f"   Total: ${order.total_amount:.2f}")
            print(f"   Estado: {order.status}")
            print(f"   Hora: {order.requested_time}")
            print(f"   Creado: {order.created_at}")
    
    def _search_order_by_id(self):
        """Busca un pedido por ID"""
        order_id = input("Ingresa ID del pedido (ej: PED-20240101-XXXX): ").strip()
        
        if not order_id:
            print("❌ Debes ingresar un ID")
            return
        
        order = self.db_tools.get_order(order_id)
        if order:
            print(f"\n✅ Pedido encontrado:")
            print(f"ID: {order.order_id}")
            print(f"Cliente: {order.customer_name}")
            print(f"Teléfono: {order.customer_phone}")
            print(f"Estado: {order.status}")
            print(f"Hora solicitada: {order.requested_time}")
            print(f"Total: ${order.total_amount:.2f}")
            
            print("\n📦 Items:")
            for item in order.items:
                print(f"  • {item.get('quantity', 1)}x {item.get('name', 'Desconocido')} - ${item.get('subtotal', 0):.2f}")
            
            if order.notes:
                print(f"\n📝 Notas: {order.notes}")
        else:
            print("❌ Pedido no encontrado")
    
    def _show_orders_by_customer(self):
        """Muestra pedidos por cliente"""
        phone = input("Ingresa teléfono del cliente: ").strip()
        
        if not phone:
            print("❌ Debes ingresar un teléfono")
            return
        
        orders = self.db_tools.get_customer_orders(phone)
        print(f"\n📋 Pedidos para {phone}: {len(orders)}")
        
        if not orders:
            print("No se encontraron pedidos para este cliente.")
            return
        
        total_spent = sum(order.total_amount for order in orders)
        
        for i, order in enumerate(orders, 1):
            print(f"\n#{i}. {order.order_id}")
            print(f"   Fecha: {order.created_at}")
            print(f"   Total: ${order.total_amount:.2f}")
            print(f"   Estado: {order.status}")
        
        print(f"\n💰 Total gastado: ${total_spent:.2f}")
        print(f"📊 Promedio por pedido: ${total_spent/len(orders):.2f}" if orders else "")
    
    def _show_full_menu(self):
        """Muestra el menú completo"""
        menu_items = list(self.menu_tools.menu.values())
        print(f"\n🍽️ Menú completo ({len(menu_items)} items)")
        print("="*60)
        
        # Agrupar por categoría
        categories = {}
        for item in menu_items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        for category, items in categories.items():
            print(f"\n{category.upper()}:")
            print("-"*40)
            for item in items:
                print(f"\n{item.name} - ${item.price:.2f}")
                print(f"  {item.description}")
                if item.ingredients:
                    print(f"  Ingredientes: {', '.join(item.ingredients[:3])}{'...' if len(item.ingredients) > 3 else ''}")
                if item.allergens:
                    print(f"  Alérgenos: {', '.join(item.allergens)}")
                print(f"  Tiempo preparación: {item.preparation_time} min")
                print(f"  {'✅ Disponible' if item.available else '❌ No disponible'}")
    
    def _test_custom_message(self):
        """Prueba un mensaje personalizado"""
        print("\n💬 PRUEBA DE MENSAJE PERSONALIZADO")
        print("-"*40)
        
        customer_name = input("Nombre del cliente: ").strip() or "Cliente Demo"
        phone = input("Teléfono: ").strip() or "+12345678900"
        message = input("Mensaje: ").strip()
        
        if not message:
            print("❌ Debes ingresar un mensaje")
            return
        
        message_data = {
            'customer': customer_name,
            'phone': phone,
            'message': message
        }
        
        self.simulate_whatsapp_conversation(message_data)
    
    def _show_advanced_stats(self):
        """Muestra estadísticas avanzadas"""
        print("\n📊 ESTADÍSTICAS AVANZADAS")
        print("="*50)
        
        # Obtener pedidos de la semana
        orders = self.db_tools.get_orders_by_status(hours_back=168)
        
        if not orders:
            print("No hay datos suficientes para estadísticas.")
            return
        
        # Calcular métricas
        total_revenue = sum(order.total_amount for order in orders)
        avg_order = total_revenue / len(orders)
        
        # Contar por estado
        status_count = {}
        for order in orders:
            status_count[order.status] = status_count.get(order.status, 0) + 1
        
        # Items más populares
        item_count = {}
        for order in orders:
            for item in order.items:
                item_name = item.get('name', 'Desconocido')
                quantity = item.get('quantity', 1)
                item_count[item_name] = item_count.get(item_name, 0) + quantity
        
        print(f"📅 Período: Últimos 7 días")
        print(f"📦 Total pedidos: {len(orders)}")
        print(f"💰 Ingresos totales: ${total_revenue:.2f}")
        print(f"📈 Ticket promedio: ${avg_order:.2f}")
        
        print(f"\n📋 Distribución por estado:")
        for status, count in status_count.items():
            percentage = (count / len(orders)) * 100
            print(f"  • {status}: {count} ({percentage:.1f}%)")
        
        if item_count:
            print(f"\n🏆 Items más populares:")
            sorted_items = sorted(item_count.items(), key=lambda x: x[1], reverse=True)
            for item_name, count in sorted_items[:5]:
                print(f"  • {item_name}: {count} unidades")
    
    def _test_crewai(self):
        """Prueba la integración con CrewAI"""
        if not hasattr(self, 'crew') or not self.crew:
            print("❌ CrewAI no está configurado o no hay LLM disponible.")
            print("   Asegúrate de tener GROQ_API_KEY en .env")
            return
        
        print("\n🧪 PROBANDO CREWAI")
        print("-"*40)
        
        test_message = input("Mensaje para procesar con CrewAI: ").strip()
        
        if not test_message:
            test_message = "Hola, quiero pedir 2 pizzas margarita para las 8 pm"
        
        print(f"\n📤 Enviando a CrewAI: {test_message}")
        print("⏳ Procesando...")
        
        try:
            # Ejecutar crew con el mensaje
            result = self.crew.kickoff(inputs={'message': test_message})
            
            print("\n✅ Resultado de CrewAI:")
            print("-"*40)
            print(result)
            
        except Exception as e:
            print(f"❌ Error en CrewAI: {e}")
            print("💡 Sugerencia: Verifica tu conexión a internet y la API key de Groq")

def main():
    """Función principal"""
    print("🤖 PEDIBOT DEMO - CONFIGURACIÓN")
    print("-"*40)
    
    # Verificar si Groq está configurado
    groq_key = os.getenv('GROQ_API_KEY')
    
    if groq_key and groq_key.startswith('gsk_'):
        print("✅ GROQ_API_KEY detectada")
        use_groq = True
    else:
        print("⚠️  GROQ_API_KEY no encontrada o inválida")
        print("📝 Usando modo simulado")
        use_groq = False
    
    print("\n1. Demo completa (con Groq si está disponible)")
    print("2. Demo simplificada (sin IA)")
    
    choice = input("\nSelecciona opción (1-2): ").strip()
    
    try:
        if choice == '1':
            demo = PedibotDemo(use_groq=use_groq)
            demo.run_interactive_demo()
        elif choice == '2':
            demo = PedibotDemo(use_groq=False)
            demo.run_interactive_demo()
        elif choice == '3':
            # Probar conexión Groq CON MODELO ACTUALIZADO
            if groq_key and groq_key.startswith('gsk_'):
                print("\n🔗 Probando conexión a Groq...")
                try:
                    from groq import Groq
                    client = Groq(api_key=groq_key)
                    
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": "Responde 'OK' en español"}],
                        model="llama-3.3-70b-versatile",  # <-- CAMBIADO
                        max_tokens=10
                    )
                    
                    print(f"✅ Conexión exitosa con llama-3.3-70b-versatile!")
                    print(f"🤖 Respuesta: {response.choices[0].message.content}")
                    
                except Exception as e:
                    print(f"❌ Error de conexión: {e}")
        else:
            print("❌ Opción inválida")
    
    except KeyboardInterrupt:
        print("\n\n👋 ¡Demo interrumpida por el usuario!")
    except Exception as e:
        print(f"\n❌ Error durante la demo: {e}")
        import traceback
        traceback.print_exc()
        


if __name__ == "__main__":
    main()