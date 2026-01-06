"""
Flask Web应用
提供任务管理的Web界面
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from task_manager import TaskManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 生产环境应该使用环境变量

# 初始化任务管理器
task_manager = TaskManager()


@app.route('/')
def index():
    """主页 - 显示所有任务"""
    try:
        tasks = task_manager.get_tasks_with_countdown()
        return render_template('index.html', tasks=tasks)
    except Exception as e:
        return render_template('index.html', tasks=[], error=str(e))


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """API: 获取所有任务"""
    try:
        tasks = task_manager.get_tasks_with_countdown()
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tasks', methods=['POST'])
def add_task():
    """API: 添加新任务"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data or 'title' not in data or 'deadline' not in data:
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400

        title = data['title'].strip()
        description = data.get('description', '').strip()
        deadline = data['deadline'].strip()

        if not title:
            return jsonify({'success': False, 'error': '任务标题不能为空'}), 400

        if not deadline:
            return jsonify({'success': False, 'error': '截止日期不能为空'}), 400

        # 添加任务
        task_id = task_manager.add_task(title, description, deadline)

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务添加成功'
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """API: 删除任务"""
    try:
        success = task_manager.delete_task(task_id)

        if success:
            return jsonify({'success': True, 'message': '任务删除成功'})
        else:
            return jsonify({'success': False, 'error': '任务不存在'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tasks/<task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """API: 切换任务完成状态"""
    try:
        success = task_manager.toggle_task_completion(task_id)

        if success:
            return jsonify({'success': True, 'message': '任务状态更新成功'})
        else:
            return jsonify({'success': False, 'error': '任务不存在'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API: 获取任务统计信息"""
    try:
        all_tasks = task_manager.get_all_tasks()
        pending_tasks = [t for t in all_tasks if not t['completed']]
        completed_tasks = [t for t in all_tasks if t['completed']]

        # 统计紧急任务（3天内到期或已超期）
        urgent_count = 0
        for task in pending_tasks:
            countdown = task_manager.calculate_remaining_days(task['deadline'])
            if countdown['status'] in ['urgent', 'overdue']:
                urgent_count += 1

        return jsonify({
            'success': True,
            'stats': {
                'total': len(all_tasks),
                'pending': len(pending_tasks),
                'completed': len(completed_tasks),
                'urgent': urgent_count
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/send-email', methods=['POST'])
def send_email_reminder():
    """API: 发送邮件提醒（供外部定时服务调用）"""
    try:
        # 简单的安全验证（使用API密钥）
        api_key = request.headers.get('X-API-Key')
        expected_key = os.environ.get('API_KEY', 'task-reminder-secret-key')

        if api_key != expected_key:
            return jsonify({'success': False, 'error': '未授权'}), 401

        # 导入邮件发送模块
        from email_sender import EmailSender

        # 获取所有未完成的任务
        tasks_with_countdown = task_manager.get_tasks_with_countdown()
        pending_tasks = [t for t in tasks_with_countdown if not t['completed']]

        if not pending_tasks:
            return jsonify({
                'success': True,
                'message': '没有未完成的任务',
                'sent': False
            })

        # 发送邮件
        try:
            email_sender = EmailSender()
            success = email_sender.send_reminder_email(pending_tasks)

            if success:
                return jsonify({
                    'success': True,
                    'message': f'已发送 {len(pending_tasks)} 个任务的提醒邮件',
                    'sent': True
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '邮件发送失败'
                }), 500
        except Exception as e:
            # 记录详细的邮件发送错误
            import traceback
            error_details = f"{str(e)}\n{traceback.format_exc()}"
            print(f"邮件发送错误: {error_details}")
            return jsonify({
                'success': False,
                'error': f'邮件发送失败: {str(e)}'
            }), 500

    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        print(f"API错误: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('index.html', tasks=[], error="页面不存在"), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('index.html', tasks=[], error="服务器内部错误"), 500


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 任务提醒系统 Web 服务器")
    print("=" * 50)

    # 从环境变量获取端口，兼容云平台
    port = int(os.environ.get('PORT', 5000))

    print(f"📱 访问地址: http://127.0.0.1:{port}")
    print("📝 按 Ctrl+C 停止服务器")
    print("=" * 50)
    print()

    # 启动Flask服务器
    # 生产环境不要使用 debug=True
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
