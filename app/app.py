from flask import Flask, render_template, request, jsonify
import subprocess
import os
import json
from datetime import datetime
import schedule
import threading
import time
from pathlib import Path
import sys

app = Flask(__name__)
# 启用调试模式
app.debug = True

# 确保日志立即输出
sys.stdout.reconfigure(line_buffering=True)

# 存储同步任务的文件
TASKS_FILE = '/app/data/sync_tasks.json'

def load_tasks():
    # 确保目录存在
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    # 确保目录存在
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def run_sync(source, destination, delete_option=True):
    # 确保目标目录存在
    os.makedirs(os.path.dirname(destination.rstrip('/')), exist_ok=True)
    
    # 修改rsync命令，使用斜杠结尾来避免创建额外的目录
    if not source.endswith('/'):
        source += '/'
        
    cmd = ['rsync', '-av']
    if delete_option:
        cmd.append('--delete')
    cmd.extend([source, destination])
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    return {
        'success': process.returncode == 0,
        'message': '同步成功' if process.returncode == 0 else '同步失败',
        'output': stdout if process.returncode == 0 else stderr
    }

def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(60)

# 启动定时任务线程
threading.Thread(target=run_scheduled_tasks, daemon=True).start()

def setup_schedule(task):
    """设置定时任务"""
    if not task.get('schedule'):
        return

    schedule_info = task['schedule']
    delete_option = task.get('delete_option', True)  # 默认为True

    if schedule_info['type'] == 'daily':
        schedule.every().day.at(schedule_info['time']).do(
            run_sync, task['source'], task['destination'], delete_option
        ).tag(f"task_{task['id']}")
    elif schedule_info['type'] == 'weekly':
        # 将前端的周日(0)到周六(6)转换为schedule库的周一(0)到周日(6)
        frontend_to_schedule = {
            "0": "sunday",    # 周日
            "1": "monday",    # 周一
            "2": "tuesday",   # 周二
            "3": "wednesday", # 周三
            "4": "thursday",  # 周四
            "5": "friday",    # 周五
            "6": "saturday"   # 周六
        }
        day = frontend_to_schedule[str(schedule_info['day'])]
        getattr(schedule.every(), day).at(schedule_info['time']).do(
            run_sync, task['source'], task['destination'], delete_option
        ).tag(f"task_{task['id']}")
    elif schedule_info['type'] == 'monthly':
        def monthly_job():
            if datetime.now().day == int(schedule_info['day']):
                run_sync(task['source'], task['destination'], delete_option)
        
        schedule.every().day.at(schedule_info['time']).do(monthly_job).tag(f"task_{task['id']}")
    elif schedule_info['type'] == 'interval':
        # 添加间隔定时功能
        interval = int(schedule_info['interval'])
        unit = schedule_info['unit']
        
        if unit == 'minutes':
            schedule.every(interval).minutes.do(
                run_sync, task['source'], task['destination'], delete_option
            ).tag(f"task_{task['id']}")
        elif unit == 'hours':
            schedule.every(interval).hours.do(
                run_sync, task['source'], task['destination'], delete_option
            ).tag(f"task_{task['id']}")

def get_actual_mount_points():
    """获取挂载点信息"""
    try:
        # Dynamically determine the mount points at runtime
        home_path = os.path.realpath('/home')
        data_path = os.path.realpath('/data')
        print(f"Determined mount points: /home -> {home_path}, /data -> {data_path}")
        return {'/home': home_path, '/data': data_path}
    except Exception as e:
        print(f"Error determining mount points: {str(e)}")
        return {'/home': '/home', '/data': '/data'}

@app.route('/')
def index():
    tasks = load_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/sync', methods=['POST'])
