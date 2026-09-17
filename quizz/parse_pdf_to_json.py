import re
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_text_file = r"C:\Users\facun\.gemini\antigravity\brain\f06d2f62-d69a-464e-9ce2-4a86f0ae9805\scratch\extracted_text.txt"
output_file = r"c:\Users\facun\OneDrive\Escritorio\quizz final\questions.json"

if not os.path.exists(pdf_text_file):
    print("Extracted text file not found!")
    exit(1)

with open(pdf_text_file, "r", encoding="utf-8") as f:
    text = f.read()

# ----------------- CLEANUP FUNCTION -----------------
def clean_text_v2(t):
    # Normalize carriage returns
    t = t.replace('\r\n', '\n')
    
    # Strip PAGE headers completely first
    t = re.sub(r'--- PAGE \d+ ---', '', t)
    
    # First protect bullets and questions
    t = re.sub(r'●', ' |BULLET| ', t)
    # Match question starts like "1. La respuesta" or "58.3 Fase"
    t = re.sub(r'(?:^|\n)\s*(\d+(?:\.\d+)?)\s*\.\s+(?=(?:La\s+respuesta|Las\s+respuestas|Las\s+afirmaciones|La\s+afirmación|El\s+orden|Las\s+propiedades|2\s+Trabajador|Correcta:|Fase|Trabajador))', r' |QUESTION_\1| ', t, flags=re.IGNORECASE)
    
    # Normalize all whitespace to single spaces
    t = re.sub(r'\s+', ' ', t)
    
    # Restore bullets and questions
    t = t.replace(' |BULLET| ', '\n● ')
    t = re.sub(r' \|QUESTION_([\d\.]+)\| ', r'\n\n\1. ', t)
    
    # Clean up spaces around punctuation
    t = re.sub(r'\s+\.', '.', t)
    t = re.sub(r'\s+,', ',', t)
    t = re.sub(r'\s+:', ':', t)
    t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'\s+\)', ')', t)
    t = re.sub(r'\s+¿', ' ¿', t)
    t = re.sub(r'\s+\?', '?', t)
    
    return t.strip()

cleaned_text = clean_text_v2(text)
blocks = cleaned_text.split('\n\n')

# Predefined distractor pools for smart match
distractors_map = {
    "retrospectiva": ["Sprint Planning", "Sprint Review", "Daily Scrum"],
    "entrevista": ["Cuestionario/Encuesta", "Observación directa", "Lluvia de Ideas (Brainstorming)"],
    "tareas": ["Historias de Usuario", "Épicas", "Temas", "Casos de Uso"],
    "requerimientos del negocio": ["Requerimientos del Usuario", "Requerimientos del Sistema", "Requisitos de Software"],
    "modelo conceptual": ["Diagrama de Actividades", "Modelo de Casos de Uso", "Diagrama de Clases Físico"],
    "no funcional del producto": ["Funcional del Producto", "No Funcional del Proceso", "Requerimiento de Dominio"],
    "operativa": ["Técnica", "Económica", "Financiera"],
    "abstraccion": ["Conceptualizacion", "Simbolizacion", "Sincronizacion"],
    "correcta": ["No ambigua", "Completa", "Priorizada (o clasificada)"],
    "falso": ["Verdadero"],
    "verdadero": ["Falso"],
    "boundary": ["Control", "Entidad", "Actor"],
    "control": ["Boundary (Interfaz)", "Entidad", "Actor"],
    "entidad": ["Boundary (Interfaz)", "Control", "Actor"],
    "casos de uso del negocio": ["Casos de Uso del Sistema", "Diagramas de Actividad", "Diagramas de Estado"],
    "casos de uso del sistema": ["Casos de Uso del Negocio", "Diagramas de Secuencia", "Diagramas de Despliegue"],
    "product owner": ["Scrum Master", "Developers", "Stakeholders"],
    "scrum master": ["Product Owner", "Developers", "Stakeholders"],
    "moscow": ["INVEST", "FIBONACCI", "SMART"],
    "dado-cuando-entonces": ["Como-Quiero-Para", "MoSCoW", "INVEST"]
}

