#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/8/9 02:40
@Author  : claudexie
@File    : api_demo.py
@Software: PyCharm
"""

from flask import Flask, jsonify, request
import os
import json

app = Flask(__name__)

def create_api_service(file_path, port=5000):
    """
    部署一个简单的API服务，读取指定文本文件的内容

    :param file_path: 文本文件的路径
    :param port: API服务的端口号，默认为5000
    """

    @app.route('/get_content', methods=['GET'])
    def get_file_content():
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # 尝试解析JSON内容
            try:
                json_content = json.loads(content)
            except json.JSONDecodeError:
                return jsonify({"error": "File content is not valid JSON"}), 400

            return jsonify({"content": json_content})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/clear_content', methods=['POST'])
    def clear_file_content():
        try:
            # 清空文件内容
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("")

            return jsonify({"message": "File content cleared successfully"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/write_content', methods=['POST'])
    def write_file_content():
        try:
            # 获取请求中的数据
            data = request.get_json()
            if 'content' not in data:
                return jsonify({"error": "No content provided"}), 400

            content = data['content']

            # 写入文件内容
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            return jsonify({"message": "File content written successfully"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # 启动Flask应用
    app.run(host='0.0.0.0', port=port)

# 使用示例
if __name__ == "__main__":
    file_path = "/home/lighthouse/chatgpt-on-wechat/trigger_ai_video_time.txt"  # 替换为你的文本文件路径
    create_api_service(file_path)
