import subprocess, sys
result = subprocess.run([sys.executable, "-c", "print(8 + 9)"], capture_output=True, text=True, check=True)
print(result.stdout.strip())
