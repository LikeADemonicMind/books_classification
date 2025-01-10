import os
import subprocess
import signal


def run_tests():
    print("Running tests...")
    result = subprocess.run(["pytest", "--maxfail=5", "--disable-warnings"], check=False)
    if result.returncode != 0:
        print("Tests failed. Halting pipeline.")
        exit(result.returncode)
    print("All tests passed!")


def lint_code():
    print("Linting code...")
    result = subprocess.run(["flake8", "."], check=False)
    if result.returncode != 0:
        print("Linting errors found. Please fix them.")
        exit(result.returncode)
    print("Code is clean!")


def restart_application(pid_file, start_command, git_bash_path):
    print("Restarting application...")
    try:
        # Vérifier si le fichier PID existe
        if not os.path.exists(pid_file):
            print(f"{pid_file} not found. Starting application...")
            subprocess.Popen(
                [git_bash_path, "-c", f"nohup {start_command} &"],
                shell=True
            )
            print("Application started successfully!")
            return

        # Lire le PID depuis le fichier PID
        with open(pid_file, "r") as file:
            pid = int(file.read().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped application with PID: {pid}")

        # Relancer l'application
        subprocess.Popen(
            [git_bash_path, "-c", f"nohup {start_command} &"],
            shell=True
        )
        print("Application restarted successfully!")
    except FileNotFoundError:
        print(f"Error: {pid_file} not found.")
    except ProcessLookupError:
        print(f"Error: Process with PID {pid} not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    run_tests()
    lint_code()
    git_bash_path = r"C:\Program Files\Git\git-bash.exe"
    restart_application("app.pid", "uvicorn app:asgi_app --host 0.0.0.0 --port 8000", git_bash_path)
    restart_application("api.pid", "uvicorn api_lm_svc:app --host 0.0.0.0 --port 29000", git_bash_path)
