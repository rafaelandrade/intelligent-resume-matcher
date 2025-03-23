import pytest
from unittest.mock import patch, MagicMock, mock_open
from fastapi import UploadFile
import io
from src.services.resume_matcher_service import is_resume_content
from src.exceptions.NotResume import NotResume


ENGLISH_RESUME = """
John Doe
Email: john.doe@example.com
Phone: (123) 456-7890

SUMMARY
Experienced software engineer with 5+ years in web development and cloud technologies.

EXPERIENCE
Senior Software Engineer
ABC Tech, San Francisco, CA
January 2019 - Present
- Developed and maintained RESTful APIs using Python and FastAPI
- Implemented CI/CD pipelines with GitHub Actions

Software Developer
XYZ Solutions, Seattle, WA
March 2016 - December 2018
- Built responsive web applications using React and Node.js

EDUCATION
Bachelor of Science in Computer Science
University of Washington, Seattle
Graduated: May 2016

SKILLS
- Python, JavaScript, Java
- FastAPI, React, Node.js
- AWS, Docker, Kubernetes
"""

# Sample resume content in Portuguese
PORTUGUESE_RESUME = """
João Silva
Email: joao.silva@exemplo.com
Telefone: (11) 98765-4321

RESUMO
Engenheiro de software experiente com mais de 5 anos em desenvolvimento web e tecnologias cloud.

EXPERIÊNCIA PROFISSIONAL
Engenheiro de Software Sênior
ABC Tecnologia, São Paulo, SP
Janeiro 2019 - Presente
- Desenvolvimento e manutenção de APIs RESTful usando Python e FastAPI
- Implementação de pipelines de CI/CD com GitHub Actions

Desenvolvedor de Software
XYZ Soluções, Rio de Janeiro, RJ
Março 2016 - Dezembro 2018
- Construção de aplicações web responsivas usando React e Node.js

FORMAÇÃO ACADÊMICA
Bacharelado em Ciência da Computação
Universidade de São Paulo, São Paulo
Concluído: Maio 2016

HABILIDADES
- Python, JavaScript, Java
- FastAPI, React, Node.js
- AWS, Docker, Kubernetes
"""

# Non-resume content (random text)
NON_RESUME_TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud 
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute 
irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat 
nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa 
qui officia deserunt mollit anim id est laborum.
"""

SHORT_TEXT = "This is a very short text that doesn't have enough content."


def create_mock_file(content: str):
    content_bytes = content.encode('utf-8')
    file = io.BytesIO(content_bytes)
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = file
    mock_file.filename = "test.pdf"
    return mock_file


@pytest.mark.asyncio
class TestResumeMatcherService:
    
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_valid_english_resume(self, mock_pdf_reader):
        mock_pdf_reader.return_value = ENGLISH_RESUME
        mock_file = create_mock_file(ENGLISH_RESUME)

        result = await is_resume_content(mock_file, "en-US")
        
        assert result is True
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
        
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_valid_portuguese_resume(self, mock_pdf_reader):        
        mock_pdf_reader.return_value = PORTUGUESE_RESUME
        mock_file = create_mock_file(PORTUGUESE_RESUME)
        
        result = await is_resume_content(mock_file, "pt-BR")
        
        assert result is True
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
        
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_non_resume_content(self, mock_pdf_reader):
        mock_pdf_reader.return_value = NON_RESUME_TEXT
        mock_file = create_mock_file(NON_RESUME_TEXT)
        
        with pytest.raises(NotResume) as exc_info:
            await is_resume_content(mock_file, "en-US")
        
        assert "Document lacks resume characteristics" in str(exc_info.value)
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
            
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_non_resume_content_portuguese(self, mock_pdf_reader):
        mock_pdf_reader.return_value = NON_RESUME_TEXT
        mock_file = create_mock_file(NON_RESUME_TEXT)
        
        with pytest.raises(NotResume) as exc_info:
            await is_resume_content(mock_file, "pt-BR")
        
        assert "não possui características de um currículo" in str(exc_info.value)
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
        
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_empty_content(self, mock_pdf_reader):
        mock_pdf_reader.return_value = ""
        mock_file = create_mock_file("")
        
        with pytest.raises(NotResume) as exc_info:
            await is_resume_content(mock_file, "en-US")
        
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
    
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_short_content(self, mock_pdf_reader):
        # Arrange
        mock_pdf_reader.return_value = SHORT_TEXT
        mock_file = create_mock_file(SHORT_TEXT)
        
        with pytest.raises(NotResume) as exc_info:
            await is_resume_content(mock_file, "en-US")
        
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
    
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_pdf_reader_exception(self, mock_pdf_reader):
        # Arrange
        mock_pdf_reader.side_effect = NotResume("Failed to read PDF")
        mock_file = create_mock_file("dummy content")
        
        # Act & Assert  
        with pytest.raises(NotResume):
            await is_resume_content(mock_file, "en-US")
        
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
        
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_english_resume_with_minimum_score(self, mock_pdf_reader):
        # Create a resume with just enough elements to pass
        minimal_resume = """
        John Doe
        john.doe@example.com
        Phone: 123-456-7890
        
        EDUCATION
        University of Example, 2015-2019
        
        EXPERIENCE
        Company XYZ, Jan 2020 - Present
        """
        
        mock_pdf_reader.return_value = minimal_resume
        mock_file = create_mock_file(minimal_resume)
        
        # Act
        result = await is_resume_content(mock_file, "en-US")
        
        # Assert
        assert result is True
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
    
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_portuguese_resume_with_minimum_score(self, mock_pdf_reader):
        # Create a resume with just enough elements to pass
        minimal_resume = """
        João Silva
        joao.silva@exemplo.com
        Telefone: (11) 98765-4321
        
        EDUCAÇÃO
        Universidade de Exemplo, 2015-2019
        
        EXPERIÊNCIA
        Empresa XYZ, Jan 2020 - Presente
        """
        
        mock_pdf_reader.return_value = minimal_resume
        mock_file = create_mock_file(minimal_resume)   
             
        # Act
        result = await is_resume_content(mock_file, "pt-BR")
        
        # Assert
        assert result is True
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
    
    @patch('src.services.resume_matcher_service.pdf_reader')
    async def test_almost_resume_but_not_quite(self, mock_pdf_reader):
        # Create a document that has some resume elements but not enough to pass
        almost_resume = """
        John Doe
        
        Some random text that mentions education and experience
        without proper formatting or contact information.
        """
        
        mock_pdf_reader.return_value = almost_resume
        mock_file = create_mock_file(almost_resume)
        
        # Act & Assert
        with pytest.raises(NotResume) as exc_info:
            await is_resume_content(mock_file, "en-US")
        
        mock_pdf_reader.assert_called_once_with(pdf_file=mock_file)
