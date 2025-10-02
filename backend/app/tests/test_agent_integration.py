import pytest
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from app.processing.models import Task
from app.projects.models import Project
from unittest.mock import patch, MagicMock
import io
User = get_user_model()
class AgentIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    @patch('app.processing.views.analyze_document_with_legal_llm')
    def test_analyze_document_endpoint(self, mock_task):
        pdf_content = b'%PDF-1.4 fake pdf content'
        pdf_file = io.BytesIO(pdf_content)
        pdf_file.name = 'test_contract.pdf'
        response = self.client.post(
            '/api/v1/agents/analyze-document/',
            {'file': pdf_file},
            format='multipart'
        )
        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['status'] == 'queued'
        task_id = response.data['id']
        task = Task.objects.get(id=task_id)
        assert task.status == Task.Status.QUEUED
        assert 'document:' in task.url
        mock_task.delay.assert_called_once()
    @patch('app.processing.views.analyze_website_with_browser_agent')
    def test_analyze_website_endpoint(self, mock_task):
        response = self.client.post(
            '/api/v1/agents/analyze-website/',
            {'url': 'https://example.com'},
            format='json'
        )
        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['status'] == 'queued'
        task_id = response.data['id']
        task = Task.objects.get(id=task_id)
        assert task.status == Task.Status.QUEUED
        assert task.url == 'https://example.com'
        mock_task.delay.assert_called_once()
    def test_analyze_document_with_project(self):
        project = Project.objects.create(
            name='Test Project',
            site_url='https://example.com',
            owner=self.user
        )
        with patch('PyPDF2.PdfReader') as mock_pdf_reader, \
             patch('app.processing.views.analyze_document_with_legal_llm'):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test contract"
            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]
            mock_pdf_reader.return_value = mock_pdf
            pdf_file = io.BytesIO(b'%PDF-1.4 test')
            pdf_file.name = 'test.pdf'
            response = self.client.post(
                '/api/v1/agents/analyze-document/',
                {
                    'file': pdf_file,
                    'project_id': str(project.id)
                },
                format='multipart'
            )
            assert response.status_code == 201
            task = Task.objects.get(id=response.data['id'])
            assert task.project_id == project.id
    def test_analyze_website_invalid_url(self):
        response = self.client.post(
            '/api/v1/agents/analyze-website/',
            {},
            format='json'
        )
        assert response.status_code == 400
        assert 'url' in str(response.data).lower()
@pytest.mark.django_db
class AgentTaskTest(TestCase):
    @patch('app.agents.legal_llm.analyze_contract')
    @patch('app.agents.document_extractor.extract_text_from_file')
    def test_document_analysis_task_success(self, mock_extract, mock_analyze):
        from app.processing.tasks import analyze_document_with_legal_llm
        task = Task.objects.create(
            url='document:test.pdf',
            status=Task.Status.QUEUED
        )
        mock_extract.return_value = "Test contract text"
        mock_result = MagicMock()
        mock_result.contract_id = str(task.id)
        mock_result.analysis_date = '2024-01-01T00:00:00'
        mock_result.overall_compliance_score = 0.85
        mock_result.summary = 'Test summary'
        mock_result.critical_issues = ['Issue 1']
        mock_result.recommendations = ['Fix issue 1']
        mock_result.__annotations__ = {}
        mock_analyze.return_value = mock_result
        file_content = b'fake pdf content'
        analyze_document_with_legal_llm(str(task.id), file_content, 'test.pdf')
        task.refresh_from_db()
        assert task.status == Task.Status.DONE
        assert task.result_json is not None
        assert task.result_json['overall_compliance_score'] == 0.85
        assert mock_extract.called
        assert mock_analyze.called
    def test_document_analysis_task_failure(self):
        from app.processing.tasks import analyze_document_with_legal_llm
        task = Task.objects.create(
            url='document:test.pdf',
            status=Task.Status.QUEUED
        )
        with patch('app.agents.document_extractor.extract_text_from_file') as mock_extract:
            mock_extract.side_effect = ValueError('Extraction failed')
            with pytest.raises(ValueError):
                analyze_document_with_legal_llm(str(task.id), b'fake content', 'test.pdf')
            task.refresh_from_db()
            assert task.status == Task.Status.FAILED
            assert 'Extraction failed' in task.error
    def test_website_analysis_task(self):
        from app.processing.tasks import analyze_website_with_browser_agent
        from unittest.mock import patch
        task = Task.objects.create(
            url='https://example.com',
            status=Task.Status.QUEUED
        )
        with patch('app.agents.dynamic_agent.analyze_website') as mock_analyze:
            mock_analyze.return_value = {
                'url': 'https://example.com',
                'transparency_score': 85.0,
                'dark_patterns': ['Pattern 1', 'Pattern 2'],
                'summary': 'Analysis completed successfully',
                'status': 'completed'
            }
            analyze_website_with_browser_agent(str(task.id), 'https://example.com')
            task.refresh_from_db()
            assert task.status == Task.Status.DONE
            assert task.result_json is not None
            assert task.result_json['url'] == 'https://example.com'
            assert task.result_json['transparency_score'] == 85.0
            assert mock_analyze.called
            analyze_website_with_browser_agent(str(task.id), 'https://example.com')
            task.refresh_from_db()
            assert task.status == Task.Status.DONE
            assert task.result_json is not None
            assert task.result_json['url'] == 'https://example.com'
            assert task.result_json['transparency_score'] == 85.0
            assert mock_analyze.called
