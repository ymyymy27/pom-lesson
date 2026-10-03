import subprocess, sys
result = subprocess.run([sys.executable, "-c", "print(6 * 7)"], capture_output=True, text=True, check=True)
print(result.stdout.strip())
