"""
Demo Service - 简单 Flask API
用于演示 GitHub Actions + 阿里云 ACR + ECS 部署流程
"""
from flask import Flask, jsonify
import os
import datetime

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        'message': 'Hello from Demo Service!',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'environment': os.getenv('ENVIRONMENT', 'production')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/info')
def info():
    return jsonify({
        'service': 'demo-service',
        'version': '1.0.0',
        'author': '皇阿玛',
        'deploy_time': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
