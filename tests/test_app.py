"""
Demo Service 单元测试
"""
import pytest
import json
from src.app import app

@pytest.fixture
def client():
    """测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestHelloRoute:
    """测试根路由 /"""
    
    def test_hello_returns_json(self, client):
        """验证返回 JSON 格式"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
    
    def test_hello_has_message(self, client):
        """验证返回消息字段"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Hello' in data['message']
    
    def test_hello_has_timestamp(self, client):
        """验证返回时间戳"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'timestamp' in data
    
    def test_hello_has_version(self, client):
        """验证返回版本号"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'version' in data
        assert data['version'] in ['1.0.0', 'dev', 'test']
    
    def test_hello_has_environment(self, client):
        """验证返回环境信息"""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'environment' in data

class TestHealthRoute:
    """测试健康检查 /health"""
    
    def test_health_returns_200(self, client):
        """验证健康检查返回 200"""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_returns_json(self, client):
        """验证返回 JSON 格式"""
        response = client.get('/health')
        assert response.content_type == 'application/json'
    
    def test_health_status_healthy(self, client):
        """验证状态为 healthy"""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

class TestApiInfoRoute:
    """测试 API 信息 /api/info"""
    
    def test_info_returns_200(self, client):
        """验证返回 200"""
        response = client.get('/api/info')
        assert response.status_code == 200
    
    def test_info_returns_json(self, client):
        """验证返回 JSON 格式"""
        response = client.get('/api/info')
        assert response.content_type == 'application/json'
    
    def test_info_has_service_name(self, client):
        """验证服务名称"""
        response = client.get('/api/info')
        data = json.loads(response.data)
        assert data['service'] == 'demo-service'
    
    def test_info_has_version(self, client):
        """验证版本号"""
        response = client.get('/api/info')
        data = json.loads(response.data)
        assert 'version' in data
    
    def test_info_has_author(self, client):
        """验证作者信息"""
        response = client.get('/api/info')
        data = json.loads(response.data)
        assert 'author' in data
    
    def test_info_has_deploy_time(self, client):
        """验证部署时间"""
        response = client.get('/api/info')
        data = json.loads(response.data)
        assert 'deploy_time' in data

class TestNotFoundRoute:
    """测试 404 处理"""
    
    def test_not_found_returns_404(self, client):
        """验证不存在的路由返回 404"""
        response = client.get('/nonexistent')
        assert response.status_code == 404

if __name__ == '__main__':
    pytest.main(['-v', __file__])
