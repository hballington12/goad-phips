class SubprocessRunner:
    def run_command(self, command):
        import subprocess
        
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return e.stdout.decode('utf-8'), e.stderr.decode('utf-8')