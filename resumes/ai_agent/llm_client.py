"""
LLM Client for interfacing with local language models.
Supports Ollama and provides a mock fallback for testing.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for communicating with local LLM (Ollama).
    Falls back to mock responses if Ollama is not available.
    """
    
    def __init__(self, model_name='llama2', use_mock=False):
        """
        Initialize LLM client.
        
        Args:
            model_name: Name of the Ollama model to use
            use_mock: If True, use mock responses instead of real LLM
        """
        self.model_name = model_name
        self.use_mock = use_mock or os.getenv('USE_MOCK_LLM', 'true').lower() == 'true'
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    
    def generate(self, prompt, system_prompt=None, temperature=0.7):
        """
        Generate response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            str: Generated text response
        """
        if self.use_mock:
            return self._mock_generate(prompt, system_prompt)
        
        try:
            return self._ollama_generate(prompt, system_prompt, temperature)
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}. Falling back to mock.")
            return self._mock_generate(prompt, system_prompt)
    
    def _ollama_generate(self, prompt, system_prompt, temperature):
        """
        Generate response using Ollama API.
        
        Note: Requires 'requests' library and running Ollama instance.
        Install: pip install requests
        Start Ollama: ollama serve
        Pull model: ollama pull llama2
        """
        try:
            import requests
            
            url = f"{self.ollama_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except ImportError:
            raise Exception("requests library not installed. Install with: pip install requests")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _mock_generate(self, prompt, system_prompt):
        """
        Generate mock response for testing without LLM.
        
        This method analyzes the prompt to provide realistic mock responses.
        """
        prompt_lower = prompt.lower()
        
        # Mock ATS analysis
        if 'ats' in prompt_lower or 'score' in prompt_lower:
            return json.dumps({
                "score": 75,
                "missing_skills": "Cloud Computing (AWS/Azure), Docker, Kubernetes",
                "suggestions": "Add more quantifiable achievements, Include relevant certifications, Optimize keyword density for ATS systems"
            })
        
        # Mock resume generation
        if 'resume' in prompt_lower or 'generate' in prompt_lower:
            return """
# PROFESSIONAL SUMMARY
Results-driven professional with strong technical skills and proven ability to deliver high-quality solutions. Passionate about leveraging technology to solve complex problems and drive innovation.

# SKILLS
- Programming Languages: Python, JavaScript, Java
- Web Technologies: Django, React, Node.js
- Database: PostgreSQL, MySQL, MongoDB
- Tools: Git, Docker, AWS
- Soft Skills: Problem-solving, Team collaboration, Communication

# EDUCATION
Bachelor of Technology in Computer Science
XYZ University | 2020 - 2024
- GPA: 8.5/10
- Relevant Coursework: Data Structures, Algorithms, Web Development, Database Management

# PROJECTS
**E-Commerce Platform** | Django, React, PostgreSQL
- Developed full-stack e-commerce application with user authentication and payment integration
- Implemented RESTful APIs serving 1000+ daily active users
- Optimized database queries resulting in 40% faster page load times

**Task Management System** | Python, Flask, SQLite
- Built web-based task management application with real-time updates
- Designed intuitive UI/UX for seamless user experience
- Integrated email notifications for task reminders

# EXPERIENCE
**Software Development Intern** | ABC Tech Solutions
June 2023 - August 2023
- Collaborated with senior developers on enterprise web applications
- Wrote clean, maintainable code following best practices
- Participated in code reviews and agile development processes
- Contributed to improving application performance by 25%
"""
        
        # Default mock response
        return "This is a mock AI response. Configure Ollama for real AI capabilities."


# Global LLM client instance
llm_client = LLMClient()


def get_llm_client():
    """
    Get the global LLM client instance.
    
    Returns:
        LLMClient: Configured LLM client
    """
    return llm_client
