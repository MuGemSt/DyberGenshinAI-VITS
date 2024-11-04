import time
import subprocess

# 运行 Python 脚本的路径
script_path = "game.py"

# 创建子进程并运行 Python 脚本
process = subprocess.Popen(
    ["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

# 等待几秒钟
time.sleep(60)

# 尝试优雅地终止子进程
process.terminate()

# 等待子进程结束，这里设置一个较短的超时时间
try:
    process.wait(timeout=1)
except subprocess.TimeoutExpired:
    # 如果子进程没有在超时时间内结束，强制终止子进程
    process.kill()
