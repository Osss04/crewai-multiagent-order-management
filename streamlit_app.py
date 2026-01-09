import os
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

from src.tools.menu_tools import MenuTools
from src.tools.db_tools import DatabaseTools
from src.tools.whatsapp_tools import WhatsAppTools
from src.tools.llm_tools import GroqLLMFactory, OrderExtractor


st.set_page_config(
    page_title="Pedibot Demo",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Pedibot – Demo de Automatización de Pedidos")
st.caption("Sistema multiagente con extracción de pedidos mediante LLM")


@st.cache_resource
def init_services(use_groq: bool = True):
    menu = MenuTools()
    db = DatabaseTools()
    whatsapp = WhatsAppTools(use_twilio=False)

    llm = GroqLLMFactory.create() if use_groq else None
    extractor = OrderExtractor(llm)

    return menu, db, whatsapp, extractor, llm


use_groq = st.sidebar.toggle("Usar Groq LLM", value=True)
menu_tools, db_tools, whatsapp_tools, extractor, llm = init_services(use_groq)


st.subheader("📱 Mensaje del cliente")

default_message = "Hola, quiero 2 pizzas margarita y 1 coca-cola para las 20:30"
message = st.text_area("Escribe un mensaje tipo WhatsApp:", default_message, height=120)
phone = st.text_input("Teléfono del cliente", "+12345678901")
customer = st.text_input("Nombre del cliente", "Cliente Demo")

if st.button("🚀 Procesar mensaje"):
    st.divider()

    
    analysis = whatsapp_tools.process_incoming_message(message, phone)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Análisis")
        st.json({
            "intent": analysis["intent"],
            "is_order": analysis["is_order"]
        })

   
    # Extracción del pedido
    if analysis["is_order"]:
        extracted = extractor.extract(message)

        # Normalizar contrato
        extracted = {
            "items": extracted.get("items", []),
            "requested_time": extracted.get("requested_time", "ASAP"),
            "notes": extracted.get("notes", "")
        }

        with col2:
            st.subheader("📋 Pedido extraído")
            st.json(extracted)

        # Validación del pedido
        validation = menu_tools.validate_order_items(extracted["items"])

        st.subheader("✅ Validación del pedido")

        if validation["valid"]:
            st.success("Pedido válido")

            st.write("**Items validados:**")
            st.table(validation["validated_items"])

            st.metric("💰 Total", f"${validation['total_price']:.2f}")

            # Registrar pedido
            if st.button("📦 Registrar pedido"):
                order_data = {
                    "customer_name": customer,
                    "customer_phone": phone,
                    "items": validation["validated_items"],
                    "total_amount": validation["total_price"],
                    "requested_time": extracted["requested_time"],
                    "notes": extracted["notes"]
                }

                result = db_tools.create_order(order_data)

                if result["success"]:
                    st.success(f"Pedido registrado correctamente 🎉")
                    st.code(result["order_id"])

                    summary = whatsapp_tools.format_order_summary(
                        {**order_data, **result},
                        menu_tools
                    )

                    st.subheader("📤 Mensaje de confirmación")
                    st.text(summary)

                else:
                    st.error(result.get("error", "Error registrando pedido"))

        else:
            st.error("Pedido inválido")
            st.write(validation["issues"])

    else:
        st.info("El mensaje no es un pedido.")
