"""
任务管理模块
负责任务的增删改查和倒计时计算
"""
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path


class TaskManager:
    def __init__(self, data_file='tasks.json'):
        self.data_file = Path(data_file)
        self._init_data_file()

    def _init_data_file(self):
        """初始化数据文件"""
        if not self.data_file.exists():
            self._save_data({'tasks': []})
        else:
            # 迁移旧数据：给没有user_id的任务添加user_id
            self._migrate_old_data()

    def _migrate_old_data(self):
        """迁移旧数据，给没有user_id的任务添加默认user_id"""
        data = self._load_data()
        tasks = data.get('tasks', [])
        updated = False

        for task in tasks:
            if 'user_id' not in task:
                task['user_id'] = 'liumingzhe'  # 默认分配给刘明哲
                updated = True

        if updated:
            self._save_data(data)

    def _load_data(self):
        """从文件加载数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {'tasks': []}

    def _save_data(self, data):
        """保存数据到文件"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_task(self, title, description, deadline, user_id='default'):
        """
        添加新任务

        Args:
            title: 任务标题
            description: 任务描述
            deadline: 截止日期 (格式: YYYY-MM-DD)
            user_id: 用户ID (默认为 'default')

        Returns:
            新创建的任务ID
        """
        data = self._load_data()

        # 验证日期格式
        try:
            datetime.strptime(deadline, '%Y-%m-%d')
        except ValueError:
            raise ValueError("日期格式必须为 YYYY-MM-DD")

        task = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'deadline': deadline,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'completed': False,
            'user_id': user_id  # 添加用户ID
        }

        data['tasks'].append(task)
        self._save_data(data)
        return task['id']

    def get_all_tasks(self, user_id=None):
        """
        获取所有任务（可选按用户过滤）

        Args:
            user_id: 用户ID，如果提供则只返回该用户的任务

        Returns:
            任务列表
        """
        data = self._load_data()
        tasks = data.get('tasks', [])

        # 如果指定了用户ID，只返回该用户的任务
        if user_id:
            # 同时匹配有user_id的任务和没有user_id的旧任务
            tasks = [t for t in tasks if t.get('user_id') == user_id or 'user_id' not in t]

        return tasks

    def get_task_by_id(self, task_id):
        """根据ID获取任务"""
        tasks = self.get_all_tasks()
        for task in tasks:
            if task['id'] == task_id:
                return task
        return None

    def delete_task(self, task_id):
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 删除成功返回True，失败返回False
        """
        data = self._load_data()
        original_length = len(data['tasks'])
        data['tasks'] = [t for t in data['tasks'] if t['id'] != task_id]

        if len(data['tasks']) < original_length:
            self._save_data(data)
            return True
        return False

    def toggle_task_completion(self, task_id):
        """
        切换任务完成状态

        Args:
            task_id: 任务ID

        Returns:
            bool: 操作成功返回True，失败返回False
        """
        data = self._load_data()
        for task in data['tasks']:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                self._save_data(data)
                return True
        return False

    def get_pending_tasks(self):
        """获取所有未完成的任务"""
        tasks = self.get_all_tasks()
        return [t for t in tasks if not t['completed']]

    def calculate_remaining_days(self, deadline):
        """
        计算剩余天数

        Args:
            deadline: 截止日期 (格式: YYYY-MM-DD)

        Returns:
            dict: {
                'days': 剩余天数（负数表示已超期）,
                'status': 'normal' | 'urgent' | 'overdue',
                'text': '剩余X天' | '已超期X天'
            }
        """
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            deadline_date = deadline_date.replace(hour=0, minute=0, second=0, microsecond=0)

            delta = deadline_date - today
            days = delta.days

            if days < 0:
                return {
                    'days': days,
                    'status': 'overdue',
                    'text': f'已超期{abs(days)}天'
                }
            elif days <= 3:
                return {
                    'days': days,
                    'status': 'urgent',
                    'text': f'剩余{days}天' if days > 0 else '今天到期'
                }
            else:
                return {
                    'days': days,
                    'status': 'normal',
                    'text': f'剩余{days}天'
                }
        except Exception:
            return {
                'days': 0,
                'status': 'normal',
                'text': '未知'
            }

    def get_tasks_with_countdown(self, user_id=None):
        """
        获取所有任务及其倒计时信息
        按紧急程度排序（即将到期的在前）

        Args:
            user_id: 用户ID，如果提供则只返回该用户的任务
        """
        tasks = self.get_all_tasks(user_id)
        tasks_with_countdown = []

        for task in tasks:
            countdown = self.calculate_remaining_days(task['deadline'])
            task_with_countdown = {**task, 'countdown': countdown}
            tasks_with_countdown.append(task_with_countdown)

        # 按剩余天数排序（剩余天数少的在前）
        tasks_with_countdown.sort(key=lambda x: x['countdown']['days'])

        return tasks_with_countdown


# 测试代码
if __name__ == '__main__':
    tm = TaskManager()
    print("任务管理器初始化成功")

    # 测试倒计时计算
    print("\n倒计时测试:")
    today = datetime.now()
    test_dates = [
        (today + timedelta(days=1)).strftime('%Y-%m-%d'),
        (today + timedelta(days=5)).strftime('%Y-%m-%d'),
        (today - timedelta(days=2)).strftime('%Y-%m-%d'),
    ]
    for date in test_dates:
        result = tm.calculate_remaining_days(date)
        print(f"{date}: {result}")
