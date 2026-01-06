"""
邮件发送模块
负责发送任务提醒邮件
支持环境变量和配置文件两种方式
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from pathlib import Path
import json
import os


class EmailSender:
    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self):
        """加载邮件配置，优先使用环境变量"""
        # 优先从环境变量读取（用于生产环境如 Render）
        if os.environ.get('EMAIL_SMTP_SERVER'):
            return {
                'smtp_server': os.environ.get('EMAIL_SMTP_SERVER'),
                'smtp_port': int(os.environ.get('EMAIL_SMTP_PORT', '587')),
                'sender_email': os.environ.get('EMAIL_SENDER'),
                'sender_password': os.environ.get('EMAIL_PASSWORD'),
                'recipient_email': os.environ.get('EMAIL_RECIPIENT')
            }

        # 如果没有环境变量，从配置文件读取（用于本地开发）
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"配置文件 {self.config_file} 不存在，请先创建配置文件\n"
                f"配置文件格式示例：\n"
                '{\n'
                '  "email": {\n'
                '    "smtp_server": "smtp.gmail.com",\n'
                '    "smtp_port": 587,\n'
                '    "sender_email": "your_email@gmail.com",\n'
                '    "sender_password": "your_app_password",\n'
                '    "recipient_email": "your_email@gmail.com"\n'
                '  }\n'
                '}'
            )

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if 'email' not in config:
            raise ValueError("配置文件中缺少 'email' 配置项")

        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'recipient_email']
        for field in required_fields:
            if field not in config['email']:
                raise ValueError(f"配置文件中缺少必需的邮件配置: {field}")

        return config['email']

    def send_reminder_email(self, tasks):
        """
        发送任务提醒邮件

        Args:
            tasks: 任务列表（已包含倒计时信息）

        Returns:
            bool: 发送成功返回True，失败返回False
        """
        if not tasks:
            print("没有未完成的任务，不需要发送邮件")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(f'📋 任务提醒 - 你有{len(tasks)}个未完成任务', 'utf-8')
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['recipient_email']

            # 生成邮件内容
            html_content = self._generate_email_html(tasks)
            text_content = self._generate_email_text(tasks)

            # 添加邮件正文
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # 发送邮件
            # 根据端口选择连接方式
            if self.config['smtp_port'] == 465:
                # 使用SSL
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'])
            else:
                # 使用STARTTLS
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
                server.starttls()

            server.login(self.config['sender_email'], self.config['sender_password'])
            server.send_message(msg)
            server.quit()

            print(f"[成功] 邮件发送成功！收件人: {self.config['recipient_email']}")
            return True

        except Exception as e:
            print(f"邮件发送失败: {str(e)}")
            return False

    def _generate_email_html(self, tasks):
        """生成HTML格式的邮件内容"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .task-list { margin-top: 20px; }
        .task-item { background: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
        .task-item.urgent { border-left-color: #ff6b6b; background: #fff5f5; }
        .task-item.overdue { border-left-color: #dc3545; background: #ffebeb; }
        .task-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
        .task-desc { color: #666; font-size: 14px; margin: 5px 0; }
        .countdown { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; margin-top: 8px; }
        .countdown.normal { background: #d4edda; color: #155724; }
        .countdown.urgent { background: #fff3cd; color: #856404; }
        .countdown.overdue { background: #f8d7da; color: #721c24; }
        .footer { margin-top: 30px; text-align: center; color: #999; font-size: 12px; }
        .stats { background: #e7f3ff; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 任务提醒</h1>
            <p>今日待办任务清单</p>
        </div>

        <div class="stats">
            <strong>你有 {task_count} 个未完成任务</strong>
        </div>

        <div class="task-list">
        """.format(task_count=len(tasks))

        for task in tasks:
            countdown = task.get('countdown', {})
            status_class = countdown.get('status', 'normal')
            countdown_text = countdown.get('text', '未知')

            html += """
            <div class="task-item {status_class}">
                <div class="task-title">{title}</div>
                <div class="task-desc">{desc}</div>
                <div class="countdown {status_class}">{countdown_text}</div>
                <div style="font-size: 12px; color: #999; margin-top: 5px;">截止日期: {deadline}</div>
            </div>
            """.format(
                status_class=status_class,
                title=task.get('title', '无标题'),
                desc=task.get('description', '无描述'),
                countdown_text=countdown_text,
                deadline=task.get('deadline', '未知')
            )

        html += """
        </div>

        <div class="footer">
            <p>这是一封自动发送的邮件，请勿回复。</p>
            <p>任务提醒系统 &copy; 2026</p>
        </div>
    </div>
</body>
</html>
        """

        return html

    def _generate_email_text(self, tasks):
        """生成纯文本格式的邮件内容"""
        text = f"任务提醒 - 你有{len(tasks)}个未完成任务\n"
        text += "=" * 50 + "\n\n"

        for task in tasks:
            countdown = task.get('countdown', {})
            text += f"标题: {task.get('title', '无标题')}\n"
            text += f"描述: {task.get('description', '无描述')}\n"
            text += f"截止日期: {task.get('deadline', '未知')}\n"
            text += f"状态: {countdown.get('text', '未知')}\n"
            text += "-" * 50 + "\n"

        text += "\n" + "=" * 50 + "\n"
        text += "这是一封自动发送的邮件，请勿回复。\n"

        return text


# 测试代码
if __name__ == '__main__':
    from task_manager import TaskManager

    try:
        # 测试邮件发送
        print("测试邮件发送功能...")
        sender = EmailSender()
        tm = TaskManager()

        tasks = tm.get_tasks_with_countdown()
        pending_tasks = [t for t in tasks if not t['completed']]

        if pending_tasks:
            sender.send_reminder_email(pending_tasks)
        else:
            print("没有未完成的任务")

    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
