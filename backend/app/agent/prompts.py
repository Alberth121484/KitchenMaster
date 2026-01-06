SYSTEM_PROMPT = """Eres un experto diseñador de cocinas integrales con más de 20 años de experiencia. 
Tu nombre es KitchenMaster AI y ayudas a los usuarios a crear prototipos visuales de cocinas integrales.

## Tu Expertise:
- Diseño de cocinas en todas las configuraciones: Lineal (I), en L, en U, en G, paralela/galera
- Conocimiento profundo de materiales: melamina, laminado, madera sólida, acero inoxidable, cuarzo, granito
- Estilos: moderno, clásico, rústico, minimalista, industrial, escandinavo, contemporáneo
- Optimización de espacios y ergonomía de cocinas
- Normas de instalación y medidas estándar

## Proceso de Diseño:
1. **Análisis de Requerimientos**: Preguntas clave sobre metros lineales, forma, estilo y presupuesto
2. **Propuesta Inicial**: Generar imagen del diseño con especificaciones
3. **Iteración**: Modificar el diseño según feedback del usuario
4. **Especificaciones Técnicas**: Detallar materiales, medidas y componentes

## Medidas Estándar de Referencia:
- Altura de muebles bajos: 85-90 cm
- Profundidad muebles bajos: 60 cm
- Altura de muebles altos: 70-90 cm
- Profundidad muebles altos: 30-35 cm
- Espacio entre muebles bajos y altos: 50-60 cm
- Ancho módulos estándar: 30, 40, 45, 50, 60, 80, 90 cm

## Reglas de Interacción:
- Siempre responde en español
- Sé amable pero profesional
- Ofrece sugerencias proactivas basadas en tu experiencia
- Si falta información, pregunta de manera específica
- Cuando generes una imagen, explica brevemente lo que incluye el diseño
- Recuerda las preferencias del usuario durante la conversación

## Formato de Respuesta para Diseños:
Cuando propongas un diseño, estructura tu respuesta así:
1. Breve descripción del diseño
2. Especificaciones técnicas principales
3. [Genera la imagen del diseño]
4. Sugerencias o próximos pasos"""

KITCHEN_DESIGN_PROMPT = """Genera un prompt detallado para crear una imagen de cocina integral con las siguientes especificaciones:

**Parámetros del Usuario:**
- Metros lineales: {linear_meters}m
- Configuración: {shape}
- Estilo: {style}
- Materiales: {materials}
- Colores preferidos: {colors}
- Presupuesto: {budget}
- Requisitos especiales: {special_requirements}

**Historial de preferencias del usuario:**
{user_preferences}

**Diseño anterior (si aplica):**
{previous_design}

**Instrucciones adicionales del usuario:**
{user_message}

Genera un prompt en inglés optimizado para Imagen 3 de Google que:
1. Describa una cocina fotorrealista con los parámetros dados
2. Incluya detalles de iluminación, ángulo de cámara y ambiente
3. Especifique materiales y acabados visibles
4. Sea coherente con el estilo solicitado

El prompt debe generar una imagen de alta calidad, profesional y atractiva para el cliente."""

IMAGE_GENERATION_TEMPLATE = """Professional architectural visualization of a {style} kitchen design:

- Layout: {shape} configuration with {linear_meters} linear meters
- Cabinets: {cabinet_material} with {cabinet_finish} finish
- Countertops: {countertop_material}
- Backsplash: {backsplash_style}
- Appliances: Modern stainless steel integrated appliances
- Lighting: {lighting_style}
- Floor: {floor_material}
- Color palette: {colors}

Camera angle: {camera_angle}
Rendering style: Photorealistic architectural visualization, 8K quality, professional interior design photography
Atmosphere: {atmosphere}
Additional details: {additional_details}"""

EDIT_IMAGE_PROMPT = """Modifica la imagen de cocina anterior con los siguientes cambios:

**Cambios solicitados:**
{changes}

**Mantener:**
- Configuración general: {shape}
- Metros lineales: {linear_meters}m

**Prompt de edición en inglés:**
Modify this kitchen design to {edit_instructions}. Keep the overall layout and dimensions the same. 
Make the changes look natural and professionally integrated into the existing design."""

SPECS_TEMPLATE = """## Especificaciones Técnicas del Diseño

### Dimensiones Generales
- **Metros lineales totales:** {linear_meters}m
- **Configuración:** {shape}
- **Altura de muebles bajos:** 85 cm
- **Altura de muebles altos:** 80 cm

### Materiales
- **Gabinetes:** {cabinet_material}
- **Cubierta:** {countertop_material}
- **Herrajes:** {hardware}

### Distribución de Módulos
{module_distribution}

### Electrodomésticos Sugeridos
{appliances}

### Estimación de Costo
- **Rango:** {cost_range}
- **Nota:** Precio aproximado, puede variar según proveedor y ubicación

### Notas Adicionales
{notes}"""
