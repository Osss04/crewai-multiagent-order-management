# Sistema de Gestión de Pedidos Multiagente con CrewAI

Este proyecto implementa un **sistema multiagente** para la gestión de pedidos en un restaurante utilizando **CrewAI** y **LLMs**. El sistema gestiona de forma autónoma los pedidos de los usuarios expresados en lenguaje natural, los valida y los persiste en una base de datos, siguiendo una arquitectura modular y orientada a entornos de producción.

---

## 🧠 Arquitectura del Sistema

El sistema sigue una **arquitectura multiagente**, donde cada agente tiene un rol y una responsabilidad bien definidos. Los agentes colaboran mediante tareas estructuradas coordinadas por una **Crew**, lo que permite una clara separación de responsabilidades y flujos de trabajo escalables.

### Flujo de alto nivel:
1. El usuario envía un pedido a través de una interfaz Streamlit.
2. El pedido es procesado por un conjunto de agentes especializados.
3. Los agentes se comunican y razonan utilizando un LLM (Grok a través de LiteLLM).
4. Los pedidos validados se almacenan en una base de datos.
5. El sistema devuelve una confirmación estructurada o un mensaje de error.

---

## 🤖 Agentes y Roles

El sistema está compuesto por los siguientes agentes:

### 🧾 Agente de Recepción de Pedidos
- Interpreta la entrada del usuario en lenguaje natural.
- Extrae información estructurada del pedido (productos, cantidades, peticiones especiales).
- Gestiona pedidos ambiguos o incompletos mediante razonamiento con LLMs.

### ✅ Agente de Validación de Pedidos
- Valida las reglas de negocio (disponibilidad del menú, cantidades, restricciones).
- Garantiza la coherencia y corrección del pedido.
- Solicita aclaraciones al usuario si la validación falla.

### 💾 Agente de Persistencia
- Gestiona las interacciones con la base de datos.
- Almacena los pedidos validados en una base de datos relacional.
- Garantiza la integridad transaccional y el manejo de errores.

Cada agente se implementa como un **Agente de CrewAI**, con su propia:
- Descripción del rol
- Objetivo
- Contexto o *backstory*
- Herramientas (cuando aplica)

---

## 🧩 Tareas y Orquestación de la Crew

Las tareas definen **qué debe hacerse**, mientras que los agentes definen **quién lo hace**.

Las tareas típicas incluyen:
- Análisis y estructuración del pedido en bruto.
- Validación de restricciones del pedido.
- Persistencia del pedido en la base de datos.
- Generación de una respuesta final para el usuario.

Estas tareas son orquestadas por una **Crew**, que:
- Controla el orden de ejecución.
- Gestiona el contexto compartido entre agentes.
- Permite razonamiento colaborativo entre agentes.

Este diseño facilita la extensión del sistema (por ejemplo, añadiendo un agente de pagos o un agente de recomendaciones).

---

## 🧠 Integración del LLM (LiteLLM + Grok)

El sistema integra **Grok** como LLM subyacente a través de **LiteLLM**, lo que proporciona:
- Una interfaz de API unificada para llamadas a LLMs.
- Facilidad para cambiar de modelo si es necesario.
- Configuración centralizada mediante variables de entorno.

Las llamadas al LLM se utilizan para:
- Comprensión de lenguaje natural.
- Lógica de razonamiento y validación.
- Generación de salidas estructuradas a partir de texto libre.

Todo el acceso al LLM está securizado mediante variables de entorno y **nunca se codifica de forma explícita en el código fuente**.

---

## 🚀 Instalación y Ejecución

### 1. Crear entorno virtual
```bash
py -3.11 -m venv .venv
```

### 2. Activar entorno virtual
```bash
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar depedencias
```bash
python -m pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea un archivo `env` e introduce tu *Groq API key*:
```bash
GROQ_API_KEY="tu_api_key"
```

### 5. Corre la aplicación de Streamlit
```bash
streamlit run .\streamlit_app.py
```