# Mapping of custom manual questions/answers for key questions
manual_questions = {
    "1": {
        "question": "¿Cuáles son los beneficios o ventajas principales de utilizar preguntas cerradas en una entrevista?",
        "options": ["Facilitan la comparacion de varias entrevistas", "Permiten mayor espontaneidad en el entrevistado", "El entrevistado encuentra el proceso más interesante", "Permiten descubrir vías de cuestionamiento adicionales"]
    },
    "2": {
        "question": "En el contexto de Historias de Usuario, ¿cuál es el propósito de la técnica de comportamiento DADO-CUANDO-ENTONCES (formato Gherkin)?",
        "options": ["Escribir los Criterios de Aceptacion de la Historia de Usuario", "Definir la estructura de la base de datos", "Asignar la prioridad de negocio (MoSCoW)", "Desglosar las tareas técnicas para los desarrolladores"]
    },
    "3": {
        "question": "En la metodología Scrum, ¿cuál es el evento dedicado a la mejora continua del propio equipo, donde se analiza el proceso de trabajo?",
        "options": ["Retrospectiva", "Sprint Planning", "Sprint Review", "Daily Scrum"]
    },
    "4": {
        "question": "¿Cuál de las siguientes afirmaciones NO es una consideración apropiada sobre el estudio de viabilidad?",
        "options": ["Es una decision a cargo del analista de sistema sobre si resulta conveniente seguir con el proyecto", "Un compromiso por parte de los directivos sólo significa que se realizará un estudio, no que se aceptará forzosamente", "El proceso de evaluación es muy útil para desechar proyectos que se contraponen con los objetivos corporativos", "Aunque es laborioso, el estudio de factibilidad ahorra mucho tiempo y dinero a largo plazo"]
    },
    "5": {
        "question": "¿Cuál es el resultado principal en el que se materializa un estudio de viabilidad (EV)?",
        "options": ["Un informe que recomiende si merece o no la pea seguir con la igenieria de requerimientos y el proceso de desarrollo del Sistema", "Un análisis detallado de todos los requerimientos y servicios del sistema", "Una estimación exacta y cerrada del costo-beneficio del proyecto", "Una planificación detallada del proyecto de desarrollo de software"]
    },
    "6": {
        "question": "Un requisito que impone restricciones sobre la disponibilidad y el tiempo operativo del sistema (por ejemplo, estar disponible 24/7 sin fallas) es un requerimiento:",
        "options": ["No Funcional del Producto", "Funcional del Producto", "No Funcional del Proceso", "Requerimiento de Dominio"]
    },
    "7": {
        "question": "¿Cuál de las siguientes es una característica correcta de un Caso de Uso?",
        "options": ["Esta asociado a uno o varios requisitos funcionales", "Muestra detalladamente cómo el sistema operará internamente", "Representa un único escenario de ejecución posible", "Está asociado siempre a un único e indivisible requisito funcional"]
    },
    "8": {
        "question": "En Scrum, ¿por qué elementos está compuesto únicamente el Sprint Backlog (Pila del Sprint)?",
        "options": ["Tareas", "Historias de Usuario", "Épicas", "Temas"]
    },
    "9": {
        "question": "¿Verdadero o Falso? Los sistemas de información transaccional (TPS) funcionan en el nivel operacional de la organización, asitiendo a la alta dirección.",
        "options": ["Verdadero", "Falso"]
    },
    "10": {
        "question": "Al iniciar un proyecto de sistemas, ¿qué nivel de requerimientos define el 'porqué' del desarrollo y justifica el proyecto?",
        "options": ["Requerimientos del Negocio", "Requerimientos del Usuario", "Requerimientos del Sistema (Funcionales)", "Requerimientos No Funcionales"]
    },
    "11": {
        "question": "¿Qué técnica de recopilación de datos permite exclusivamente al analista evaluar tanto lo que se dice como la comunicación no verbal (cómo se dice)?",
        "options": ["Entrevista", "Cuestionario/Encuesta", "Observación directa", "Lluvia de Ideas (Brainstorming)"]
    },
    "12": {
        "question": "¿De qué factor principal depende el éxito de una entrevista de relevamiento?",
        "options": ["La habilidad del entrevistador y de su preparacion para la misma", "La disposición de mucho tiempo para llevarla a cabo", "La utilización de un lenguaje sumamente técnico", "La secuencia en la que se formulen las preguntas"]
    },
    "13": {
        "question": "¿Cuál de las siguientes afirmaciones representa correctamente uno de los valores fundamentales del Manifiesto Ágil?",
        "options": ["Hay que potenciar la colaboracion con el cliente frente a la negociacion de contratos precisos", "Hay que potenciar la colaboración con el cliente frente a la documentación exhaustiva", "Si se plantean cambios con posterioridad a la planificación hay que ajustarse estrictamente al plan", "Se valoran los procesos y las herramientas por encima de los individuos y las interacciones"]
    },
    "14": {
        "question": "¿Qué herramienta nos permite descomponer y visualizar el dominio del problema en unidades comprensibles llamadas conceptos o clases conceptuales?",
        "options": ["Modelo Conceptual", "Diagrama de Actividades", "Modelo de Casos de Uso", "Diagrama de Casos de Uso del Negocio"]
    },
    "15": {
        "question": "¿Cuáles de las siguientes opciones corresponden a características de las preguntas cerradas y representan desventajas de las preguntas abiertas?",
        "options": ["Aseguran una mejor utilizacion del tiempo permitiendo entrevistas mas cortas y Facilita mantener el control durante la entrevista", "Permiten mayor espontaneidad y libertad de expresión", "Hacen que el entrevistado encuentre el proceso más interesante", "Permiten descubrir vías de cuestionamiento adicionales"]
    },
    "16": {
        "question": "¿Cuáles son las características fundamentales que describen el enfoque de las metodologías Orientadas a Objetos?",
        "options": ["Se ven a los sistemas como un conjunto de objetos que colaboran entre si y Los objetos se analizan desde lo particular a lo general", "Las propiedades del objeto se representan en sus métodos", "Cualquiera de las clases abstractas se puede instanciar directamente", "Los objetos se analizan siempre desde lo general a lo particular (Top-down)"]
    },
    "17": {
        "question": "En la metodología XP (Programación Extrema), ¿cuál de las siguientes combinaciones pertenece a sus prácticas o principios operativos?",
        "options": ["El cliente en el sitio, Programacion en parejas, Estandar de codificacion y Diseño simple", "Comunicación, simpleza, retroalimentación, valentía y respeto", "Dueño del producto, retrospectiva, reunión diaria y demo", "Codificación simple, programación individual y documentación rígida"]
    },
    "18": {
        "question": "¿Qué atributo se cumple en una Especificación de Requisitos de Software (ERS) si todo requisito que figura en ella refleja una necesidad real?",
        "options": ["Correcta", "No ambigua", "Completa", "Priorizada (o clasificada)"]
    },
    "19": {
        "question": "¿Cuáles son las cuatro actividades básicas de desarrollo de software definidas en Programación Extrema (XP)?",
        "options": ["Codificar, probar, escuchar y diseñar", "Comunicación, simpleza, valentía y respeto", "Planificación, demo, retrospectiva y reunión diaria", "Diseño de datos, pruebas unitarias, compilación y despliegue"]
    },
    "20": {
        "question": "En el análisis del Proceso Unificado (y utilizando UML), ¿cuál es la regla de diseño respecto a las clases de interfaz (boundary)?",
        "options": ["Cada clase de interfaz deberia asociarse con al menos un actor, y viceversa", "Una clase entidad no puede aparecer en varias realizaciones de Caso de Uso", "Se debe identificar solo una clase Control por cada escenario del Caso de Uso", "Se debe identificar solo una clase de Control por cada actor registrado"]
    }
}

