import yaml
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from typing import Dict, List
import os
from dotenv import load_dotenv
import litellm

load_dotenv()

class CrewConfigLoader:
    def __init__(self, config_path: str = "config"):
        self.config_path = config_path
        self.llm = self._setup_llm_with_litellm()  # <-- CAMBIADO
    
    def _setup_llm_with_litellm(self):
        """Configura LLM usando LiteLLM para Groq"""
        groq_key = os.getenv('GROQ_API_KEY')
        
        if not groq_key:
            print("⚠️  GROQ_API_KEY no encontrada")
            return None
        
        if not groq_key.startswith('gsk_'):
            print(f"⚠️  GROQ_API_KEY formato incorrecto")
            return None
        
        try:
            print("🤖 Configurando LiteLLM para Groq...")
            
            # Configurar LiteLLM
            litellm.drop_params = True
            litellm.set_verbose = False
            
            # Crear LLM de CrewAI usando LiteLLM
            llm = LLM(
                model="groq/llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1024,
                api_key=groq_key,
                # Configuración específica para LiteLLM
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )
            
            # Test simple
            print("✅ LiteLLM configurado para Groq")
            print(f"📊 Modelo: llama-3.3-70b-versatile")
            
            return llm
            
        except Exception as e:
            print(f"❌ Error configurando LiteLLM: {e}")
            print("💡 Ejecuta: pip install litellm")
            return None
    
    def load_agents(self) -> Dict[str, Agent]:
        """Carga agentes desde agents.yaml"""
        try:
            with open(os.path.join(self.config_path, "agents.yaml"), 'r', encoding='utf-8') as file:
                agents_config = yaml.safe_load(file)
        except Exception as e:
            print(f"❌ Error cargando agents.yaml: {e}")
            return {}
        
        agents = {}
        for agent_name, config in agents_config.get('agents', {}).items():
            try:
                agent_kwargs = {
                    'role': config.get('role', ''),
                    'goal': config.get('goal', ''),
                    'backstory': config.get('backstory', ''),
                    'verbose': config.get('verbose', True),
                    'allow_delegation': config.get('allow_delegation', False),
                    'max_iter': 3,
                    'max_rpm': 20
                }
                
                # Solo añadir LLM si está disponible
                if self.llm:
                    agent_kwargs['llm'] = self.llm
                    print(f"   ✅ {agent_name} - Con LLM")
                else:
                    print(f"   ⚠️  {agent_name} - Sin LLM (modo simulado)")
                
                agents[agent_name] = Agent(**agent_kwargs)
                
            except Exception as e:
                print(f"❌ Error creando agente {agent_name}: {e}")
                continue
        
        return agents
    
    def load_tasks(self, agents: Dict[str, Agent]) -> Dict[str, Task]:
        """Carga tareas desde tasks.yaml"""
        try:
            with open(os.path.join(self.config_path, "tasks.yaml"), 'r', encoding='utf-8') as file:
                tasks_config = yaml.safe_load(file)
        except Exception as e:
            print(f"❌ Error cargando tasks.yaml: {e}")
            return {}
        
        tasks = {}
        for task_name, config in tasks_config.get('tasks', {}).items():
            try:
                agent_name = config.get('agent')
                if agent_name not in agents:
                    print(f"⚠️  Agente '{agent_name}' no encontrado para tarea '{task_name}'")
                    continue
                
                agent = agents[agent_name]
                
                # Obtener tareas de contexto si existen
                context_tasks = []
                for context_task_name in config.get('context', []):
                    if context_task_name in tasks:
                        context_tasks.append(tasks[context_task_name])
                
                task_kwargs = {
                    'description': config.get('description', ''),
                    'expected_output': config.get('expected_output', ''),
                    'agent': agent,
                }
                
                if context_tasks:
                    task_kwargs['context'] = context_tasks
                
                tasks[task_name] = Task(**task_kwargs)
                print(f"   ✅ Tarea: {task_name}")
                
            except Exception as e:
                print(f"❌ Error creando tarea {task_name}: {e}")
                continue
        
        return tasks
    
    def load_crew_config(self) -> Dict:
        """Carga configuración del crew desde crew.yaml"""
        try:
            with open(os.path.join(self.config_path, "crew.yaml"), 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"❌ Error cargando crew.yaml: {e}")
            return {'crew': {'agents': [], 'tasks': [], 'process': 'sequential'}}
    
    def create_crew(self) -> Crew:
        """Crea y retorna el crew completo"""
        print("🤖 Creando Crew de agentes...")
        
        # Cargar agentes y tareas
        agents = self.load_agents()
        
        if not agents:
            print("❌ No se pudieron cargar agentes")
            raise Exception("No hay agentes configurados")
        
        tasks = self.load_tasks(agents)
        
        if not tasks:
            print("❌ No se pudieron cargar tareas")
            raise Exception("No hay tareas configuradas")
        
        # Cargar configuración del crew
        crew_config = self.load_crew_config()
        
        # Convertir nombres a objetos
        crew_agents = []
        for name in crew_config['crew']['agents']:
            if name in agents:
                crew_agents.append(agents[name])
            else:
                print(f"⚠️  Agente '{name}' no encontrado para el crew")
        
        crew_tasks = []
        for name in crew_config['crew']['tasks']:
            if name in tasks:
                crew_tasks.append(tasks[name])
            else:
                print(f"⚠️  Tarea '{name}' no encontrada para el crew")
        
        if not crew_agents or not crew_tasks:
            raise Exception("Crew incompleto - faltan agentes o tareas")
        
        # Crear crew
        try:
            process_name = crew_config['crew'].get('process', 'sequential').lower()

            process_map = {
                'sequential': Process.sequential,
                'hierarchical': Process.hierarchical
            }

            crew = Crew(
                agents=crew_agents,
                tasks=crew_tasks,
                process=process_map.get(process_name, Process.sequential),
                verbose=crew_config['crew'].get('verbose', True),
                memory=crew_config['crew'].get('memory', False)
            )
            
            print("✅ Crew creado exitosamente")
            return crew
            
        except Exception as e:
            print(f"❌ Error creando crew: {e}")
            raise