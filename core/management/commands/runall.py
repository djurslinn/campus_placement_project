import sys
import subprocess
import time
import signal
import os
import socket
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Runs all microservices and the Django development server simultaneously'

    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def handle(self, *args, **options):
        import threading
        self.stdout.write(self.style.SUCCESS('Starting all services...'))

        processes = []
        root_dir = settings.BASE_DIR
        ats_service_dir = os.path.join(root_dir, 'ats-ai-service')

        # Check for port conflict
        if self.is_port_in_use(8001):
            self.stdout.write(self.style.WARNING('Port 8001 is already in use. Skipping ATS startup.'))
        else:
            # 1. Start ATS AI Microservice (FastAPI)
            try:
                self.stdout.write(self.style.WARNING('Starting ATS AI Service...'))
                ats_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001"],
                    cwd=ats_service_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                processes.append(ats_process)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to start ATS AI Service: {e}'))

        # 2. Start Django Development Server
        try:
            self.stdout.write(self.style.WARNING('Starting Django Server...'))
            django_process = subprocess.Popen(
                [sys.executable, "manage.py", "runserver", "127.0.0.1:8000"],
                cwd=root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes.append(django_process)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to start Django Server: {e}'))

        def log_reader(pipe, prefix, color_code):
            with pipe:
                for line in iter(pipe.readline, ''):
                    if line:
                        self.stdout.write(f'\033[{color_code}m{prefix}\033[0m {line.strip()}')

        # Start logging threads
        for p in processes:
            # Simple check based on command line
            is_ats = any("uvicorn" in arg for arg in p.args)
            prefix = "[ATS]" if is_ats else "[Django]"
            color = "94" if is_ats else "92"
            threading.Thread(target=log_reader, args=(p.stdout, prefix, color), daemon=True).start()

        def stop_all():
            self.stdout.write(self.style.NOTICE('\nStopping all services...'))
            for p in processes:
                try:
                    p.terminate()
                    if os.name == 'nt':
                        # Force kill if terminate didn't work immediately
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    pass
            sys.exit(0)

        def signal_handler(sig, frame):
            stop_all()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.stdout.write(self.style.SUCCESS('\nProject is active! (http://127.0.0.1:8000)'))
        self.stdout.write(self.style.NOTICE('Press Ctrl+C to stop.'))

        try:
            while True:
                for p in processes:
                    if p.poll() is not None:
                        is_ats = any("uvicorn" in arg for arg in p.args)
                        name = "ATS Service" if is_ats else "Django Server"
                        self.stderr.write(self.style.ERROR(f'\n[FATAL] {name} has stopped unexpectedly.'))
                        stop_all()
                time.sleep(1)
        except KeyboardInterrupt:
            stop_all()

