from typing import TypedDict, Annotated, List, Optional, Dict, Any
from uuid import UUID
import json
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.agent.prompts import SYSTEM_PROMPT, SPECS_TEMPLATE
from app.agent.tools import (
    GeminiReasoner, 
    GeminiImageGenerator,
    generate_kitchen_image,
    edit_kitchen_image
)


class KitchenState(TypedDict):
    """State for the kitchen design agent."""
    messages: Annotated[List[dict], operator.add]
    user_id: str
    conversation_id: str
    
    # Design parameters
    linear_meters: Optional[float]
    shape: Optional[str]
    style: Optional[str]
    materials: Optional[Dict[str, str]]
    colors: Optional[List[str]]
    budget: Optional[str]
    
    # Current design state
    current_image: Optional[str]  # base64
    design_version: int
    design_history: List[dict]
    
    # Agent state
    action: Optional[str]
    needs_clarification: bool
    questions: List[str]
    
    # Response
    response_text: str
    artifacts: List[dict]
    error: Optional[str]


class KitchenDesignAgent:
    """
    LangGraph-based agent for kitchen design generation and iteration.
    
    Flow:
    1. Analyze user input
    2. Determine action (generate, edit, clarify, respond)
    3. Execute action (generate image, edit image, ask questions)
    4. Format response with artifacts
    """
    
    def __init__(self):
        self.reasoner = GeminiReasoner(SYSTEM_PROMPT)
        self.image_generator = GeminiImageGenerator()
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        workflow = StateGraph(KitchenState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_input)
        workflow.add_node("clarify", self._ask_clarification)
        workflow.add_node("generate", self._generate_design)
        workflow.add_node("edit", self._edit_design)
        workflow.add_node("respond", self._generate_response)
        workflow.add_node("format_output", self._format_output)
        
        # Set entry point
        workflow.set_entry_point("analyze")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze",
            self._route_action,
            {
                "clarify": "clarify",
                "generate": "generate",
                "edit": "edit",
                "respond": "respond"
            }
        )
        
        # All paths lead to format_output
        workflow.add_edge("clarify", "format_output")
        workflow.add_edge("generate", "format_output")
        workflow.add_edge("edit", "format_output")
        workflow.add_edge("respond", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _route_action(self, state: KitchenState) -> str:
        """Route to appropriate action based on analysis."""
        if state.get("needs_clarification"):
            return "clarify"
        
        action = state.get("action", "respond")
        
        if action == "generate":
            return "generate"
        elif action == "edit":
            return "edit"
        else:
            return "respond"
    
    async def _analyze_input(self, state: KitchenState) -> dict:
        """Analyze user input to determine intent and extract parameters."""
        
        # Get the last user message
        messages = state.get("messages", [])
        if not messages:
            return {"error": "No message provided"}
        
        last_message = messages[-1]
        user_message = last_message.get("content", "")
        
        # Build context from current state
        context = {
            "linear_meters": state.get("linear_meters"),
            "shape": state.get("shape"),
            "style": state.get("style"),
            "materials": state.get("materials"),
            "has_current_design": state.get("current_image") is not None,
            "design_version": state.get("design_version", 0)
        }
        
        # Analyze with Gemini
        analysis = await self.reasoner.analyze_request(user_message, context)
        
        # Update state based on analysis
        updates = {
            "action": analysis.get("action", "respond"),
            "needs_clarification": analysis.get("action") == "clarification",
            "questions": analysis.get("questions_to_ask", [])
        }
        
        # Update design parameters if provided
        if analysis.get("linear_meters"):
            updates["linear_meters"] = analysis["linear_meters"]
        if analysis.get("shape"):
            updates["shape"] = analysis["shape"]
        if analysis.get("style"):
            updates["style"] = analysis["style"]
        if analysis.get("materials"):
            current_materials = state.get("materials", {})
            current_materials.update({k: v for k, v in analysis["materials"].items() if v})
            updates["materials"] = current_materials
        if analysis.get("colors"):
            updates["colors"] = analysis["colors"]
        if analysis.get("budget"):
            updates["budget"] = analysis["budget"]
        
        # Check if we have enough info to generate
        if updates["action"] == "generate":
            if not updates.get("linear_meters") and not state.get("linear_meters"):
                updates["needs_clarification"] = True
                updates["questions"] = ["¿Cuántos metros lineales tiene disponibles para su cocina?"]
        
        return updates
    
    async def _ask_clarification(self, state: KitchenState) -> dict:
        """Generate clarification questions."""
        
        questions = state.get("questions", [])
        
        if not questions:
            # Generate contextual questions
            missing = []
            if not state.get("linear_meters"):
                missing.append("metros lineales disponibles")
            if not state.get("shape"):
                missing.append("configuración deseada (L, U, lineal, etc.)")
            if not state.get("style"):
                missing.append("estilo preferido")
            
            if missing:
                questions = [f"Para crear tu diseño ideal, necesito saber: {', '.join(missing)}. ¿Podrías proporcionarme esta información?"]
            else:
                questions = ["¿Podrías darme más detalles sobre lo que te gustaría modificar?"]
        
        # Format response
        response_text = "\n".join(questions)
        
        # Add helpful suggestions
        if not state.get("shape"):
            response_text += "\n\n**Configuraciones disponibles:**\n"
            response_text += "- **Lineal (I):** Ideal para espacios estrechos\n"
            response_text += "- **En L:** La más versátil, aprovecha esquinas\n"
            response_text += "- **En U:** Máximo almacenamiento, espacios amplios\n"
            response_text += "- **Paralela:** Perfecta para cocinas tipo pasillo\n"
        
        return {
            "response_text": response_text,
            "artifacts": []
        }
    
    async def _generate_design(self, state: KitchenState) -> dict:
        """Generate a new kitchen design."""
        
        linear_meters = state.get("linear_meters", 3.0)
        shape = state.get("shape", "L")
        style = state.get("style", "modern")
        materials = state.get("materials", {
            "cabinets": "lacquered MDF",
            "countertop": "quartz",
            "backsplash": "ceramic tiles"
        })
        colors = state.get("colors", ["white", "gray"])
        
        # Generate image
        result = await generate_kitchen_image(
            linear_meters=linear_meters,
            shape=shape,
            style=style,
            materials=materials,
            colors=colors
        )
        
        if not result.get("success"):
            return {
                "response_text": f"Lo siento, hubo un problema al generar la imagen: {result.get('error', 'Error desconocido')}. ¿Podrías intentarlo de nuevo?",
                "artifacts": [],
                "error": result.get("error")
            }
        
        # Get image
        images = result.get("images", [])
        if not images:
            return {
                "response_text": "No se pudo generar la imagen. Por favor intenta de nuevo.",
                "artifacts": [],
                "error": "No images generated"
            }
        
        image_base64 = images[0]
        new_version = state.get("design_version", 0) + 1
        
        # Generate specifications
        specs = self._generate_specs(linear_meters, shape, style, materials)
        
        # Build response
        shape_names = {
            "I": "lineal",
            "L": "en L",
            "U": "en U",
            "G": "en G",
            "parallel": "paralela"
        }
        
        response_text = f"""## Diseño de Cocina - Versión {new_version}

He creado un diseño de cocina **{style}** con configuración **{shape_names.get(shape, shape)}** de **{linear_meters} metros lineales**.

### Características principales:
- **Gabinetes:** {materials.get('cabinets', 'MDF lacado')}
- **Cubierta:** {materials.get('countertop', 'Cuarzo')}
- **Salpicadero:** {materials.get('backsplash', 'Azulejo cerámico')}
- **Paleta de colores:** {', '.join(colors)}

¿Te gustaría hacer alguna modificación? Puedo ajustar colores, materiales, agregar o quitar elementos, cambiar el estilo, etc."""

        artifacts = [
            {
                "type": "image",
                "title": f"Diseño de Cocina v{new_version}",
                "image_data": image_base64,
                "metadata": {
                    "linear_meters": linear_meters,
                    "shape": shape,
                    "style": style,
                    "version": new_version
                }
            },
            {
                "type": "specs",
                "title": "Especificaciones Técnicas",
                "content": specs,
                "metadata": {}
            }
        ]
        
        # Update design history
        design_history = state.get("design_history", [])
        design_history.append({
            "version": new_version,
            "params": {
                "linear_meters": linear_meters,
                "shape": shape,
                "style": style,
                "materials": materials
            }
        })
        
        return {
            "response_text": response_text,
            "artifacts": artifacts,
            "current_image": image_base64,
            "design_version": new_version,
            "design_history": design_history
        }
    
    async def _edit_design(self, state: KitchenState) -> dict:
        """Edit existing kitchen design."""
        
        current_image = state.get("current_image")
        if not current_image:
            # No current design, generate new one
            return await self._generate_design(state)
        
        # Get edit instructions from last message
        messages = state.get("messages", [])
        edit_instructions = messages[-1].get("content", "") if messages else ""
        
        # Edit image
        result = await edit_kitchen_image(
            base_image=current_image,
            edit_instructions=edit_instructions,
            current_params={
                "linear_meters": state.get("linear_meters"),
                "shape": state.get("shape"),
                "style": state.get("style")
            }
        )
        
        if not result.get("success"):
            # If edit fails, try regenerating with modifications
            return {
                "response_text": f"Estoy regenerando el diseño con tus modificaciones...",
                "artifacts": [],
                "action": "generate"  # Trigger regeneration
            }
        
        images = result.get("images", [])
        if not images:
            return await self._generate_design(state)
        
        image_base64 = images[0]
        new_version = state.get("design_version", 0) + 1
        
        response_text = f"""## Diseño Actualizado - Versión {new_version}

He aplicado las modificaciones solicitadas al diseño. 

¿Qué te parece? Puedo seguir ajustando cualquier detalle que necesites."""

        artifacts = [
            {
                "type": "image",
                "title": f"Diseño de Cocina v{new_version}",
                "image_data": image_base64,
                "metadata": {
                    "version": new_version,
                    "edit": True
                }
            }
        ]
        
        return {
            "response_text": response_text,
            "artifacts": artifacts,
            "current_image": image_base64,
            "design_version": new_version
        }
    
    async def _generate_response(self, state: KitchenState) -> dict:
        """Generate conversational response without image generation."""
        
        messages = state.get("messages", [])
        if not messages:
            return {"response_text": "¡Hola! Soy KitchenMaster AI, tu experto en diseño de cocinas integrales. ¿En qué puedo ayudarte hoy?"}
        
        # Convert messages to chat format
        chat_history = []
        for msg in messages[:-1]:
            chat_history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        self.reasoner.start_chat(chat_history)
        
        last_message = messages[-1].get("content", "")
        response = await self.reasoner.send_message(last_message)
        
        return {
            "response_text": response,
            "artifacts": []
        }
    
    async def _format_output(self, state: KitchenState) -> dict:
        """Format final output."""
        return {
            "response_text": state.get("response_text", ""),
            "artifacts": state.get("artifacts", [])
        }
    
    def _generate_specs(
        self, 
        linear_meters: float, 
        shape: str, 
        style: str, 
        materials: dict
    ) -> str:
        """Generate technical specifications."""
        
        # Calculate module distribution based on meters
        modules = []
        remaining = linear_meters
        
        # Standard modules
        if remaining >= 0.9:
            modules.append("1x Módulo fregadero (90cm)")
            remaining -= 0.9
        if remaining >= 0.6:
            modules.append("1x Módulo estufa/parrilla (60cm)")
            remaining -= 0.6
        if remaining >= 0.6:
            modules.append("1x Módulo refrigerador (60cm)")
            remaining -= 0.6
        
        # Fill rest with storage
        storage_60 = int(remaining / 0.6)
        remaining -= storage_60 * 0.6
        storage_40 = int(remaining / 0.4)
        
        if storage_60 > 0:
            modules.append(f"{storage_60}x Módulo almacenamiento (60cm)")
        if storage_40 > 0:
            modules.append(f"{storage_40}x Módulo almacenamiento (40cm)")
        
        module_distribution = "\n".join(f"- {m}" for m in modules)
        
        # Appliances
        appliances = """- Campana extractora
- Estufa/Parrilla 4 quemadores
- Horno empotrable (opcional)
- Refrigerador
- Microondas empotrable (opcional)
- Lavavajillas (opcional)"""
        
        # Cost estimation based on budget
        cost_ranges = {
            "low": "$15,000 - $25,000 MXN",
            "medium": "$25,000 - $45,000 MXN",
            "high": "$45,000 - $80,000 MXN",
            "premium": "$80,000 - $150,000+ MXN"
        }
        
        specs = f"""## Especificaciones Técnicas

### Dimensiones
- **Metros lineales:** {linear_meters}m
- **Configuración:** {shape}
- **Altura muebles bajos:** 85 cm
- **Altura muebles altos:** 80 cm
- **Profundidad muebles bajos:** 60 cm

### Materiales
- **Gabinetes:** {materials.get('cabinets', 'MDF lacado')}
- **Cubierta:** {materials.get('countertop', 'Cuarzo')}
- **Salpicadero:** {materials.get('backsplash', 'Azulejo')}
- **Herrajes:** Cierre suave, bisagras de 110°

### Distribución de Módulos
{module_distribution}

### Electrodomésticos Sugeridos
{appliances}

### Estimación de Inversión
Rango aproximado: {cost_ranges.get('medium', '$30,000 - $50,000 MXN')}

*Nota: Los precios son aproximados y pueden variar según proveedor y ubicación.*"""
        
        return specs
    
    async def run(
        self,
        user_message: str,
        user_id: str,
        conversation_id: str,
        existing_state: dict = None
    ) -> dict:
        """
        Run the agent with a user message.
        
        Args:
            user_message: The user's input
            user_id: User identifier for memory
            conversation_id: Conversation identifier
            existing_state: Previous state to continue from
            
        Returns:
            Dict with response_text, artifacts, and updated state
        """
        
        # Build initial state
        state = existing_state or {
            "messages": [],
            "user_id": user_id,
            "conversation_id": conversation_id,
            "linear_meters": None,
            "shape": None,
            "style": None,
            "materials": {},
            "colors": [],
            "budget": None,
            "current_image": None,
            "design_version": 0,
            "design_history": [],
            "action": None,
            "needs_clarification": False,
            "questions": [],
            "response_text": "",
            "artifacts": [],
            "error": None
        }
        
        # Add new message
        state["messages"] = state.get("messages", []) + [{
            "role": "user",
            "content": user_message
        }]
        
        # Run graph
        config = {"configurable": {"thread_id": f"{user_id}:{conversation_id}"}}
        
        result = await self.graph.ainvoke(state, config)
        
        # Extract response
        return {
            "response_text": result.get("response_text", ""),
            "artifacts": result.get("artifacts", []),
            "state": {
                "linear_meters": result.get("linear_meters"),
                "shape": result.get("shape"),
                "style": result.get("style"),
                "materials": result.get("materials"),
                "colors": result.get("colors"),
                "budget": result.get("budget"),
                "current_image": result.get("current_image"),
                "design_version": result.get("design_version"),
                "design_history": result.get("design_history"),
                "messages": result.get("messages")
            }
        }
