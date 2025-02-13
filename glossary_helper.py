import win32com.client as win32
import os
import pythoncom  # Import pythoncom to handle COM initialization

global glossary
def load_glossary(filename):
    pythoncom.CoInitialize()
    word = win32.gencache.EnsureDispatch('Word.Application')
    doc = word.Documents.Open(filename)
    glossary_data = []

    current_topic = None
    definitions = []

    for paragraph in doc.Paragraphs:
        text = paragraph.Range.Text.strip()
        style = paragraph.Range.Style.NameLocal

        # Detect titles by Heading 1
        if style == "Heading 1":
            if current_topic:
                # Append the previous entry to glossary_data
                glossary_data.append({
                    "title": current_topic,
                    "definitions": definitions
                })
            current_topic = text
            definitions = []
        else:
            # Treat as definition text under the current title
            definitions.append(text)

    # Append the last entry
    if current_topic:
        glossary_data.append({
            "title": current_topic,
            "definitions": definitions
        })

    doc.Close(False)
    word.Quit()
    pythoncom.CoUninitialize()
    return glossary_data

def group_by_letter(glossary):
    grouped_glossary = {}
    for letter, entries in glossary.items():
        grouped_glossary[letter] = sorted(entries, key=lambda item: item[0])
    return grouped_glossary

def create_links(glossary):
    linked_glossary = {}
    sorted_terms = [term for term in sorted(glossary.keys(), key=len, reverse=True) if len(term) > 1]

    for letter, entries in glossary.items():
        linked_glossary[letter] = []
        for topic, definitions in entries:
            definition_text = "\n".join(definitions)
            for other_topic in sorted_terms:
                if other_topic != topic:
                    pattern = rf"\b{re.escape(other_topic)}\b"
                    replacement = f"<a href='#{other_topic.replace(' ', '-').lower()}'>{other_topic}</a>"
                    definition_text = re.sub(pattern, replacement, definition_text)
            linked_glossary[letter].append((topic, definition_text.split("\n")))

    return linked_glossary

def update_glossary_document(filename, title, definition, additional_html):
    pythoncom.CoInitialize()
    try:
        word = win32.gencache.EnsureDispatch('Word.Application')
        doc = word.Documents.Open(os.path.abspath(filename))

        # Add the title with Heading 1 style
        doc.Content.InsertAfter(f"{title}\n")
        last_paragraph = doc.Paragraphs.Last
        last_paragraph.Range.Style = "Heading 1"

        # Add the definition with Normal style
        doc.Content.InsertAfter(f"{definition}\n")
        definition_paragraph = doc.Paragraphs.Last
        definition_paragraph.Range.Style = "Normal" 

        # Add definition and additional HTML as normal paragraphs
        doc.Content.InsertAfter(f"{definition}\n")
        if additional_html:
            doc.Content.InsertAfter(f"{additional_html}\n")
        
        # Save and close
        doc.Save()
        doc.Close()
        word.Quit()
    finally:
        pythoncom.CoUninitialize()
