import json
import socket
import subprocess
import threading
import logging
import time

logger = logging.getLogger("MPVTest")

class SimpleMPVPlayer:
    def __init__(self, mpv_path="mpv"):
        self.path = mpv_path
        self.mpv_sock = '/tmp/mpv_test_socket'
        self.proc = None
        self.ipc_sock = None
        self.running = True
        self.command_id = 0
        self.connected = False
        
    def send_command(self, command):
        """发送命令到MPV"""
        data = {
            "command": command,
            "request_id": self.command_id
        }
        self.command_id += 1
        msg = json.dumps(data) + '\n'
        try:
            logger.info(f"发送命令到MPV: {msg}")
            self.ipc_sock.sendall(msg.encode())
            return True
        except Exception as e:
            logger.error(f'发送命令失败: {str(e)}')
            return False

    def start_ipc(self):
        """启动IPC通信"""
        while self.running:
            try:
                self.ipc_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                
                # 添加错误处理和重试机制
                retry_count = 0
                while retry_count < 3 and self.running:
                    try:
                        logger.info(f"尝试连接到MPV socket: {self.mpv_sock}")
                        self.ipc_sock.connect(self.mpv_sock)
                        self.connected = True
                        logger.info("IPC连接成功")
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"IPC连接尝试 {retry_count}/3 失败: {str(e)}")
                        time.sleep(1)
                
                if not self.connected:
                    logger.error("IPC连接失败")
                    return

                # 设置基本属性
                self.send_command(['set_property', 'volume', 100])
                
                # 接收MPV返回的消息
                while self.running:
                    try:
                        data = self.ipc_sock.recv(1024)
                        if data:
                            msg = data.decode()
                            logger.info(f"收到MPV消息: {msg}")
                            # 尝试解析JSON响应
                            try:
                                response = json.loads(msg)
                                if 'error' in response:
                                    logger.error(f"MPV返回错误: {response['error']}")
                            except json.JSONDecodeError:
                                pass
                    except Exception as e:
                        logger.error(f"接收消息错误: {str(e)}")
                        break
                        
            except Exception as e:
                logger.error(f"IPC连接错误: {str(e)}")
                time.sleep(1)
                
    def start(self):
        """启动MPV播放器"""
        # MPV基本参数
        params = [
            self.path,
            f'--input-ipc-server={self.mpv_sock}',
            '--idle=yes',
            '--msg-level=all=v',
            '--hwdec=auto',
        ]
        
        logger.info(f"启动MPV，参数: {params}")
        
        try:
            self.proc = subprocess.Popen(
                params,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 启动一个线程来读取MPV的输出
            def log_output(pipe, prefix):
                for line in pipe:
                    logger.info(f"{prefix}: {line.strip()}")
                    
            threading.Thread(target=log_output, args=(self.proc.stdout, "MPV stdout")).start()
            threading.Thread(target=log_output, args=(self.proc.stderr, "MPV stderr")).start()
            
        except Exception as e:
            logger.error(f"无法启动MPV: {str(e)}")
            return False
            
        # 启动IPC通信线程
        self.ipc_thread = threading.Thread(target=self.start_ipc)
        self.ipc_thread.start()
        return True

    def stop(self):
        """停止播放器"""
        self.running = False
        if self.proc:
            self.proc.terminate()
        if self.ipc_sock:
            self.ipc_sock.close()

    def play(self, url):
        """播放指定URL"""
        # 等待IPC连接成功
        retry_count = 0
        while not self.connected and retry_count < 5:
            time.sleep(1)
            retry_count += 1
            
        if not self.connected:
            logger.error("无法播放：IPC未连接")
            return False
            
        return self.send_command(['loadfile', url])

# 修改使用示例:
if __name__ == "__main__":
    # 设置更详细的日志格式
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    player = SimpleMPVPlayer()
    if not player.start():
        logger.error("MPV启动失败")
        exit(1)
    
    # 等待MPV启动和IPC连接
    time.sleep(3)
    
    # 播放测试视频
    test_url = "http://vjs.zencdn.net/v/oceans.mp4"
    logger.info(f"尝试播放: {test_url}")
    if not player.play(test_url):
        logger.error("播放命令发送失败")
    
    # 延长等待时间以观察播放效果
    time.sleep(30)
    player.stop()