q_start_pat = re.compile(r'^(\d+(?:\.\d+)?)\s*\.\s+(.*)$', re.DOTALL)
ans_pat = re.compile(r'(?:la\s+respuesta\s+correcta\s+es|las\s+respuestas\s+correctas\s+son|las\s+afirmaciones\s+correctas\s+son|la\s+afirmación\s+correcta\s+es|el\s+orden\s+correcto\s+es|las\s+propiedades\s+o\s+características\s+fundamentales\s+que\s+tiene\s+un\s+"objeto"\s+son|la\s+respuesta\s+correcta\s+\(la\s+afirmación\s+falsa\s+\)\s+es)\s*(.*)', re.IGNORECASE | re.DOTALL)

parsed_questions = []

for block in blocks:
    m = q_start_pat.match(block.strip())
    if not m:
        continue
        
    q_id = m.group(1)
    content = m.group(2).strip()
    
    ans_match = ans_pat.search(content)
    
    correct_ans = ""
    explanation = ""
    
    if ans_match:
        correct_ans = ans_match.group(1).strip()
        split_match = re.search(r'\.\s+\b(De\s+acuerdo|En\s+la|Según|Las\s+otras|Esta|Los|El|La|Para|Un|Al|Durante|Como|En|Si|O|Y|No|Con|De|Por|Para|Es|Enfoque:|Nivel:)\b', correct_ans, re.IGNORECASE)
        if split_match:
            explanation = correct_ans[split_match.start() + 1:].strip()
            correct_ans = correct_ans[:split_match.start()].strip()
        else:
            period_idx = correct_ans.find('.')
            if period_idx != -1 and period_idx < len(correct_ans) - 1:
                explanation = correct_ans[period_idx+1:].strip()
                correct_ans = correct_ans[:period_idx].strip()
    elif q_id.startswith("58") or q_id == "58":
        ans_match = re.search(r'Correcta:\s*(.*)', content, re.IGNORECASE)
        if ans_match:
            correct_ans = ans_match.group(1).strip()
            explanation = content.replace(ans_match.group(0), "").strip()
            
    if not correct_ans:
        continue
        
    correct_ans = re.sub(r'^\s*[:\-\s\.]+', '', correct_ans).strip()
    if correct_ans.endswith('.'):
        correct_ans = correct_ans[:-1].strip()
    correct_ans = re.sub(r'\s+', ' ', correct_ans)
    
    # Categorization
    category = "Conceptos Generales"
    expl_lower = explanation.lower()
    ans_lower = correct_ans.lower()
    
    if any(k in expl_lower or k in ans_lower for k in ["scrum", "retrospectiva", "sprint", "product owner", "backlog", "agilidad", "ágil", "moscow", "story", "historias de usuario", "user story", "gherkin", "dado-cuando-entonces"]):
        category = "Metodologías Ágiles (Scrum / HU)"
    elif any(k in expl_lower or k in ans_lower for k in ["viabilidad", "factibilidad", "económico", "operativa", "estudio de viabilidad", "toma la decisión"]):
        category = "Estudio de Viabilidad"
    elif any(k in expl_lower or k in ans_lower for k in ["entrevista", "cuestionario", "observación", "juegos de rol", "brainstorming", "lluvia de ideas", "relevamiento", "fuentes de datos"]):
        category = "Técnicas de Relevamiento"
    elif any(k in expl_lower or k in ans_lower for k in ["caso de uso", "cus", "cun", "actor", "worker", "diagrama", "extend", "include", "uml", "escenario"]):
        category = "Modelado de Casos de Uso (UML)"
    elif any(k in expl_lower or k in ans_lower for k in ["objeto", "clase", "estado", "comportamiento", "identidad", "encapsulamiento", "polimorfismo", "herencia", "oo", "atrib"]):
        category = "Orientación a Objetos (UML)"
    elif any(k in expl_lower or k in ans_lower for k in ["requerimiento", "requisito", "funcional", "no funcional", "ingeniería de requerimientos", "pieces", "5c", "negocio"]):
        category = "Ingeniería de Requerimientos"
    elif any(k in expl_lower or k in ans_lower for k in ["transaccional", "tps", "mis", "dss", "sistema de información", "operacional", "toma de decisiones"]):
        category = "Sistemas de Información"

    # Default Question and Options construction
    q_text = ""
    options = [correct_ans]
    
    # Apply manual curation if available
    if q_id in manual_questions:
        q_text = manual_questions[q_id]["question"]
        options = manual_questions[q_id]["options"]
    else:
        # Infer question from explanation or correct answer
        first_sentence = explanation.split('.')[0].strip()
        if len(first_sentence) > 30 and ("fuentes" in first_sentence or "acuerdo" in first_sentence or "metodología" in first_sentence or "según" in first_sentence):
            q_text = f"Según el apunte de ADS: {first_sentence}."
        else:
            q_text = f"En relación al tema de {category}: ¿Cuál es la opción correcta?"
            
        # Distractor generation
        if correct_ans.lower() in ["falso", "verdadero"] or (len(correct_ans) < 10 and "falso" in correct_ans.lower()) or (len(correct_ans) < 10 and "verdadero" in correct_ans.lower()):
            options = ["Verdadero", "Falso"]
        else:
            # Try to extract bullet points from explanation as distractors
            bullets = re.findall(r'●\s*(.*?)(?=\n|●|$)', explanation)
            extracted_distractors = []
            for b in bullets:
                b_cleaned = b.strip()
                if ":" in b_cleaned:
                    b_cleaned = b_cleaned.split(":")[0].strip()
                if "," in b_cleaned:
                    b_cleaned = b_cleaned.split(",")[0].strip()
                    
                b_cleaned = re.sub(r'^(No\s+es\s+un\s+|No\s+es\s+una\s+|No\s+es\s+|No\s+|Es\s+falso\s+)', '', b_cleaned, flags=re.IGNORECASE)
                b_cleaned = b_cleaned.strip()
                if b_cleaned:
                    b_cleaned = b_cleaned[0].upper() + b_cleaned[1:]
                    
                if b_cleaned and b_cleaned.lower() != correct_ans.lower() and len(b_cleaned) > 2 and b_cleaned not in extracted_distractors:
                    extracted_distractors.append(b_cleaned)
            
            if len(extracted_distractors) >= 1:
                options.extend(extracted_distractors[:3])
                
            if len(options) < 4:
                for key, dists in distractors_map.items():
                    if key in correct_ans.lower() and len(correct_ans) < 30:
                        for d in dists:
                            if d not in options:
                                options.append(d)
                                
            # Fallback adding from other questions in same category
            while len(options) < 4:
                fallback_added = False
                for other_q in parsed_questions:
                    if other_q["category"] == category and other_q["correct_answer"] not in options and len(other_q["correct_answer"]) < 80:
                        options.append(other_q["correct_answer"])
                        fallback_added = True
                        break
                if not fallback_added:
                    generic_dists = ["Opción alternativa de análisis", "Ninguna de las opciones anteriores es correcta", "Depende del contexto del proyecto y el cliente", "Es una consideración secundaria del analista"]
                    for gd in generic_dists:
                        if gd not in options:
                            options.append(gd)
                            break
                            
    options = [re.sub(r'\s+', ' ', opt).strip() for opt in options]
    options = [opt[:-1] if opt.endswith('.') else opt for opt in options]
    
    parsed_questions.append({
        "id": q_id,
        "category": category,
        "question": q_text,
        "correct_answer": correct_ans,
        "explanation": explanation,
        "options": list(set(options))
    })

# Save output questions.json
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(parsed_questions, f, ensure_ascii=False, indent=2)

print(f"Successfully processed and generated {len(parsed_questions)} questions in {output_file}")
