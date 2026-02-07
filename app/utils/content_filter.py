"""
Filtro de contenido para mensajes de chat.

Implementa funcionalidad de moderación automática para detectar
y filtrar contenido inapropiado en los mensajes.
"""

import re
import os
from typing import List, Set


class ContentFilter:
    """
    Filtro de contenido para detectar palabras inapropiadas.
    
    Proporciona funcionalidad para:
    - Detectar contenido inapropiado
    - Obtener lista de palabras problemáticas
    - Cargar diccionarios personalizados
    """
    
    # Palabras inapropiadas por defecto (básicas para testing)
    DEFAULT_INAPPROPRIATE_WORDS = {
        "spam", "malware", "virus", "fraude", "fraudulento",
        "ofensivo", "malicioso", "phishing", "scam"
    }
    
    def __init__(self, custom_words: List[str] = None):
        """
        Inicializar filtro de contenido.
        
        Args:
            custom_words: Lista personalizada de palabras inapropiadas.
                         Si no se proporciona, usa las palabras por defecto.
        """
        if custom_words is not None:
            self.inappropriate_words = set(word.lower() for word in custom_words)
        else:
            self.inappropriate_words = self.DEFAULT_INAPPROPRIATE_WORDS.copy()
    
    def is_appropriate(self, content: str) -> bool:
        """
        Verificar si el contenido es apropiado.
        
        Args:
            content: Texto a verificar
            
        Returns:
            True si el contenido es apropiado, False en caso contrario
        """
        if not content or not content.strip():
            return True  # Contenido vacío se considera apropiado
        
        inappropriate_words = self.get_inappropriate_words(content)
        return len(inappropriate_words) == 0
    
    def get_inappropriate_words(self, content: str) -> List[str]:
        """
        Obtener lista de palabras inapropiadas encontradas en el contenido.
        
        Args:
            content: Texto a analizar
            
        Returns:
            Lista de palabras inapropiadas encontradas
        """
        if not content or not content.strip():
            return []
        
        content_lower = content.lower()
        found_words = []
        
        for word in self.inappropriate_words:
            # Usar word boundaries para evitar coincidencias parciales
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content_lower):
                found_words.append(word)
        
        return found_words
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'ContentFilter':
        """
        Cargar filtro desde archivo de texto.
        
        Args:
            file_path: Ruta al archivo con palabras inapropiadas (una por línea)
            
        Returns:
            Instancia de ContentFilter con palabras del archivo
            
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo de filtro no encontrado: {file_path}")
        
        words = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:  # Ignorar líneas vacías
                    words.append(word)
        
        return cls(custom_words=words)
    
    def add_word(self, word: str) -> None:
        """
        Agregar palabra al filtro dinámicamente.
        
        Args:
            word: Palabra a agregar al filtro
        """
        self.inappropriate_words.add(word.lower())
    
    def remove_word(self, word: str) -> bool:
        """
        Remover palabra del filtro.
        
        Args:
            word: Palabra a remover
            
        Returns:
            True si la palabra fue removida, False si no estaba presente
        """
        word_lower = word.lower()
        if word_lower in self.inappropriate_words:
            self.inappropriate_words.remove(word_lower)
            return True
        return False
    
    def get_word_count(self) -> int:
        """
        Obtener número de palabras en el filtro.
        
        Returns:
            Cantidad de palabras inapropiadas configuradas
        """
        return len(self.inappropriate_words)
    
    def clear(self) -> None:
        """Limpiar todas las palabras del filtro."""
        self.inappropriate_words.clear()
    
    def __repr__(self) -> str:
        """Representación string del filtro."""
        return f"ContentFilter(words={self.get_word_count()})"