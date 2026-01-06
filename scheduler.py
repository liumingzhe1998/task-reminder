"""
定时任务调度模块
负责每天定时发送邮件提醒
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from task_manager import TaskManager
from email_sender import EmailSender


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaskReminderScheduler:
    def __init__(self, reminder_time='08:00'):
        """
        初始化调度器

        Args:
            reminder_time: 提醒时间，格式 'HH:MM'，默认 '08:00'
        """
        self.reminder_time = reminder_time
        self.scheduler = BlockingScheduler()
        self.task_manager = TaskManager()
        self.email_sender = EmailSender()

    def send_daily_reminder(self):
        """发送每日提醒邮件"""
        try:
            logger.info("=" * 50)
            logger.info("开始执行每日任务提醒...")

            # 获取所有未完成的任务
            tasks_with_countdown = self.task_manager.get_tasks_with_countdown()
            pending_tasks = [t for t in tasks_with_countdown if not t['completed']]

            if not pending_tasks:
                logger.info("没有未完成的任务，跳过邮件发送")
                return

            # 发送邮件
            success = self.email_sender.send_reminder_email(pending_tasks)

            if success:
                logger.info(f"✅ 成功发送 {len(pending_tasks)} 个任务的提醒邮件")
            else:
                logger.error("❌ 邮件发送失败")

        except Exception as e:
            logger.error(f"发送提醒邮件时出错: {str(e)}", exc_info=True)

    def start(self):
        """启动调度器"""
        try:
            # 解析时间
            hour, minute = map(int, self.reminder_time.split(':'))

            # 添加定时任务 - 每天指定时间执行
            self.scheduler.add_job(
                self.send_daily_reminder,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_reminder',
                name='每日任务提醒',
                replace_existing=True
            )

            logger.info(f"🚀 任务提醒调度器已启动")
            logger.info(f"📅 每天将在 {self.reminder_time} 发送任务提醒邮件")
            logger.info(f"📧 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("按 Ctrl+C 停止调度器")

            # 立即执行一次（可选）
            # self.send_daily_reminder()

            # 启动调度器（阻塞模式）
            self.scheduler.start()

        except Exception as e:
            logger.error(f"调度器启动失败: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器时出错: {str(e)}")


def main():
    """主函数"""
    import sys

    # 可以从命令行参数指定提醒时间
    reminder_time = '08:00'  # 默认早上8点
    if len(sys.argv) > 1:
        reminder_time = sys.argv[1]

    # 验证时间格式
    try:
        hour, minute = map(int, reminder_time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("时间格式不正确")
    except:
        print("❌ 时间格式错误，请使用 HH:MM 格式，例如 08:00")
        print("使用默认时间: 08:00")
        reminder_time = '08:00'

    # 创建并启动调度器
    scheduler = TaskReminderScheduler(reminder_time)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n收到停止信号，正在关闭调度器...")
        scheduler.stop()


if __name__ == '__main__':
    main()