def sync():
    source = request.form.get('source')
    destination = request.form.get('destination')
    schedule_time = request.form.get('schedule_time', '')
    delete_option = request.form.get('delete_option') == 'true'
    
    if not source or not destination:
        return jsonify({'error': '请填写源路径和目标路径'}), 400
    
    result = run_sync(source, destination, delete_option)
    
    if result['success'] and schedule_time:
        tasks = load_tasks()
        task = {
            'id': len(tasks) + 1,
            'source': source,
            'destination': destination,
            'schedule_time': schedule_time,
            'delete_option': delete_option,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        tasks.append(task)
        save_tasks(tasks)
        
        schedule.every().day.at(schedule_time).do(
            run_sync, source=source, destination=destination, delete_option=delete_option
        )
    
    return jsonify(result)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    return jsonify(load_tasks())

@app.route('/tasks', methods=['POST'])
def add_task():
    source = request.form.get('source')
    destination = request.form.get('destination')
    schedule_json = request.form.get('schedule')
    delete_option = request.form.get('delete_option') == 'true'
    remark = request.form.get('remark', '')
    
    if not source or not destination:
        return jsonify({'success': False, 'error': '请填写源路径和目标路径'}), 400
    
    tasks = load_tasks()
    task = {
        'id': len(tasks) + 1,
        'source': source,
        'destination': destination,
        'delete_option': delete_option,
        'remark': remark,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if schedule_json:
        task['schedule'] = json.loads(schedule_json)
        setup_schedule(task)
    
    tasks.append(task)
    save_tasks(tasks)
    
    return jsonify({'success': True})

@app.route('/tasks/<int:task_id>/sync', methods=['POST'])
def execute_sync(task_id):
    tasks = load_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    result = run_sync(task['source'], task['destination'], task.get('delete_option', True))
    return jsonify(result)

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    tasks = load_tasks()
    tasks = [task for task in tasks if task['id'] != task_id]
    save_tasks(tasks)
    
    # 删除对应的定时任务
    schedule.clear(f"task_{task_id}")
    
    return jsonify({'success': True})

@app.route('/list_dir', methods=['GET'])
def list_dir():
    path = request.args.get('path', '/')
    print(f"\n=== list_dir called with path: {path} ===")
    
    try:
        mount_info = get_actual_mount_points()
        print(f"Mount info: {mount_info}")
        
        # 确定基础路径
        base_path = None
        for mount_point in ['/home', '/data']:
            if path.startswith(mount_point):
                base_path = mount_point
                break
        
        if not base_path:
            base_path = '/home'
            path = base_path
        
        print(f"Selected base_path: {base_path}")
        print(f"Final path: {path}")
        
        # 使用实际的挂载点路径
        if base_path in mount_info:
            real_path = path.replace(base_path, mount_info[base_path], 1)
        else:
            real_path = path
            
        full_path = os.path.abspath(real_path)
        print(f"Full path: {full_path}")
        
        # 获取目录内容
        items = []
        if os.path.exists(full_path):
            # 只在不是挂载点根路径时添加父目录选项
            if path not in mount_info.keys():
                parent_path = str(Path(path).parent)
                # 确保父目录不会超出挂载点
                if any(parent_path.startswith(mount) for mount in mount_info.keys()):
                    items.append({
                        'name': '..',
                        'path': parent_path,
                        'type': 'directory'
                    })
            
            # 列出目录内容
            try:
                for item in os.listdir(full_path):
                    try:
                        item_path = os.path.join(full_path, item)
                        if os.access(item_path, os.R_OK):
                            # 将实际路径转换回显路径
                            display_path = os.path.join(path, item)
                            items.append({
                                'name': item,
                                'path': display_path,
                                'type': 'directory' if os.path.isdir(item_path) else 'file'
                            })
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError) as e:
                return jsonify({'error': f'无法访问目录 {full_path}: {str(e)}'}), 403
        
        return jsonify({
            'current_path': path,  # 返回显示路径而不是实际路径
            'items': items
        })
    except Exception as e:
        print(f"Error in list_dir: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        data = request.get_json()
        tasks = load_tasks()
        
        # 找到要更新的任务
        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
            
        # 更新定时设置
        if 'schedule' in data:
            # 如果有旧的定时任务，先清除
            schedule.clear(f"task_{task_id}")
            
            # 更新任务的定时设置
            task['schedule'] = data['schedule']
            
            # 如果有新的定时设置，则设置新的定时任务
            if data['schedule']:
                setup_schedule(task)
        
        # 保存更新后的任务列表
        save_tasks(tasks)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 在用启动时清除所有现有的定时任务
@app.before_first_request
def init_app():
    schedule.clear()
    # 重新加载已保存的任务
    tasks = load_tasks()
    for task in tasks:
        if 'schedule' in task:
            setup_schedule(task)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8856) 